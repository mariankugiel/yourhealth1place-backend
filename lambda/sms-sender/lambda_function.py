"""
SMS Sender Lambda - Processes SMS queue and sends via SNS
"""
import json
import boto3
from datetime import datetime
import os
import re

# Initialize AWS clients
sns_client = boto3.client('sns', region_name=os.environ['AWS_REGION'])

def lambda_handler(event, context):
    """
    Process SMS notifications from SQS FIFO queue
    Send SMS via AWS SNS (E.164 format required)
    """
    
    print(f"📱 Processing {len(event['Records'])} SMS messages")
    
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
            
            # Log delivery to backend
            log_delivery(notification_id, user_id, 'sms', 'sent', phone_number, message_id, response)
            
            processed += 1
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Failed to send SMS: {error_msg}")
            
            # Log failure
            try:
                log_delivery(
                    message.get('notification_id'),
                    message.get('user_id'),
                    'sms',
                    'failed',
                    message.get('phone_number'),
                    None,
                    {'error': error_msg}
                )
            except:
                pass
            
            failed += 1
            
            # Don't raise - continue processing other messages
    
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

def log_delivery(notification_id, user_id, channel, status, target, provider_message_id, provider_response):
    """Log delivery to backend API"""
    try:
        backend_url = os.environ['BACKEND_URL']
        log_endpoint = f"{backend_url}/api/v1/notifications/delivery-log"
        
        import requests
        requests.post(
            log_endpoint,
            json={
                'notification_id': notification_id,
                'user_id': user_id,
                'channel': channel,
                'status': status,
                'target_address': target,
                'provider_message_id': provider_message_id,
                'provider_response': json.dumps(provider_response),
                'timestamp': datetime.utcnow().isoformat()
            },
            headers={'Authorization': f"Bearer {os.environ['LAMBDA_API_TOKEN']}"},
            timeout=5
        )
    except Exception as e:
        print(f"⚠️ Failed to log delivery: {e}")

