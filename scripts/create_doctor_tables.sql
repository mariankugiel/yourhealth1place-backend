-- ============================================================================
-- Script to Create Doctor Tables in Single Supabase Project
-- ============================================================================
-- This script creates:
--   1. doctor_profiles table (replaces user_profiles for doctors)
--   2. doctor_acuity_calendars table (replaces acuity_calendars)
--
-- IMPORTANT: 
--   - Run this script in the MAIN Supabase project (same as patient project)
--   - These tables follow the doctor_* naming convention
-- ============================================================================

-- ============================================================================
-- Step 0: Drop existing tables if they exist (to fix FK constraints)
-- ============================================================================
-- Note: If you've already run this script and need to fix the FK constraint,
-- uncomment the following lines to drop and recreate the tables.

-- DROP TABLE IF EXISTS doctor_acuity_calendars CASCADE;
-- DROP TABLE IF EXISTS doctor_profiles CASCADE;

-- ============================================================================
-- Step 1: Create doctor_profiles table
-- ============================================================================

CREATE TABLE IF NOT EXISTS doctor_profiles (
    -- Primary key (UUID from Supabase auth.users)
    -- Note: No foreign key constraint because the users table is in the main PostgreSQL database,
    -- not in Supabase. The relationship is maintained via supabase_user_id in the main users table.
    id UUID PRIMARY KEY,
    
    -- User ID (UUID from Supabase auth.users, same as id in most cases)
    -- This is the Supabase auth.users.id, which links to the main DB users table via supabase_user_id
    user_id UUID,
    
    -- Name fields
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100),
    full_name VARCHAR(255),
    
    -- Contact information
    phone_number VARCHAR(20),
    phone_country_code VARCHAR(10),
    address TEXT,
    
    -- Doctor-specific fields
    specialty VARCHAR(255),
    license_number VARCHAR(100),
    bio TEXT,
    
    -- Profile image
    avatar_url VARCHAR(500),
    
    -- Acuity integration (kept for backward compatibility, but use doctor_acuity_calendars table)
    acuity_owner_id VARCHAR(255),
    
    -- Onboarding status
    onboarding_completed BOOLEAN DEFAULT FALSE,
    onboarding_skipped BOOLEAN DEFAULT FALSE,
    onboarding_skipped_at TIMESTAMP WITH TIME ZONE,
    is_new_user BOOLEAN DEFAULT TRUE,
    
    -- Metadata (JSONB for flexibility)
    metadata JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- Step 2: Create doctor_acuity_calendars table
-- ============================================================================

CREATE TABLE IF NOT EXISTS doctor_acuity_calendars (
    id SERIAL PRIMARY KEY,
    calendar_id VARCHAR(255) NOT NULL UNIQUE,
    doctor_id UUID NOT NULL,  -- References doctor_profiles.id (logical reference, no FK constraint)
    -- Note: No foreign key constraint because doctor_profiles.id is a UUID from Supabase auth.users
    -- The relationship is maintained at the application level
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- Step 3: Create indexes for performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_doctor_profiles_user_id ON doctor_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_doctor_profiles_specialty ON doctor_profiles(specialty);
CREATE INDEX IF NOT EXISTS idx_doctor_acuity_calendars_doctor_id ON doctor_acuity_calendars(doctor_id);
CREATE INDEX IF NOT EXISTS idx_doctor_acuity_calendars_calendar_id ON doctor_acuity_calendars(calendar_id);

-- ============================================================================
-- Step 4: Enable Row Level Security (RLS)
-- ============================================================================

-- Enable RLS on doctor_profiles
ALTER TABLE doctor_profiles ENABLE ROW LEVEL SECURITY;

-- Enable RLS on doctor_acuity_calendars
ALTER TABLE doctor_acuity_calendars ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- Step 5: Create RLS Policies
-- ============================================================================

-- Policy: Doctors can read their own profile
CREATE POLICY "Doctors can read own profile"
    ON doctor_profiles
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy: Doctors can update their own profile
CREATE POLICY "Doctors can update own profile"
    ON doctor_profiles
    FOR UPDATE
    USING (auth.uid() = user_id);

-- Policy: Service role can read all doctor profiles (for backend operations)
CREATE POLICY "Service role can read all doctor profiles"
    ON doctor_profiles
    FOR SELECT
    USING (auth.role() = 'service_role');

-- Policy: Service role can insert doctor profiles
CREATE POLICY "Service role can insert doctor profiles"
    ON doctor_profiles
    FOR INSERT
    WITH CHECK (auth.role() = 'service_role');

-- Policy: Service role can update all doctor profiles
CREATE POLICY "Service role can update all doctor profiles"
    ON doctor_profiles
    FOR UPDATE
    USING (auth.role() = 'service_role');

-- Policy: Service role can read all acuity calendars
CREATE POLICY "Service role can read all acuity calendars"
    ON doctor_acuity_calendars
    FOR SELECT
    USING (auth.role() = 'service_role');

-- Policy: Service role can insert acuity calendars
CREATE POLICY "Service role can insert acuity calendars"
    ON doctor_acuity_calendars
    FOR INSERT
    WITH CHECK (auth.role() = 'service_role');

-- Policy: Service role can update acuity calendars
CREATE POLICY "Service role can update acuity calendars"
    ON doctor_acuity_calendars
    FOR UPDATE
    USING (auth.role() = 'service_role');

-- ============================================================================
-- Step 6: Insert 6 Doctor Profiles
-- ============================================================================
-- IMPORTANT: These UUIDs must match existing auth.users in Supabase
-- If these users don't exist in auth.users, create them first or update the UUIDs

-- Doctor 1: Dr. Sarah Johnson - Cardiology
-- Email: okisahandsome@gmail.com
-- UUID: 7a69a0da-95e0-457c-be8b-b2a4f4d52142
-- Calendar ID: 12526411
INSERT INTO doctor_profiles (
    id,
    user_id,
    first_name,
    last_name,
    full_name,
    phone_number,
    phone_country_code,
    specialty,
    acuity_owner_id,
    onboarding_completed,
    is_new_user,
    created_at,
    updated_at
) VALUES (
    '7a69a0da-95e0-457c-be8b-b2a4f4d52142'::uuid,
    '7a69a0da-95e0-457c-be8b-b2a4f4d52142'::uuid,
    'Sarah',
    'Johnson',
    'Dr. Sarah Johnson',
    '5550101',
    '+1',
    'Cardiology',
    '36512122',  -- Acuity owner ID (shared across all doctors)
    TRUE,
    FALSE,
    NOW(),
    NOW()
) ON CONFLICT (id) DO UPDATE SET
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    full_name = EXCLUDED.full_name,
    phone_number = EXCLUDED.phone_number,
    phone_country_code = EXCLUDED.phone_country_code,
    specialty = EXCLUDED.specialty,
    acuity_owner_id = EXCLUDED.acuity_owner_id,
    updated_at = NOW();

-- Doctor 2: Dr. Michael Chen - Dermatology
-- Email: krystian.djk@gmail.com
-- UUID: 89dd4d34-2dda-49ae-a68a-8931ab662fc1
-- Calendar ID: 12967393
INSERT INTO doctor_profiles (
    id,
    user_id,
    first_name,
    last_name,
    full_name,
    phone_number,
    phone_country_code,
    specialty,
    acuity_owner_id,
    onboarding_completed,
    is_new_user,
    created_at,
    updated_at
) VALUES (
    '89dd4d34-2dda-49ae-a68a-8931ab662fc1'::uuid,
    '89dd4d34-2dda-49ae-a68a-8931ab662fc1'::uuid,
    'Michael',
    'Chen',
    'Dr. Michael Chen',
    '5550102',
    '+1',
    'Dermatology',
    '36512122',
    TRUE,
    FALSE,
    NOW(),
    NOW()
) ON CONFLICT (id) DO UPDATE SET
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    full_name = EXCLUDED.full_name,
    phone_number = EXCLUDED.phone_number,
    phone_country_code = EXCLUDED.phone_country_code,
    specialty = EXCLUDED.specialty,
    acuity_owner_id = EXCLUDED.acuity_owner_id,
    updated_at = NOW();

-- Doctor 3: Dr. Emily Rodriguez - Pediatrics
-- Email: kdajka98@gmail.com
-- UUID: 973ab625-08d0-4f15-aae7-6dbdad0c1233
-- Calendar ID: 12983864
INSERT INTO doctor_profiles (
    id,
    user_id,
    first_name,
    last_name,
    full_name,
    phone_number,
    phone_country_code,
    specialty,
    acuity_owner_id,
    onboarding_completed,
    is_new_user,
    created_at,
    updated_at
) VALUES (
    '973ab625-08d0-4f15-aae7-6dbdad0c1233'::uuid,
    '973ab625-08d0-4f15-aae7-6dbdad0c1233'::uuid,
    'Emily',
    'Rodriguez',
    'Dr. Emily Rodriguez',
    '5550103',
    '+1',
    'Pediatrics',
    '36512122',
    TRUE,
    FALSE,
    NOW(),
    NOW()
) ON CONFLICT (id) DO UPDATE SET
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    full_name = EXCLUDED.full_name,
    phone_number = EXCLUDED.phone_number,
    phone_country_code = EXCLUDED.phone_country_code,
    specialty = EXCLUDED.specialty,
    acuity_owner_id = EXCLUDED.acuity_owner_id,
    updated_at = NOW();

-- Doctor 4: Dr. James Wilson - Orthopedic Surgery
-- Email: mariankugiel819@gmail.com
-- UUID: 9816f018-9f17-40fe-9389-09cc835d3c97
-- Calendar ID: 12983866
INSERT INTO doctor_profiles (
    id,
    user_id,
    first_name,
    last_name,
    full_name,
    phone_number,
    phone_country_code,
    specialty,
    acuity_owner_id,
    onboarding_completed,
    is_new_user,
    created_at,
    updated_at
) VALUES (
    '9816f018-9f17-40fe-9389-09cc835d3c97'::uuid,
    '9816f018-9f17-40fe-9389-09cc835d3c97'::uuid,
    'James',
    'Wilson',
    'Dr. James Wilson',
    '5550104',
    '+1',
    'Orthopedic Surgery',
    '36512122',
    TRUE,
    FALSE,
    NOW(),
    NOW()
) ON CONFLICT (id) DO UPDATE SET
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    full_name = EXCLUDED.full_name,
    phone_number = EXCLUDED.phone_number,
    phone_country_code = EXCLUDED.phone_country_code,
    specialty = EXCLUDED.specialty,
    acuity_owner_id = EXCLUDED.acuity_owner_id,
    updated_at = NOW();

-- Doctor 5: Dr. Lisa Anderson - Psychiatry
-- Email: yourhealth1place@gmail.com
-- UUID: 9e7500be-7a02-40aa-b991-62f740e1e4fe
-- Calendar ID: 12983868
INSERT INTO doctor_profiles (
    id,
    user_id,
    first_name,
    last_name,
    full_name,
    phone_number,
    phone_country_code,
    specialty,
    acuity_owner_id,
    onboarding_completed,
    is_new_user,
    created_at,
    updated_at
) VALUES (
    '9e7500be-7a02-40aa-b991-62f740e1e4fe'::uuid,
    '9e7500be-7a02-40aa-b991-62f740e1e4fe'::uuid,
    'Lisa',
    'Anderson',
    'Dr. Lisa Anderson',
    '5550105',
    '+1',
    'Psychiatry',
    '36512122',
    TRUE,
    FALSE,
    NOW(),
    NOW()
) ON CONFLICT (id) DO UPDATE SET
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    full_name = EXCLUDED.full_name,
    phone_number = EXCLUDED.phone_number,
    phone_country_code = EXCLUDED.phone_country_code,
    specialty = EXCLUDED.specialty,
    acuity_owner_id = EXCLUDED.acuity_owner_id,
    updated_at = NOW();

-- Doctor 6: Dr. Robert Taylor - General Practice
-- Email: damian.nowa@gmail.com
-- UUID: acc6b520-7ff6-4719-b1ce-762e4abf339a
-- Calendar ID: 12983871
INSERT INTO doctor_profiles (
    id,
    user_id,
    first_name,
    last_name,
    full_name,
    phone_number,
    phone_country_code,
    specialty,
    acuity_owner_id,
    onboarding_completed,
    is_new_user,
    created_at,
    updated_at
) VALUES (
    'acc6b520-7ff6-4719-b1ce-762e4abf339a'::uuid,
    'acc6b520-7ff6-4719-b1ce-762e4abf339a'::uuid,
    'Robert',
    'Taylor',
    'Dr. Robert Taylor',
    '5550106',
    '+1',
    'General Practice',
    '36512122',
    TRUE,
    FALSE,
    NOW(),
    NOW()
) ON CONFLICT (id) DO UPDATE SET
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    full_name = EXCLUDED.full_name,
    phone_number = EXCLUDED.phone_number,
    phone_country_code = EXCLUDED.phone_country_code,
    specialty = EXCLUDED.specialty,
    acuity_owner_id = EXCLUDED.acuity_owner_id,
    updated_at = NOW();

-- ============================================================================
-- Step 7: Insert Acuity Calendars (one per doctor)
-- ============================================================================

-- Calendar for Doctor 1 - Dr. Sarah Johnson - Cardiology
INSERT INTO doctor_acuity_calendars (calendar_id, doctor_id, created_at, updated_at)
VALUES ('12526411', '7a69a0da-95e0-457c-be8b-b2a4f4d52142'::uuid, NOW(), NOW())
ON CONFLICT (calendar_id) DO UPDATE SET
    doctor_id = EXCLUDED.doctor_id,
    updated_at = NOW();

-- Calendar for Doctor 2 - Dr. Michael Chen - Dermatology
INSERT INTO doctor_acuity_calendars (calendar_id, doctor_id, created_at, updated_at)
VALUES ('12967393', '89dd4d34-2dda-49ae-a68a-8931ab662fc1'::uuid, NOW(), NOW())
ON CONFLICT (calendar_id) DO UPDATE SET
    doctor_id = EXCLUDED.doctor_id,
    updated_at = NOW();

-- Calendar for Doctor 3 - Dr. Emily Rodriguez - Pediatrics
INSERT INTO doctor_acuity_calendars (calendar_id, doctor_id, created_at, updated_at)
VALUES ('12983864', '973ab625-08d0-4f15-aae7-6dbdad0c1233'::uuid, NOW(), NOW())
ON CONFLICT (calendar_id) DO UPDATE SET
    doctor_id = EXCLUDED.doctor_id,
    updated_at = NOW();

-- Calendar for Doctor 4 - Dr. James Wilson - Orthopedic Surgery
INSERT INTO doctor_acuity_calendars (calendar_id, doctor_id, created_at, updated_at)
VALUES ('12983866', '9816f018-9f17-40fe-9389-09cc835d3c97'::uuid, NOW(), NOW())
ON CONFLICT (calendar_id) DO UPDATE SET
    doctor_id = EXCLUDED.doctor_id,
    updated_at = NOW();

-- Calendar for Doctor 5 - Dr. Lisa Anderson - Psychiatry
INSERT INTO doctor_acuity_calendars (calendar_id, doctor_id, created_at, updated_at)
VALUES ('12983868', '9e7500be-7a02-40aa-b991-62f740e1e4fe'::uuid, NOW(), NOW())
ON CONFLICT (calendar_id) DO UPDATE SET
    doctor_id = EXCLUDED.doctor_id,
    updated_at = NOW();

-- Calendar for Doctor 6 - Dr. Robert Taylor - General Practice
INSERT INTO doctor_acuity_calendars (calendar_id, doctor_id, created_at, updated_at)
VALUES ('12983871', 'acc6b520-7ff6-4719-b1ce-762e4abf339a'::uuid, NOW(), NOW())
ON CONFLICT (calendar_id) DO UPDATE SET
    doctor_id = EXCLUDED.doctor_id,
    updated_at = NOW();

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Verify tables were created
SELECT 
    table_name,
    table_type
FROM information_schema.tables
WHERE table_schema = 'public'
    AND table_name IN ('doctor_profiles', 'doctor_acuity_calendars')
ORDER BY table_name;

-- Verify indexes were created
SELECT 
    indexname,
    tablename
FROM pg_indexes
WHERE schemaname = 'public'
    AND tablename IN ('doctor_profiles', 'doctor_acuity_calendars')
ORDER BY tablename, indexname;

-- Verify all doctor profiles were inserted
SELECT 
    id,
    user_id,
    first_name,
    last_name,
    full_name,
    specialty,
    acuity_owner_id
FROM doctor_profiles
ORDER BY full_name;

-- Verify all calendars were inserted
SELECT 
    dac.id,
    dac.calendar_id,
    dac.doctor_id,
    dp.full_name as doctor_name,
    dp.specialty,
    dac.created_at
FROM doctor_acuity_calendars dac
LEFT JOIN doctor_profiles dp ON dac.doctor_id = dp.id
ORDER BY dp.full_name;

