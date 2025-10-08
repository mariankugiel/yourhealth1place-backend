import json
import boto3
import psycopg2
from datetime import datetime, timedelta
import os

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    """
    Handle WebSocket connection
    Store connection_id and user_id mapping
    """
    
    connection_id = event['requestContext']['connectionId']
    
    try:
        # Extract user_id from query parameters
        user_id = None
        if 'queryStringParameters' in event and event['queryStringParameters']:
            user_id = event['queryStringParameters'].get('user_id')
        
        if not user_id:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'user_id required in query parameters'})
            }
        
        user_id = int(user_id)
        
        # Store connection in database
        conn = psycopg2.connect(
            host=os.environ['DB_HOST'],
            database=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            port=os.environ.get('DB_PORT', '5432')
        )
        cursor = conn.cursor()
        
        # Remove any existing connections for this user
        cursor.execute(
            "UPDATE websocket_connections SET is_active = false WHERE user_id = %s",
            (user_id,)
        )
        
        # Insert new connection
        cursor.execute("""
            INSERT INTO websocket_connections 
            (connection_id, user_id, connected_at, is_active)
            VALUES (%s, %s, %s, %s)
        """, (connection_id, user_id, datetime.utcnow(), True))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ User {user_id} connected with connection_id: {connection_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Connected successfully'})
        }
        
    except Exception as e:
        print(f"Error in WebSocket connect: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
