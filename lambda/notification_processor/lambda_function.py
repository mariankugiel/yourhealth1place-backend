import json
import boto3
import psycopg2
import requests
from datetime import datetime
import os

def lambda_handler(event, context):
    """
    Process notification from SQS and send to backend via HTTP hook
    """
    
    print(f"Processing {len(event['Records'])} notification messages")
    
    processed = 0
    failed = 0
    
    try:
        # Database connection
        conn = psycopg2.connect(
            host=os.environ['DB_HOST'],
            database=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            port=os.environ.get('DB_PORT', '5432')
        )
        cursor = conn.cursor()
        
        for record in event['Records']:
            try:
                # Parse SNS message from SQS
                sns_message = json.loads(record['body'])
                notification_data = json.loads(sns_message['Message'])
                
                user_id = notification_data['user_id']
                notification_id = notification_data['notification_id']
                
                print(f"Processing notification {notification_id} for user {user_id}")
                
                # Send notification to backend via HTTP hook
                success = send_notification_to_backend(notification_data)
                
                if success:
                    # Mark notification as delivered
                    mark_notification_delivered(cursor, notification_id)
                    processed += 1
                    print(f"✅ Sent notification to user {user_id} via backend hook")
                else:
                    failed += 1
                    print(f"❌ Failed to send notification to user {user_id}")
                
            except Exception as e:
                print(f"❌ Error processing message: {e}")
                failed += 1
                # Don't raise here - we want to process other messages
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Processed: {processed}, Failed: {failed}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'processed': processed,
                'failed': failed,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        print(f"Error in notification processor: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def send_notification_to_backend(notification_data):
    """Send notification to backend via HTTP hook"""
    try:
        backend_url = os.environ['BACKEND_URL']
        hook_endpoint = f"{backend_url}/api/v1/notifications/webhook/lambda"
        
        payload = {
            'notification_data': notification_data,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'lambda_processor'
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {os.environ['LAMBDA_WEBHOOK_TOKEN']}"
        }
        
        response = requests.post(
            hook_endpoint,
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return True
        else:
            print(f"Backend hook failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"Error sending to backend: {e}")
        return False

def mark_notification_delivered(cursor, notification_id):
    """Mark notification as delivered"""
    try:
        query = """
            UPDATE notifications 
            SET delivered_at = %s 
            WHERE id = %s
        """
        cursor.execute(query, (datetime.utcnow(), notification_id))
    except Exception as e:
        print(f"Error marking notification as delivered: {e}")