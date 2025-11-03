# Notification Preferences Setup Instructions

## Quick Setup - Run This SQL Script Now!

Copy and paste this SQL into your Supabase SQL Editor:

```sql
-- Create user_notifications table in Supabase
DROP TABLE IF EXISTS user_notifications;

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

CREATE INDEX idx_user_notifications_user_id ON user_notifications(user_id);

-- Disable RLS for development (re-enable in production)
ALTER TABLE user_notifications DISABLE ROW LEVEL SECURITY;
```

## What This Saves

The notification preferences table stores:

### Reminder Timing
- `appointment_hours_before`: "1", "2", "4", "12", "24", "48"
- `medication_minutes_before`: "0", "5", "10", "15", "30", "60"
- `tasks_reminder_time`: "HH:MM" format (e.g., "09:00")

### Email Preferences
- `email_appointments`: Boolean
- `email_medications`: Boolean
- `email_tasks`: Boolean
- `email_newsletter`: Boolean

### SMS Preferences
- `sms_appointments`: Boolean
- `sms_medications`: Boolean
- `sms_tasks`: Boolean

### WhatsApp Preferences
- `whatsapp_appointments`: Boolean
- `whatsapp_medications`: Boolean
- `whatsapp_tasks`: Boolean

### Push Notification Preferences
- `push_appointments`: Boolean
- `push_medications`: Boolean
- `push_tasks`: Boolean

**Total**: 16 fields

## After Running the Script

1. **Try saving your notification preferences** - they should save correctly!
2. **Reload the page** - preferences should load and display correctly
3. **All 16 fields** will be saved and loaded from Supabase

## Files Modified

### Frontend
- ✅ `patient-web-app/lib/api/auth-api.ts` - Added `UserNotifications` interface and API methods
- ✅ `patient-web-app/app/patient/profile/notifications/page.tsx` - Integrated load/save functionality

### Backend
- ✅ `yourhealth1place-backend/app/schemas/user.py` - Added `UserNotifications` schema
- ✅ `yourhealth1place-backend/app/schemas/__init__.py` - Exported `UserNotifications`
- ✅ `yourhealth1place-backend/app/api/v1/endpoints/auth.py` - Added GET/PUT `/auth/notifications` endpoints
- ✅ `yourhealth1place-backend/app/core/supabase_client.py` - Added `get_user_notifications` and `update_user_notifications` methods

## API Endpoints

- **GET** `/api/v1/auth/notifications` - Retrieve user notification preferences
- **PUT** `/api/v1/auth/notifications` - Update user notification preferences

## Production Note

**IMPORTANT**: The script disables RLS for development. For production:
1. Re-enable RLS: `ALTER TABLE user_notifications ENABLE ROW LEVEL SECURITY;`
2. Add proper RLS policies that allow service role access
3. Use the same pattern as `user_emergency` table

