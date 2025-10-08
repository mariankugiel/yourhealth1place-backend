"""
Email Sender Lambda - Processes email queue and sends via SES
"""
import json
import boto3
from datetime import datetime
import os

# Initialize AWS clients
ses_client = boto3.client('ses', region_name=os.environ['AWS_REGION'])
sqs_client = boto3.client('sqs', region_name=os.environ['AWS_REGION'])

def lambda_handler(event, context):
    """
    Process email notifications from SQS FIFO queue
    Send emails via AWS SES
    """
    
    print(f"📧 Processing {len(event['Records'])} email messages")
    
    processed = 0
    failed = 0
    
    for record in event['Records']:
        try:
            # Parse message
            message = json.loads(record['body'])
            
            notification_id = message.get('notification_id')
            user_id = message.get('user_id')
            email_address = message.get('email_address')
            title = message.get('title')
            content = message.get('message')
            priority = message.get('priority', 'normal')
            
            print(f"📨 Sending email to {email_address} for notification {notification_id}")
            
            # Prepare email
            subject = f"[YourHealth1Place] {title}"
            
            # HTML body
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f9f9f9; }}
                    .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                    .priority-{priority} {{ border-left: 4px solid {"#ff0000" if priority == "urgent" else "#ff9800" if priority == "high" else "#4CAF50"}; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h2>YourHealth1Place</h2>
                    </div>
                    <div class="content priority-{priority}">
                        <h3>{title}</h3>
                        <p>{content}</p>
                    </div>
                    <div class="footer">
                        <p>This is an automated message from YourHealth1Place.</p>
                        <p>To manage your notification preferences, visit your account settings.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Text body (fallback)
            text_body = f"{title}\n\n{content}\n\n---\nYourHealth1Place\nTo manage your notification preferences, visit your account settings."
            
            # Send email via SES
            response = ses_client.send_email(
                Source=os.environ['SES_FROM_EMAIL'],
                Destination={
                    'ToAddresses': [email_address]
                },
                Message={
                    'Subject': {
                        'Data': subject,
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': text_body,
                            'Charset': 'UTF-8'
                        },
                        'Html': {
                            'Data': html_body,
                            'Charset': 'UTF-8'
                        }
                    }
                }
            )
            
            message_id = response['MessageId']
            print(f"✅ Email sent successfully. SES MessageId: {message_id}")
            
            # Log delivery to backend
            log_delivery(notification_id, user_id, 'email', 'sent', email_address, message_id, response)
            
            processed += 1
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Failed to send email: {error_msg}")
            
            # Log failure
            try:
                log_delivery(
                    message.get('notification_id'),
                    message.get('user_id'),
                    'email',
                    'failed',
                    message.get('email_address'),
                    None,
                    {'error': error_msg}
                )
            except:
                pass
            
            failed += 1
            
            # Don't raise - continue processing other messages
    
    print(f"📊 Email processing complete: {processed} sent, {failed} failed")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': processed,
            'failed': failed,
            'timestamp': datetime.utcnow().isoformat()
        })
    }

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

