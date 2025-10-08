import json

def lambda_handler(event, context):
    """
    Handle default WebSocket messages (ping/pong, etc.)
    """
    
    connection_id = event['requestContext']['connectionId']
    
    try:
        body = json.loads(event.get('body', '{}'))
        
        # Handle ping messages
        if body.get('action') == 'ping':
            return {
                'statusCode': 200,
                'body': json.dumps({'action': 'pong'})
            }
        
        # Handle other messages
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Message received'})
        }
        
    except json.JSONDecodeError:
        # Handle plain text messages
        body = event.get('body', '')
        if body == 'ping':
            return {
                'statusCode': 200,
                'body': json.dumps({'action': 'pong'})
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Message received'})
        }
        
    except Exception as e:
        print(f"Error in WebSocket default handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
