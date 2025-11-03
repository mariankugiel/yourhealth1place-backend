-- Create all user preference tables in Supabase
-- Run this script in your Supabase SQL editor

-- ============================================================================
-- 1. USER NOTIFICATIONS TABLE
-- ============================================================================
DROP TABLE IF EXISTS user_notifications;

CREATE TABLE user_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    appointment_hours_before VARCHAR(10),
    medication_minutes_before VARCHAR(10),
    tasks_reminder_time VARCHAR(10),
    
    email_appointments BOOLEAN DEFAULT true,
    email_medications BOOLEAN DEFAULT true,
    email_tasks BOOLEAN DEFAULT false,
    email_newsletter BOOLEAN DEFAULT false,
    
    sms_appointments BOOLEAN DEFAULT false,
    sms_medications BOOLEAN DEFAULT false,
    sms_tasks BOOLEAN DEFAULT false,
    
    whatsapp_appointments BOOLEAN DEFAULT true,
    whatsapp_medications BOOLEAN DEFAULT false,
    whatsapp_tasks BOOLEAN DEFAULT true,
    
    push_appointments BOOLEAN DEFAULT true,
    push_medications BOOLEAN DEFAULT true,
    push_tasks BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_notifications_user_id ON user_notifications(user_id);
ALTER TABLE user_notifications DISABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 2. USER INTEGRATIONS TABLE
-- ============================================================================
DROP TABLE IF EXISTS user_integrations;

CREATE TABLE user_integrations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    google_fit BOOLEAN DEFAULT false,
    fitbit BOOLEAN DEFAULT false,
    garmin BOOLEAN DEFAULT false,
    apple_health BOOLEAN DEFAULT false,
    withings BOOLEAN DEFAULT false,
    oura BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_integrations_user_id ON user_integrations(user_id);
ALTER TABLE user_integrations DISABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 3. USER PRIVACY TABLE
-- ============================================================================
DROP TABLE IF EXISTS user_privacy;

CREATE TABLE user_privacy (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    share_anonymized_data BOOLEAN DEFAULT true,
    share_analytics BOOLEAN DEFAULT false,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_privacy_user_id ON user_privacy(user_id);
ALTER TABLE user_privacy DISABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 4. USER SHARED ACCESS TABLE
-- ============================================================================
DROP TABLE IF EXISTS user_shared_access;

CREATE TABLE user_shared_access (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    health_professionals JSONB,
    family_friends JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_user_shared_access_user_id ON user_shared_access(user_id);
ALTER TABLE user_shared_access DISABLE ROW LEVEL SECURITY;

-- ============================================================================
-- VERIFY TABLES
-- ============================================================================
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('user_notifications', 'user_integrations', 'user_privacy', 'user_shared_access');

