import json
import boto3
import psycopg2
from datetime import datetime, timedelta
import os
import pytz

# Initialize AWS clients
sns_client = boto3.client('sns')

def lambda_handler(event, context):
    """
    Lambda function triggered by EventBridge every minute
    Checks for medication reminders that need to be sent
    """
    
    print(f"Starting reminder check at {datetime.utcnow()}")
    
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
        
        # Current UTC time
        now = datetime.utcnow()
        check_window = now + timedelta(minutes=2)  # Check next 2 minutes
        
        print(f"Checking reminders between {now} and {check_window}")
        
        # Query reminders that need to be sent
        query = """
            SELECT 
                mr.id as reminder_id,
                mr.medication_id,
                mr.user_id,
                mr.reminder_time,
                mr.user_timezone,
                mr.days_of_week,
                m.medication_name,
                m.dosage,
                m.frequency,
                u.email,
                u.timezone as user_timezone_pref
            FROM medication_reminders mr
            JOIN medications m ON mr.medication_id = m.id
            JOIN users u ON mr.user_id = u.id
            WHERE mr.enabled = true
              AND mr.status = 'active'
              AND mr.next_scheduled_at <= %s
              AND mr.next_scheduled_at > %s
        """
        
        cursor.execute(query, (check_window, now))
        reminders = cursor.fetchall()
        
        print(f"Found {len(reminders)} reminders due")
        
        results = []
        
        for reminder in reminders:
            reminder_id, med_id, user_id, reminder_time, timezone, days_of_week, med_name, dosage, frequency, email, user_timezone_pref = reminder
            
            print(f"Processing reminder {reminder_id} for user {user_id}")
            
            # Create notification in database
            insert_notification = """
                INSERT INTO notifications 
                (user_id, notification_type, title, message, medication_id, data, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            
            title = f"Time to take {med_name}"
            message = f"Remember to take your {med_name} ({dosage})"
            data = json.dumps({
                "medication_id": med_id,
                "medication_name": med_name,
                "dosage": dosage,
                "frequency": frequency,
                "reminder_time": str(reminder_time),
                "reminder_id": reminder_id
            })
            
            cursor.execute(insert_notification, (
                user_id, 
                'medication_reminder', 
                title, 
                message, 
                med_id, 
                data, 
                now
            ))
            notification_id = cursor.fetchone()[0]
            
            print(f"Created notification {notification_id}")
            
            # Publish to SNS
            sns_message = {
                "notification_id": notification_id,
                "user_id": user_id,
                "type": "medication_reminder",
                "title": title,
                "message": message,
                "data": json.loads(data),
                "timestamp": now.isoformat()
            }
            
            try:
                sns_response = sns_client.publish(
                    TopicArn=os.environ['SNS_TOPIC_ARN'],
                    Message=json.dumps(sns_message),
                    Subject='Medication Reminder',
                    MessageAttributes={
                        'user_id': {'DataType': 'Number', 'StringValue': str(user_id)},
                        'notification_type': {'DataType': 'String', 'StringValue': 'medication_reminder'},
                        'medication_id': {'DataType': 'Number', 'StringValue': str(med_id)}
                    }
                )
                
                print(f"Published to SNS: {sns_response['MessageId']}")
                
            except Exception as sns_error:
                print(f"Failed to publish to SNS: {sns_error}")
                continue
            
            # Update reminder's next_scheduled_at
            next_scheduled = calculate_next_scheduled_time(
                reminder_time, 
                json.loads(days_of_week), 
                timezone or user_timezone_pref or 'UTC'
            )
            
            update_query = """
                UPDATE medication_reminders
                SET last_sent_at = %s, next_scheduled_at = %s
                WHERE id = %s
            """
            cursor.execute(update_query, (now, next_scheduled, reminder_id))
            
            results.append({
                "reminder_id": reminder_id,
                "notification_id": notification_id,
                "user_id": user_id,
                "medication_name": med_name,
                "next_scheduled_at": next_scheduled.isoformat() if next_scheduled else None
            })
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Successfully processed {len(results)} reminders")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Processed {len(results)} reminders',
                'results': results,
                'timestamp': now.isoformat()
            })
        }
        
    except Exception as e:
        print(f"Error in reminder checker: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
        }

def calculate_next_scheduled_time(reminder_time, days_of_week, user_timezone):
    """Calculate the next UTC time when the reminder should be sent"""
    try:
        user_tz = pytz.timezone(user_timezone)
        utc_tz = pytz.UTC
        
        # Get current time in user's timezone
        now_user_tz = datetime.now(user_tz)
        
        # Check next 7 days for a valid reminder time
        for i in range(7):
            check_date = now_user_tz + timedelta(days=i)
            day_name = check_date.strftime('%A').lower()
            
            if day_name in days_of_week:
                # Create the reminder datetime for this day
                reminder_datetime = user_tz.localize(
                    datetime.combine(check_date.date(), reminder_time)
                )
                
                # Only use this if it's in the future
                if reminder_datetime > now_user_tz:
                    # Convert to UTC
                    return reminder_datetime.astimezone(utc_tz).replace(tzinfo=None)
        
        return None
        
    except Exception as e:
        print(f"Error calculating next scheduled time: {e}")
        return None
