"""
WebSocket Sender Lambda - Processes WebSocket queue and sends to connected clients
"""
import json
import boto3
from datetime import datetime
import os

# Initialize AWS clients
apigateway = boto3.client('apigatewaymanagementapi', endpoint_url=os.environ['WEBSOCKET_ENDPOINT'])

def lambda_handler(event, context):
    """
    Process WebSocket notifications from SQS FIFO queue
    Send to connected clients via API Gateway WebSocket
    """
    
    print(f"🔌 Processing {len(event['Records'])} WebSocket messages")
    
    processed = 0
    failed = 0
    
    for record in event['Records']:
        try:
            # Parse message
            message = json.loads(record['body'])
            
            notification_id = message.get('notification_id')
            user_id = message.get('user_id')
            connection_id = message.get('connection_id')
            
            print(f"📡 Sending WebSocket message to connection {connection_id} for notification {notification_id}")
            
            # Prepare WebSocket message
            ws_message = {
                'type': 'notification',
                'notification_id': notification_id,
                'data': {
                    'title': message.get('title'),
                    'message': message.get('message'),
                    'priority': message.get('priority', 'normal'),
                    'notification_type': message.get('notification_type'),
                    'metadata': message.get('metadata', {})
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Send via API Gateway WebSocket
            try:
                apigateway.post_to_connection(
                    ConnectionId=connection_id,
                    Data=json.dumps(ws_message).encode('utf-8')
                )
                
                print(f"✅ WebSocket message sent successfully to {connection_id}")
                
                # Log delivery
                log_delivery(notification_id, user_id, 'websocket', 'delivered', connection_id, None, {'success': True})
                
                processed += 1
                
            except apigateway.exceptions.GoneException:
                # Connection is no longer available
                print(f"⚠️ Connection {connection_id} is gone. Marking as inactive.")
                
                # Mark connection as inactive in backend
                mark_connection_inactive(connection_id)
                
                # Log as failed
                log_delivery(notification_id, user_id, 'websocket', 'failed', connection_id, None, {'error': 'Connection gone'})
                
                failed += 1
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Failed to send WebSocket message: {error_msg}")
            
            # Log failure
            try:
                log_delivery(
                    message.get('notification_id'),
                    message.get('user_id'),
                    'websocket',
                    'failed',
                    message.get('connection_id'),
                    None,
                    {'error': error_msg}
                )
            except:
                pass
            
            failed += 1
    
    print(f"📊 WebSocket processing complete: {processed} sent, {failed} failed")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': processed,
            'failed': failed,
            'timestamp': datetime.utcnow().isoformat()
        })
    }

def mark_connection_inactive(connection_id):
    """Mark WebSocket connection as inactive in backend"""
    try:
        backend_url = os.environ['BACKEND_URL']
        endpoint = f"{backend_url}/api/v1/websocket/connections/{connection_id}/deactivate"
        
        import requests
        requests.post(
            endpoint,
            headers={'Authorization': f"Bearer {os.environ['LAMBDA_API_TOKEN']}"},
            timeout=5
        )
    except Exception as e:
        print(f"⚠️ Failed to mark connection inactive: {e}")

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

