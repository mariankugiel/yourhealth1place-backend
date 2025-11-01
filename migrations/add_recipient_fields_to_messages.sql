-- Add recipient fields to messages table
ALTER TABLE messages 
ADD COLUMN recipient_id INTEGER REFERENCES users(id),
ADD COLUMN recipient_name VARCHAR(255),
ADD COLUMN recipient_role VARCHAR(100),
ADD COLUMN recipient_type VARCHAR(50) DEFAULT 'user',
ADD COLUMN recipient_avatar VARCHAR(500);

-- Add indexes for better performance
CREATE INDEX idx_messages_recipient_id ON messages(recipient_id);
CREATE INDEX idx_messages_sender_recipient ON messages(sender_id, recipient_id);

-- Update existing messages with recipient information based on conversation data
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
JOIN conversations c ON m.conversation_id = c.id;

-- Make recipient fields NOT NULL after populating them
ALTER TABLE messages 
ALTER COLUMN recipient_id SET NOT NULL,
ALTER COLUMN recipient_name SET NOT NULL,
ALTER COLUMN recipient_role SET NOT NULL,
ALTER COLUMN recipient_type SET NOT NULL;
