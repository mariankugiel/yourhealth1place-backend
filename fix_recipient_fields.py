#!/usr/bin/env python3
"""
Script to fix recipient fields in messages table
"""
import psycopg2
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def fix_recipient_fields():
    """Fix recipient fields in messages table"""
    
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
            print('❌ No recipient columns found! Adding them...')
            
            # Add recipient fields
            cursor.execute('''
                ALTER TABLE messages 
                ADD COLUMN recipient_id INTEGER,
                ADD COLUMN recipient_name VARCHAR(255),
                ADD COLUMN recipient_role VARCHAR(100),
                ADD COLUMN recipient_type VARCHAR(50) DEFAULT 'user',
                ADD COLUMN recipient_avatar VARCHAR(500);
            ''')
            
            # Add foreign key constraint
            cursor.execute('''
                ALTER TABLE messages 
                ADD CONSTRAINT fk_messages_recipient_id 
                FOREIGN KEY (recipient_id) REFERENCES users(id);
            ''')
            
            # Add indexes
            cursor.execute('''
                CREATE INDEX idx_messages_recipient_id ON messages(recipient_id);
                CREATE INDEX idx_messages_sender_recipient ON messages(sender_id, recipient_id);
            ''')
            
            conn.commit()
            print('✅ Recipient fields added successfully!')
        
        # Check if there are any messages with NULL recipient fields
        cursor.execute('SELECT COUNT(*) FROM messages WHERE recipient_id IS NULL;')
        null_count = cursor.fetchone()[0]
        print(f'Messages with NULL recipient_id: {null_count}')
        
        # Check total messages
        cursor.execute('SELECT COUNT(*) FROM messages;')
        total_count = cursor.fetchone()[0]
        print(f'Total messages: {total_count}')
        
        if null_count > 0:
            print('Updating messages with NULL recipient fields...')
            
            # Update existing messages with recipient information
            cursor.execute('''
                UPDATE messages 
                SET 
                    recipient_id = CASE 
                        WHEN c.user_id = m.sender_id THEN c.contact_id
                        ELSE c.user_id
                    END,
                    recipient_name = CASE 
                        WHEN c.user_id = m.sender_id THEN c.contact_name
                        ELSE 'Current User'
                    END,
                    recipient_role = CASE 
                        WHEN c.user_id = m.sender_id THEN c.contact_role
                        ELSE 'Patient'
                    END,
                    recipient_type = CASE 
                        WHEN c.user_id = m.sender_id THEN c.contact_type::text
                        ELSE 'user'
                    END,
                    recipient_avatar = CASE 
                        WHEN c.user_id = m.sender_id THEN c.contact_avatar
                        ELSE NULL
                    END
                FROM messages m
                JOIN conversations c ON m.conversation_id = c.id
                WHERE m.recipient_id IS NULL;
            ''')
            
            # Make fields NOT NULL
            cursor.execute('''
                ALTER TABLE messages 
                ALTER COLUMN recipient_id SET NOT NULL,
                ALTER COLUMN recipient_name SET NOT NULL,
                ALTER COLUMN recipient_role SET NOT NULL,
                ALTER COLUMN recipient_type SET NOT NULL;
            ''')
            
            conn.commit()
            print('✅ Updated messages with recipient information!')
        
        # Final check
        cursor.execute('SELECT COUNT(*) FROM messages WHERE recipient_id IS NULL;')
        final_null_count = cursor.fetchone()[0]
        print(f'Final messages with NULL recipient_id: {final_null_count}')
        
        return True
        
    except Exception as e:
        print(f'❌ Database operation failed: {e}')
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = fix_recipient_fields()
    if success:
        print("\n🎉 Recipient fields fix completed!")
    else:
        print("\n💥 Recipient fields fix failed!")
        sys.exit(1)
