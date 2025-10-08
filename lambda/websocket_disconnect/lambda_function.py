import json
import boto3
import psycopg2
from datetime import datetime
import os

def lambda_handler(event, context):
    """
    Handle WebSocket disconnection
    Remove connection from database
    """
    
    connection_id = event['requestContext']['connectionId']
    
    try:
        # Remove connection from database
        conn = psycopg2.connect(
            host=os.environ['DB_HOST'],
            database=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            port=os.environ.get('DB_PORT', '5432')
        )
        cursor = conn.cursor()
        
        # Mark connection as inactive
        cursor.execute(
            "UPDATE websocket_connections SET is_active = false WHERE connection_id = %s",
            (connection_id,)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"❌ Connection {connection_id} disconnected")
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Disconnected'})
        }
        
    except Exception as e:
        print(f"Error in WebSocket disconnect: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
