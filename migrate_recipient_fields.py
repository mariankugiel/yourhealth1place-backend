#!/usr/bin/env python3
"""
Script to add recipient fields to messages table
"""
import psycopg2
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def run_migration():
    """Run the migration to add recipient fields to messages table"""
    
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
        
        print("Adding recipient fields to messages table...")
        
        # Add recipient fields
        cursor.execute('''
            ALTER TABLE messages 
            ADD COLUMN IF NOT EXISTS recipient_id INTEGER,
            ADD COLUMN IF NOT EXISTS recipient_name VARCHAR(255),
            ADD COLUMN IF NOT EXISTS recipient_role VARCHAR(100),
            ADD COLUMN IF NOT EXISTS recipient_type VARCHAR(50) DEFAULT 'user',
            ADD COLUMN IF NOT EXISTS recipient_avatar VARCHAR(500);
        ''')
        
        print("Adding foreign key constraint...")
        # Add foreign key constraint (check if it exists first)
        cursor.execute('''
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'messages' 
            AND constraint_name = 'fk_messages_recipient_id';
        ''')
        
        if not cursor.fetchone():
            cursor.execute('''
                ALTER TABLE messages 
                ADD CONSTRAINT fk_messages_recipient_id 
                FOREIGN KEY (recipient_id) REFERENCES users(id);
            ''')
        else:
            print("Foreign key constraint already exists")
        
        print("Adding indexes...")
        # Add indexes
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_messages_recipient_id ON messages(recipient_id);
            CREATE INDEX IF NOT EXISTS idx_messages_sender_recipient ON messages(sender_id, recipient_id);
        ''')
        
        print("Updating existing messages with recipient information...")
        # Update existing messages
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
                    WHEN c.user_id = m.sender_id THEN c.contact_type
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
        
        print("Making recipient fields NOT NULL...")
        # Make fields NOT NULL
        cursor.execute('''
            ALTER TABLE messages 
            ALTER COLUMN recipient_id SET NOT NULL,
            ALTER COLUMN recipient_name SET NOT NULL,
            ALTER COLUMN recipient_role SET NOT NULL,
            ALTER COLUMN recipient_type SET NOT NULL;
        ''')
        
        conn.commit()
        print('✅ Migration completed successfully!')
        print('✅ Added recipient fields to messages table')
        print('✅ Updated existing messages with recipient information')
        print('✅ Added indexes for better performance')
        return True
        
    except Exception as e:
        print(f'❌ Migration failed: {e}')
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("\n🎉 Database migration completed successfully!")
        print("You can now restart the backend server.")
    else:
        print("\n💥 Database migration failed!")
        sys.exit(1)
