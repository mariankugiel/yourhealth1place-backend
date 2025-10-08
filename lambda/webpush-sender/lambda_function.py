"""
Web Push Sender Lambda - Processes Web Push queue and sends via VAPID
"""
import json
from datetime import datetime
import os
from pywebpush import webpush, WebPushException

def lambda_handler(event, context):
    """
    Process Web Push notifications from SQS FIFO queue
    Send push notifications via VAPID to Service Workers
    """
    
    print(f"🔔 Processing {len(event['Records'])} Web Push messages")
    
    processed = 0
    failed = 0
    
    for record in event['Records']:
        try:
            # Parse message
            message = json.loads(record['body'])
            
            notification_id = message.get('notification_id')
            user_id = message.get('user_id')
            subscription_info = message.get('subscription_info')
            
            print(f"📲 Sending Web Push for notification {notification_id}")
            
            # Prepare push payload
            push_payload = {
                'notification': {
                    'title': message.get('title'),
                    'body': message.get('message'),
                    'icon': '/icon-192x192.png',
                    'badge': '/badge-72x72.png',
                    'data': {
                        'notification_id': notification_id,
                        'notification_type': message.get('notification_type'),
                        'priority': message.get('priority', 'normal'),
                        'url': message.get('url', '/'),
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    'actions': [
                        {
                            'action': 'view',
                            'title': 'View'
                        },
                        {
                            'action': 'dismiss',
                            'title': 'Dismiss'
                        }
                    ],
                    'requireInteraction': message.get('priority') in ['high', 'urgent'],
                    'vibrate': [200, 100, 200] if message.get('priority') in ['high', 'urgent'] else [100],
                    'tag': f"notification-{notification_id}"
                }
            }
            
            # Send Web Push
            try:
                response = webpush(
                    subscription_info=subscription_info,
                    data=json.dumps(push_payload),
                    vapid_private_key=os.environ['VAPID_PRIVATE_KEY'],
                    vapid_claims={
                        "sub": os.environ['VAPID_SUBJECT']
                    }
                )
                
                print(f"✅ Web Push sent successfully. Status: {response.status_code}")
                
                # Log delivery
                log_delivery(
                    notification_id,
                    user_id,
                    'web_push',
                    'sent',
                    subscription_info['endpoint'],
                    None,
                    {'status_code': response.status_code}
                )
                
                processed += 1
                
            except WebPushException as e:
                error_msg = f"Web Push failed: {e}"
                print(f"❌ {error_msg}")
                
                # Check if subscription is expired (410 Gone)
                if e.response and e.response.status_code == 410:
                    print(f"⚠️ Subscription expired. Marking as inactive.")
                    mark_subscription_inactive(subscription_info['endpoint'])
                
                # Log failure
                log_delivery(
                    notification_id,
                    user_id,
                    'web_push',
                    'failed',
                    subscription_info['endpoint'],
                    None,
                    {'error': error_msg, 'status_code': e.response.status_code if e.response else None}
                )
                
                failed += 1
                
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Failed to process Web Push: {error_msg}")
            
            # Log failure
            try:
                log_delivery(
                    message.get('notification_id'),
                    message.get('user_id'),
                    'web_push',
                    'failed',
                    message.get('subscription_info', {}).get('endpoint'),
                    None,
                    {'error': error_msg}
                )
            except:
                pass
            
            failed += 1
    
    print(f"📊 Web Push processing complete: {processed} sent, {failed} failed")
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'processed': processed,
            'failed': failed,
            'timestamp': datetime.utcnow().isoformat()
        })
    }

def mark_subscription_inactive(endpoint):
    """Mark Web Push subscription as inactive in backend"""
    try:
        backend_url = os.environ['BACKEND_URL']
        api_endpoint = f"{backend_url}/api/v1/web-push/subscriptions/deactivate"
        
        import requests
        requests.post(
            api_endpoint,
            json={'endpoint': endpoint},
            headers={'Authorization': f"Bearer {os.environ['LAMBDA_API_TOKEN']}"},
            timeout=5
        )
    except Exception as e:
        print(f"⚠️ Failed to mark subscription inactive: {e}")

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

