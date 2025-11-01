#!/usr/bin/env python3
"""
Script to verify recipient fields in messages table
"""
import psycopg2
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def verify_recipient_fields():
    """Verify if recipient fields exist in the messages table"""
    
    # Parse DATABASE_URL
    db_url = settings.DATABASE_URL
    print(f"Database URL: {db_url}")
    
    if db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', '')
        parts = db_url.split('@')
        if len(parts) == 2:
            auth, host_db = parts
            username, password = auth.split(':')
            host_port, database = host_db.split('/')
            if ':' in host_port:
                host, port = host_port.split(':')
            else:
                host, port = host_port, '5432'
        else:
            print('Invalid DATABASE_URL format')
            return False
    else:
        print('Not a PostgreSQL URL')
        return False

    print(f'Connecting to: {host}:{port}/{database}')

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password
        )
        cursor = conn.cursor()
        
        # Check if recipient fields exist
        cursor.execute('''
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'messages' 
            AND column_name LIKE 'recipient%';
        ''')
        
        recipient_columns = cursor.fetchall()
        print('Recipient columns in messages table:')
        for col in recipient_columns:
            print(f'  - {col[0]}')
        
        if not recipient_columns:
            print('❌ No recipient columns found!')
            return False
        else:
            print('✅ Recipient columns found!')
            return True
        
    except Exception as e:
        print(f'❌ Database check failed: {e}')
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = verify_recipient_fields()
    if success:
        print("\n🎉 Recipient fields verification completed!")
    else:
        print("\n💥 Recipient fields verification failed!")
        sys.exit(1)
