-- Create user_notifications table in Supabase
-- Run this script in your Supabase SQL editor

-- Drop table if it exists (for development only)
DROP TABLE IF EXISTS user_notifications;

-- Create user_notifications table
CREATE TABLE user_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Reminder timing settings
    appointment_hours_before VARCHAR(10),
    medication_minutes_before VARCHAR(10),
    tasks_reminder_time VARCHAR(10),
    
    -- Email preferences
    email_appointments BOOLEAN DEFAULT true,
    email_medications BOOLEAN DEFAULT true,
    email_tasks BOOLEAN DEFAULT false,
    email_newsletter BOOLEAN DEFAULT false,
    
    -- SMS preferences
    sms_appointments BOOLEAN DEFAULT false,
    sms_medications BOOLEAN DEFAULT false,
    sms_tasks BOOLEAN DEFAULT false,
    
    -- WhatsApp preferences
    whatsapp_appointments BOOLEAN DEFAULT true,
    whatsapp_medications BOOLEAN DEFAULT false,
    whatsapp_tasks BOOLEAN DEFAULT true,
    
    -- Push notification preferences
    push_appointments BOOLEAN DEFAULT true,
    push_medications BOOLEAN DEFAULT true,
    push_tasks BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index on user_id for faster lookups
CREATE INDEX idx_user_notifications_user_id ON user_notifications(user_id);

-- Enable RLS (Row Level Security)
ALTER TABLE user_notifications ENABLE ROW LEVEL SECURITY;

-- Create policy: Users can only see their own notification preferences
CREATE POLICY "Users can view their own notifications"
    ON user_notifications FOR SELECT
    USING (auth.uid() = user_id);

-- Create policy: Users can insert their own notification preferences
CREATE POLICY "Users can insert their own notifications"
    ON user_notifications FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Create policy: Users can update their own notification preferences
CREATE POLICY "Users can update their own notifications"
    ON user_notifications FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Create policy: Users can delete their own notification preferences
CREATE POLICY "Users can delete their own notifications"
    ON user_notifications FOR DELETE
    USING (auth.uid() = user_id);

-- Add comment to table
COMMENT ON TABLE user_notifications IS 'Stores user notification preferences and reminder settings';

