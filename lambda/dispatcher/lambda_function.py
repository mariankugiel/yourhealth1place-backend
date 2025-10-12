"""
Lambda Dispatcher - Triggered by EventBridge every 5 minutes
Calls Backend API to check and process due medication reminders
"""
import json
import requests
from datetime import datetime
import os

# ============================================================================
# CONFIGURATION - Update these values with your actual configuration
# ============================================================================
BACKEND_URL = 'https://your-backend-domain.com'  # Your backend API URL
LAMBDA_API_TOKEN = 'your-secure-token-here'  # Token for backend authentication

def lambda_handler(event, context):
    """
    EventBridge trigger function
    Lightweight - only calls backend API
    """
    
    print(f"🔔 Reminder check triggered at {datetime.utcnow().isoformat()}")
    
    try:
        # Backend API endpoint
        api_endpoint = f"{BACKEND_URL}/api/v1/medication-reminders/check-due"
        
        # Authentication
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {LAMBDA_API_TOKEN}"
        }
        
        # Payload
        payload = {
            'triggered_by': 'eventbridge',
            'trigger_time': datetime.utcnow().isoformat(),
            'check_window_minutes': 5
        }
        
        print(f"📤 Calling backend API: {api_endpoint}")
        
        # Call backend API
        response = requests.post(
            api_endpoint,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        # Check response
        if response.status_code == 200:
            result = response.json()
            processed_count = result.get('processed_count', 0)
            print(f"✅ Successfully processed {processed_count} reminders")
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Reminder check completed',
                    'processed_count': processed_count,
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
        else:
            error_msg = f"Backend API failed: {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")
            
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': error_msg,
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
            
    except requests.Timeout:
        error_msg = "Backend API timeout after 30 seconds"
        print(f"❌ {error_msg}")
        return {
            'statusCode': 504,
            'body': json.dumps({
                'error': error_msg,
                'timestamp': datetime.utcnow().isoformat()
            })
        }
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_msg,
                'timestamp': datetime.utcnow().isoformat()
            })
        }

