"""
SMS Sender Lambda - Processes SMS queue and sends via SNS

This function is triggered by SQS FIFO queue (yourhealth1place-sms-queue.fifo).
It receives messages from the dispatcher Lambda, sends SMS via AWS SNS,
and logs delivery status to the database.
"""
import json
import boto3
import psycopg2
from datetime import datetime
import re

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

# Initialize AWS clients
sns_client = boto3.client('sns', region_name=AWS_REGION)

def lambda_handler(event, context):
    """
    Process SMS notifications from SQS FIFO queue
    Send SMS via AWS SNS (E.164 format required)
    """
    
    print(f"📱 Processing {len(event['Records'])} SMS messages")
    
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
    
    processed = 0
    failed = 0
    
    for record in event['Records']:
        try:
            # Parse message
            message = json.loads(record['body'])
            
            notification_id = message.get('notification_id')
            user_id = message.get('user_id')
            phone_number = message.get('phone_number')
            title = message.get('title')
            content = message.get('message')
            priority = message.get('priority', 'normal')
            
            # Validate E.164 format
            if not is_valid_e164(phone_number):
                raise ValueError(f"Invalid phone number format: {phone_number}. Must be E.164 format (e.g., +12345678900)")
            
            print(f"📲 Sending SMS to {phone_number} for notification {notification_id}")
            
            # Prepare SMS message (max 160 characters recommended)
            sms_text = f"YourHealth1Place: {title}\n{content}"
            
            # Truncate if too long
            if len(sms_text) > 160:
                sms_text = sms_text[:157] + "..."
            
            # Send SMS via SNS
            response = sns_client.publish(
                PhoneNumber=phone_number,
                Message=sms_text,
                MessageAttributes={
                    'AWS.SNS.SMS.SenderID': {
                        'DataType': 'String',
                        'StringValue': 'YH1Place'  # Up to 11 characters
                    },
                    'AWS.SNS.SMS.SMSType': {
                        'DataType': 'String',
                        'StringValue': 'Transactional' if priority in ['high', 'urgent'] else 'Promotional'
                    }
                }
            )
            
            message_id = response['MessageId']
            print(f"✅ SMS sent successfully. SNS MessageId: {message_id}")
            
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
                        'sms',
                        'sent',
                        phone_number,
                        message_id,
                        json.dumps(response),
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
            print(f"❌ Failed to send SMS: {error_msg}")
            
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
                        'sms',
                        'failed',
                        message.get('phone_number'),
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
    
    print(f"📊 SMS processing complete: {processed} sent, {failed} failed")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': processed,
            'failed': failed,
            'timestamp': datetime.utcnow().isoformat()
        })
    }

def is_valid_e164(phone_number):
    """
    Validate E.164 phone number format
    Format: +[country code][subscriber number]
    Example: +12025551234
    """
    pattern = r'^\+[1-9]\d{1,14}$'
    return re.match(pattern, phone_number) is not None

