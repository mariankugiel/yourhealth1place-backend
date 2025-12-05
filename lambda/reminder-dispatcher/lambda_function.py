"""
Lambda Dispatcher - Triggered by EventBridge every 5 minutes
Checks database directly for due medication reminders and processes them
Fetches user preferences from Supabase and applies reminder offsets
"""
import json
import boto3
import psycopg2
from datetime import datetime, timedelta
import pytz
from supabase import create_client, Client

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
SQS_EMAIL_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/123456789012/email-queue'
SQS_SMS_QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/123456789012/sms-queue'
SES_FROM_EMAIL = 'notifications@yourhealth1place.com'

# Supabase Configuration (hardcoded)
SUPABASE_URL = 'https://your-supabase-url.supabase.co'
SUPABASE_SERVICE_ROLE_KEY = 'your-supabase-service-role-key'

# Initialize AWS clients
sqs_client = boto3.client('sqs', region_name=AWS_REGION)

# Initialize Supabase client (lazy initialization)
supabase_client: Client = None

def get_supabase_client() -> Client:
    """Get or create Supabase client"""
    global supabase_client
    if supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    return supabase_client

# Check window for due reminders (minutes)
CHECK_WINDOW_MINUTES = 5

# Default user preferences (used when no preferences found)
DEFAULT_PREFERENCES = {
    'email_medications': True,
    'sms_medications': True,
    'whatsapp_medications': False,
    'medication_minutes_before': '0'  # 0 minutes offset by default
}


def lambda_handler(event, context):
    """
    EventBridge trigger function
    Checks database directly for due reminders and sends notifications
    """
    
    print(f"🔔 Reminder check triggered at {datetime.utcnow().isoformat()}")
    
    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        error_msg = "Database configuration missing"
        print(f"❌ {error_msg}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT,
        )
        cursor = conn.cursor()
        
        # Calculate check window (extended to account for reminder offsets)
        # Users can set reminders to go off 15 minutes before, so we need to check further ahead
        now = datetime.utcnow()
        max_offset_minutes = 60  # Maximum offset users can set (e.g., 60 minutes before)
        check_window = now + timedelta(minutes=CHECK_WINDOW_MINUTES + max_offset_minutes)
        
        print(f"Checking reminders due between {now.isoformat()} and {check_window.isoformat()}")
        
        # Query due reminders
        # Note: Phone numbers are stored in Supabase user_profiles, not in main users table
        # For SMS, we'll need to fetch from Supabase or store phone_number in users table
        query = """
            SELECT 
                mr.id as reminder_id,
                mr.medication_id,
                mr.user_id,
                mr.reminder_time,
                mr.user_timezone,
                mr.days_of_week,
                mr.next_scheduled_at,
                m.medication_name,
                m.dosage,
                m.frequency,
                u.email,
                u.supabase_user_id
            FROM medication_reminders mr
            JOIN medications m ON mr.medication_id = m.id
            JOIN users u ON mr.user_id = u.id
            WHERE mr.enabled = true
              AND mr.status = 'active'
              AND mr.next_scheduled_at <= %s
              AND mr.next_scheduled_at >= %s
        """
        
        cursor.execute(query, (check_window, now))
        reminders = cursor.fetchall()
        
        print(f"📋 Found {len(reminders)} due reminders")
        
        processed_count = 0
        failed_count = 0
        
        for row in reminders:
            try:
                (
                    reminder_id,
                    medication_id,
                    user_id,
                    reminder_time,
                    user_timezone,
                    days_of_week,
                    next_scheduled_at,
                    medication_name,
                    dosage,
                    frequency,
                    email_address,
                    supabase_user_id
                ) = row
                
                print(f"Processing reminder {reminder_id} for user {user_id}")
                
                # Fetch user preferences and phone number from Supabase FIRST
                # We need to check the offset before creating the notification
                user_preferences = DEFAULT_PREFERENCES.copy()
                phone_number = None
                phone_country_code = None
                
                if supabase_user_id:
                    try:
                        client = get_supabase_client()
                        
                        # Fetch user notification preferences
                        try:
                            prefs_response = client.table("user_notifications").select("*").eq("user_id", supabase_user_id).execute()
                            if prefs_response.data and len(prefs_response.data) > 0:
                                prefs = prefs_response.data[0]
                                user_preferences['email_medications'] = prefs.get('email_medications', DEFAULT_PREFERENCES['email_medications'])
                                user_preferences['sms_medications'] = prefs.get('sms_medications', DEFAULT_PREFERENCES['sms_medications'])
                                user_preferences['whatsapp_medications'] = prefs.get('whatsapp_medications', DEFAULT_PREFERENCES['whatsapp_medications'])
                                user_preferences['medication_minutes_before'] = prefs.get('medication_minutes_before', DEFAULT_PREFERENCES['medication_minutes_before'])
                                print(f"📋 Loaded preferences for user {user_id}: email={user_preferences['email_medications']}, sms={user_preferences['sms_medications']}, offset={user_preferences['medication_minutes_before']}min")
                        except Exception as prefs_error:
                            print(f"⚠️ Could not fetch preferences for user {user_id}, using defaults: {prefs_error}")
                        
                        # Fetch phone number from user_profiles
                        # Note: Field name is 'phone' not 'phone_number' in Supabase schema
                        try:
                            profile_response = client.table("user_profiles").select("phone, phone_country_code").eq("id", supabase_user_id).execute()
                            if profile_response.data and len(profile_response.data) > 0:
                                profile = profile_response.data[0]
                                phone_number = profile.get('phone')
                                phone_country_code = profile.get('phone_country_code')
                        except Exception as phone_error:
                            print(f"⚠️ Could not fetch phone number for user {user_id}: {phone_error}")
                    except Exception as supabase_error:
                        print(f"⚠️ Supabase error for user {user_id}: {supabase_error}")
                
                # Apply reminder offset - check if reminder should be sent now
                reminder_offset_minutes = int(user_preferences.get('medication_minutes_before', '0'))
                send_time = next_scheduled_at - timedelta(minutes=reminder_offset_minutes)
                
                # Only process if the reminder (with offset) is due now or in the past
                # We check if send_time <= now (meaning it's time to send)
                if send_time > now:
                    print(f"⏰ Reminder {reminder_id} not due yet (with {reminder_offset_minutes}min offset). Actual reminder time: {next_scheduled_at}, Should send at: {send_time}, Current time: {now}")
                    continue
                
                print(f"⏰ Processing reminder {reminder_id} (reminder time: {next_scheduled_at}, sending {reminder_offset_minutes}min early, send time: {send_time})")
                
                # Create notification record AFTER confirming it should be sent
                notification_title = f"💊 Time to take {medication_name}"
                notification_message = f"It's time to take your {medication_name}"
                
                insert_notification = """
                    INSERT INTO notifications 
                    (user_id, notification_type, title, message, medication_id, scheduled_at, status, data, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """
                
                notification_data = json.dumps({
                    "medication_name": medication_name,
                    "medication_id": medication_id,
                    "dosage": dosage,
                    "frequency": frequency,
                    "reminder_id": reminder_id,
                    "reminder_time": str(reminder_time),
                    "user_timezone": user_timezone
                })
                
                cursor.execute(
                    insert_notification,
                    (
                        user_id,
                        'medication_reminder',
                        notification_title,
                        notification_message,
                        medication_id,
                        next_scheduled_at,
                        'pending',
                        notification_data,
                        now
                    )
                )
                notification_id = cursor.fetchone()[0]
                
                print(f"✅ Created notification {notification_id} for user {user_id}")
                
                # Format phone number to E.164 if we have both country code and number
                formatted_phone = None
                if phone_number and phone_country_code:
                    # Remove any non-digit characters and format as E.164
                    country_code = phone_country_code.replace('+', '').strip()
                    phone_digits = ''.join(filter(str.isdigit, phone_number))
                    if country_code and phone_digits:
                        formatted_phone = f"+{country_code}{phone_digits}"
                
                # Track if we sent to any queue
                sent_to_queue = False
                
                # Send to email queue (only if enabled in preferences)
                if SQS_EMAIL_QUEUE_URL and email_address and user_preferences.get('email_medications', True):
                    try:
                        message_body = {
                            'notification_id': notification_id,
                            'user_id': user_id,
                            'email_address': email_address,
                            'title': notification_title,
                            'message': notification_message,
                            'priority': 'normal',
                            'notification_type': 'medication_reminder',
                            'metadata': json.loads(notification_data)
                        }
                        
                        sqs_client.send_message(
                            QueueUrl=SQS_EMAIL_QUEUE_URL,
                            MessageBody=json.dumps(message_body),
                            MessageGroupId=f"user-{user_id}",
                            MessageDeduplicationId=f"notification-{notification_id}-{now.isoformat()}"
                        )
                        
                        print(f"📧 Queued email for user {user_id} ({email_address})")
                        sent_to_queue = True
                    except Exception as email_error:
                        print(f"❌ Failed to queue email: {email_error}")
                else:
                    print(f"⚠️ No email queue URL or email address for user {user_id}")
                
                # Send to SMS queue (only if enabled in preferences)
                if SQS_SMS_QUEUE_URL and formatted_phone and user_preferences.get('sms_medications', True):
                    try:
                        sms_message_body = {
                            'notification_id': notification_id,
                            'user_id': user_id,
                            'phone_number': formatted_phone,
                            'title': notification_title,
                            'message': notification_message,
                            'priority': 'normal',
                            'notification_type': 'medication_reminder',
                            'metadata': json.loads(notification_data)
                        }
                        
                        sqs_client.send_message(
                            QueueUrl=SQS_SMS_QUEUE_URL,
                            MessageBody=json.dumps(sms_message_body),
                            MessageGroupId=f"user-{user_id}",
                            MessageDeduplicationId=f"sms-notification-{notification_id}-{now.isoformat()}"
                        )
                        
                        print(f"📱 Queued SMS for user {user_id} ({formatted_phone})")
                        sent_to_queue = True
                    except Exception as sms_error:
                        print(f"❌ Failed to queue SMS: {sms_error}")
                elif SQS_SMS_QUEUE_URL and not formatted_phone and user_preferences.get('sms_medications', True):
                    print(f"⚠️ SMS enabled but no phone number for user {user_id}")
                elif SQS_SMS_QUEUE_URL and not user_preferences.get('sms_medications', True):
                    print(f"ℹ️ SMS disabled in preferences for user {user_id}")
                
                # Update notification status based on whether we sent to any queue
                # Note: Status remains 'pending' until sender lambdas actually send and update it
                if not sent_to_queue:
                    print(f"❌ No queues available or no contact info for user {user_id}")
                    cursor.execute(
                        "UPDATE notifications SET status = 'failed', failed_at = %s WHERE id = %s",
                        (now, notification_id)
                    )
                    failed_count += 1
                    continue
                
                # Calculate next scheduled time (without offset - offset is only for when to send, not when reminder occurs)
                next_scheduled = calculate_next_scheduled_time(
                    reminder_time,
                    json.loads(days_of_week) if isinstance(days_of_week, str) else days_of_week,
                    user_timezone or 'UTC',
                    now  # Pass current time for consistency
                )
                
                # Only update reminder if we have a valid next scheduled time
                if next_scheduled is None:
                    print(f"⚠️ Could not calculate next scheduled time for reminder {reminder_id}. Reminder may need manual review.")
                    # Don't update next_scheduled_at, but still mark as sent
                    cursor.execute(
                        """
                        UPDATE medication_reminders
                        SET last_sent_at = %s
                        WHERE id = %s
                        """,
                        (now, reminder_id)
                    )
                else:
                    # Update reminder with next scheduled time
                    cursor.execute(
                        """
                        UPDATE medication_reminders
                        SET last_sent_at = %s, next_scheduled_at = %s
                        WHERE id = %s
                        """,
                        (now, next_scheduled, reminder_id)
                    )
                
                processed_count += 1
                print(f"✅ Processed reminder {reminder_id} for user {user_id}")
                
            except Exception as reminder_error:
                print(f"❌ Error processing reminder {row[0]}: {reminder_error}")
                import traceback
                print(traceback.format_exc())
                # Note: We don't rollback here to avoid losing other successfully processed reminders
                # Individual reminder errors are logged and counted, but processing continues
                failed_count += 1
                continue
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"📊 Reminder check completed: {processed_count} processed, {failed_count} failed")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Reminder check completed',
                'processed_count': processed_count,
                'failed_count': failed_count,
                'total_due': len(reminders),
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg,
                'timestamp': datetime.utcnow().isoformat()
            })
        }


def calculate_next_scheduled_time(reminder_time, days_of_week, user_timezone, current_time_utc=None):
    """
    Calculate the next UTC datetime when the reminder should be sent
    
    Args:
        reminder_time: Time object (TIME or TIMETZ) for when reminder should occur
        days_of_week: List of day names (e.g., ['monday', 'tuesday'])
        user_timezone: Timezone string (e.g., 'America/New_York')
        current_time_utc: Optional UTC datetime to use as reference (defaults to now)
    """
    try:
        user_tz = pytz.timezone(user_timezone)
        utc_tz = pytz.UTC
        
        # Use provided current time or get current UTC time
        if current_time_utc is None:
            current_time_utc = datetime.utcnow()
        
        # Convert current UTC time to user's timezone for comparison
        if current_time_utc.tzinfo is None:
            current_time_utc = utc_tz.localize(current_time_utc)
        
        now_user_tz = current_time_utc.astimezone(user_tz)
        
        # Extract time from reminder_time (TIMETZ)
        # reminder_time is a time object with timezone info
        if hasattr(reminder_time, 'tzinfo') and reminder_time.tzinfo:
            # It's already a time with timezone
            reminder_time_only = reminder_time.replace(tzinfo=None)
        else:
            # It's a time object, extract just the time part
            reminder_time_only = reminder_time
        
        # Check next 7 days for a valid reminder time
        for i in range(7):
            check_date = now_user_tz + timedelta(days=i)
            day_name = check_date.strftime('%A').lower()
            
            if day_name in days_of_week:
                # Create the reminder datetime for this day in user's timezone
                reminder_datetime = user_tz.localize(
                    datetime.combine(check_date.date(), reminder_time_only)
                )
                
                # Only use this if it's in the future
                if reminder_datetime > now_user_tz:
                    # Convert to UTC
                    return reminder_datetime.astimezone(utc_tz).replace(tzinfo=None)
        
        return None
        
    except Exception as e:
        print(f"Error calculating next scheduled time: {e}")
        import traceback
        print(traceback.format_exc())
        return None
