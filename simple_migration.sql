-- Simple migration to add recipient fields
ALTER TABLE messages ADD COLUMN IF NOT EXISTS recipient_id INTEGER;
ALTER TABLE messages ADD COLUMN IF NOT EXISTS recipient_name VARCHAR(255);
ALTER TABLE messages ADD COLUMN IF NOT EXISTS recipient_role VARCHAR(100);
ALTER TABLE messages ADD COLUMN IF NOT EXISTS recipient_type VARCHAR(50) DEFAULT 'user';
ALTER TABLE messages ADD COLUMN IF NOT EXISTS recipient_avatar VARCHAR(500);

-- Add foreign key constraint
ALTER TABLE messages ADD CONSTRAINT fk_messages_recipient_id FOREIGN KEY (recipient_id) REFERENCES users(id);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_messages_recipient_id ON messages(recipient_id);
CREATE INDEX IF NOT EXISTS idx_messages_sender_recipient ON messages(sender_id, recipient_id);

-- Update existing messages with recipient information
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

-- Make fields NOT NULL
ALTER TABLE messages ALTER COLUMN recipient_id SET NOT NULL;
ALTER TABLE messages ALTER COLUMN recipient_name SET NOT NULL;
ALTER TABLE messages ALTER COLUMN recipient_role SET NOT NULL;
ALTER TABLE messages ALTER COLUMN recipient_type SET NOT NULL;
