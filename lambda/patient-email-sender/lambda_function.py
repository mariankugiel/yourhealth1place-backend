"""
Email Sender Lambda - Processes email queue and sends via SES

This function is triggered by SQS FIFO queue (yourhealth1place-email-queue.fifo).
It receives messages from the dispatcher Lambda, sends emails via AWS SES,
and logs delivery status to the database.
"""
import json
import boto3
import psycopg2
from datetime import datetime

# ============================================================================
# CONFIGURATION - Hardcoded variables
# ============================================================================
# Database Configuration (hardcoded)
DB_HOST = 'your-db-hostname'
DB_NAME = 'your-db-name'
DB_USER = 'your-db-user'
DB_PASSWORD = 'your-db-password'
DB_PORT = '5432'

# AWS Configuration (hardcoded)
AWS_REGION = 'us-east-1'
SES_FROM_EMAIL = 'notifications@yourhealth1place.com'

# Initialize AWS clients
ses_client = boto3.client('ses', region_name=AWS_REGION)


def lambda_handler(event, context):
    """
    Process email notifications from SQS FIFO queue
    Send emails via AWS SES
    """
    print(f"📧 Processing {len(event['Records'])} email messages")
    
    processed = 0
    failed = 0
    
    # Connect to database for logging
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
        )
        cursor = conn.cursor()
    except Exception as db_error:
        error_msg = f"Database connection failed: {db_error}"
        print(f"❌ {error_msg}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
    
    for record in event['Records']:
        try:
            # Parse message from SQS
            message = json.loads(record['body'])
            
            notification_id = message.get('notification_id')
            user_id = message.get('user_id')
            email_address = message.get('email_address')
            title = message.get('title')
            content = message.get('message')
            priority = message.get('priority', 'normal')
            metadata = message.get('metadata', {})
            
            if not email_address:
                raise ValueError("Email address is required")
            
            print(f"📧 Sending email to {email_address} for notification {notification_id}")
            
            # Build email content
            subject = f"[YourHealth1Place] {title}"
            html_body = _build_html_email(title, content, metadata)
            text_body = _build_text_email(title, content)
            
            # Send email via SES
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
            print(f"✅ Email sent successfully. SES MessageId: {ses_message_id}")
            
            # Log delivery to database
            now = datetime.utcnow()
            try:
                # Update notification status
                cursor.execute(
                    """
                    UPDATE notifications 
                    SET status = 'sent', sent_at = %s
                    WHERE id = %s
                    """,
                    (now, notification_id)
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
                    )
                )
                conn.commit()
            except Exception as log_error:
                print(f"⚠️ Failed to log delivery to database: {log_error}")
                conn.rollback()
            
            processed += 1
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Failed to send email: {error_msg}")
            
            # Log failure to database
            try:
                now = datetime.utcnow()
                cursor.execute(
                    """
                    UPDATE notifications 
                    SET status = 'failed'
                    WHERE id = %s
                    """,
                    (message.get('notification_id'),)
                )
                cursor.execute(
                    """
                    INSERT INTO notification_delivery_logs 
                    (notification_id, user_id, channel, status, target_address, provider_response, sent_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        message.get('notification_id'),
                        message.get('user_id'),
                        'email',
                        'failed',
                        message.get('email_address'),
                        json.dumps({'error': error_msg}),
                        now,
                    )
                )
                conn.commit()
            except Exception as log_error:
                print(f"⚠️ Failed to log failure to database: {log_error}")
                conn.rollback()
            
            failed += 1
            # Don't raise - continue processing other messages
    
    # Close database connection
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"📊 Email processing complete: {processed} sent, {failed} failed")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': processed,
            'failed': failed,
            'timestamp': datetime.utcnow().isoformat()
        })
    }


def _build_html_email(title: str, content: str, metadata: dict = None) -> str:
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




