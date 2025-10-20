"""
Email Sender Lambda - Direct DB polling and email sending via SES (no backend HTTP calls)

This function is intended to run on a fixed schedule (e.g., every minute) via EventBridge.
It selects due medication reminders directly from the database, creates notification rows,
sends emails via SES, logs delivery into `notification_delivery_logs`, and advances
each reminder's `next_scheduled_at`.
"""
import json
import boto3
import psycopg2
from datetime import datetime, timedelta
import pytz

# ============================================================================
# CONFIGURATION - Define environment as module-level variables
# ============================================================================
AWS_REGION = 'us-east-1'  # AWS region for SES
SES_FROM_EMAIL = 'notifications@yourhealth1place.com'  # Verified SES identity

# Database connection (RDS, Aurora, or external Postgres reachable from Lambda)
DB_HOST = 'your-db-hostname'
DB_NAME = 'your-db-name'
DB_USER = 'your-db-user'
DB_PASSWORD = 'your-db-password'
DB_PORT = '5432'

# Reminder selection window (how far ahead to look for due reminders in UTC)
CHECK_WINDOW_MINUTES = 2

# Initialize AWS clients
ses_client = boto3.client('ses', region_name=AWS_REGION)


def lambda_handler(event, context):
    """
    Scheduled entrypoint: query due reminders, send emails, log results, update schedules.
    """
    start_ts = datetime.utcnow()
    print(f"\u23f0 Email reminder run started at {start_ts.isoformat()}Z")

    processed = 0
    failed = 0
    results = []

    # Calculate query window
    now = datetime.utcnow()
    check_window = now + timedelta(minutes=CHECK_WINDOW_MINUTES)
    print(f"Selecting reminders due between {now.isoformat()}Z and {check_window.isoformat()}Z")

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
        )
        cursor = conn.cursor()

        # Find due reminders
        select_due = """
            SELECT 
                mr.id as reminder_id,
                mr.medication_id,
                mr.user_id,
                mr.reminder_time,
                mr.user_timezone,
                mr.days_of_week,
                m.medication_name,
                m.dosage,
                m.frequency,
                u.email,
                u.timezone as user_timezone_pref
            FROM medication_reminders mr
            JOIN medications m ON mr.medication_id = m.id
            JOIN users u ON mr.user_id = u.id
            WHERE mr.enabled = true
              AND mr.status = 'active'
              AND mr.next_scheduled_at <= %s
              AND mr.next_scheduled_at > %s
        """
        cursor.execute(select_due, (check_window, now))
        reminders = cursor.fetchall()
        print(f"Found {len(reminders)} reminder(s) due for email.")

        for row in reminders:
            try:
                (
                    reminder_id,
                    medication_id,
                    user_id,
                    reminder_time,
                    user_timezone,
                    days_of_week,
                    medication_name,
                    dosage,
                    frequency,
                    email_address,
                    user_timezone_pref,
                ) = row

                # Compose notification content
                title = f"Time to take {medication_name}"
                content = f"Remember to take your {medication_name} ({dosage})."

                # Create notification record (keep columns aligned with existing lambda pattern)
                insert_notification = """
                    INSERT INTO notifications 
                    (user_id, notification_type, title, message, medication_id, data, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                data_payload = json.dumps({
                    "medication_id": medication_id,
                    "medication_name": medication_name,
                    "dosage": dosage,
                    "frequency": frequency,
                    "reminder_time": str(reminder_time),
                    "reminder_id": reminder_id,
                })
                cursor.execute(
                    insert_notification,
                    (
                        user_id,
                        'medication_reminder',
                        title,
                        content,
                        medication_id,
                        data_payload,
                        now,
                    ),
                )
                notification_id = cursor.fetchone()[0]
                print(f"Created notification {notification_id} for user {user_id}")

                # Send Email
                subject = f"[YourHealth1Place] {title}"
                html_body = _build_html_email(title, content)
                text_body = _build_text_email(title, content)

                ses_response = ses_client.send_email(
                    Source=SES_FROM_EMAIL,
                    Destination={'ToAddresses': [email_address]},
                    Message={
                        'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                        'Body': {
                            'Text': {'Data': text_body, 'Charset': 'UTF-8'},
                            'Html': {'Data': html_body, 'Charset': 'UTF-8'},
                        },
                    },
                )
                ses_message_id = ses_response.get('MessageId')
                print(f"\u2705 Email sent to {email_address} (SES MessageId: {ses_message_id})")

                # Mark notification as sent (status + timestamp)
                cursor.execute(
                    """
                    UPDATE notifications 
                    SET status = 'sent', sent_at = %s
                    WHERE id = %s
                    """,
                    (now, notification_id),
                )

                # Insert delivery log
                cursor.execute(
                    """
                    INSERT INTO notification_delivery_logs 
                    (notification_id, user_id, channel, status, target_address, provider_message_id, provider_response, sent_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        notification_id,
                        user_id,
                        'email',
                        'sent',
                        email_address,
                        ses_message_id,
                        json.dumps(ses_response),
                        now,
                    ),
                )

                # Advance reminder schedule
                next_scheduled = calculate_next_scheduled_time(
                    reminder_time,
                    json.loads(days_of_week) if isinstance(days_of_week, str) else days_of_week,
                    user_timezone or user_timezone_pref or 'UTC',
                )
                cursor.execute(
                    """
                    UPDATE medication_reminders
                    SET last_sent_at = %s, next_scheduled_at = %s
                    WHERE id = %s
                    """,
                    (now, next_scheduled, reminder_id),
                )

                processed += 1
                results.append({
                    "reminder_id": reminder_id,
                    "notification_id": notification_id,
                    "user_id": user_id,
                    "email": email_address,
                    "next_scheduled_at": next_scheduled.isoformat() if next_scheduled else None,
                })

            except Exception as send_err:
                print(f"\u274c Failed processing reminder {row[0]}: {send_err}")
                failed += 1
                # best-effort: do not raise to allow other reminders to process

        conn.commit()
        cursor.close()
        conn.close()

        print(f"\ud83d\udcca Email sender completed: {processed} sent, {failed} failed")
        return {
            'statusCode': 200,
            'body': json.dumps({
                'processed': processed,
                'failed': failed,
                'results': results,
                'timestamp': datetime.utcnow().isoformat(),
            }),
        }

    except Exception as e:
        print(f"Error in email sender: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
            }),
        }


def _build_html_email(title: str, content: str) -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset=\"UTF-8\">
  <style>
    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
    .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
    .content {{ padding: 20px; background-color: #f9f9f9; }}
    .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
  </style>
  <title>YourHealth1Place</title>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <meta http-equiv=\"x-ua-compatible\" content=\"ie=edge\" />
  <meta name=\"x-apple-disable-message-reformatting\" />
  <meta name=\"format-detection\" content=\"telephone=no, date=no, address=no, email=no\" />
  <meta name=\"color-scheme\" content=\"light\" />
  <meta name=\"supported-color-schemes\" content=\"light\" />
  <style>@media (prefers-color-scheme: dark) {{ body {{ background: #111; color: #eee; }} }}</style>
  <style>img {{ max-width: 100%; height: auto; }}</style>
</head>
<body>
  <div class=\"container\">
    <div class=\"header\">
      <h2>YourHealth1Place</h2>
    </div>
    <div class=\"content\">
      <h3>{title}</h3>
      <p>{content}</p>
    </div>
    <div class=\"footer\">
      <p>This is an automated message from YourHealth1Place.</p>
      <p>To manage your notification preferences, visit your account settings.</p>
    </div>
  </div>
</body>
</html>
"""


def _build_text_email(title: str, content: str) -> str:
    return (
        f"{title}\n\n{content}\n\n---\nYourHealth1Place\n"
        "To manage your notification preferences, visit your account settings."
    )


def calculate_next_scheduled_time(reminder_time, days_of_week, user_timezone):
    """Calculate the next UTC datetime when the reminder should be sent."""
    try:
        user_tz = pytz.timezone(user_timezone)
        utc_tz = pytz.UTC

        now_user_tz = datetime.now(user_tz)
        for i in range(7):
            check_date = now_user_tz + timedelta(days=i)
            day_name = check_date.strftime('%A').lower()
            if day_name in days_of_week:
                # Construct the next reminder datetime in user's TZ
                # Combine date with the stored time (naive), then localize
                reminder_dt = user_tz.localize(
                    datetime.combine(check_date.date(), reminder_time)
                )
                if reminder_dt > now_user_tz:
                    return reminder_dt.astimezone(utc_tz).replace(tzinfo=None)
        return None
    except Exception as e:
        print(f"Error calculating next scheduled time: {e}")
        return None


