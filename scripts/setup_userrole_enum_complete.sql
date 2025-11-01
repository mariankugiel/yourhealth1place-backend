-- Complete PostgreSQL script to set up UserRole enum and related functionality
-- This script creates the enum and shows how to use it

-- Step 1: Create the UserRole enum (safe version)
DO $$
BEGIN
    -- Create the enum only if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
        CREATE TYPE userrole AS ENUM ('PATIENT', 'DOCTOR', 'ADMIN');
        RAISE NOTICE 'UserRole enum created successfully';
    ELSE
        RAISE NOTICE 'UserRole enum already exists';
    END IF;
END $$;

-- Step 2: Add comment to document the enum
COMMENT ON TYPE userrole IS 'User roles for the application: PATIENT (default), DOCTOR (medical professional), ADMIN (system administrator)';

-- Step 3: Verify the enum was created correctly
SELECT 
    'UserRole enum values:' AS info,
    array_agg(enumlabel ORDER BY enumsortorder) AS values
FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userrole');

-- Step 4: Show detailed enum information
SELECT 
    enumlabel AS role_value,
    enumsortorder AS sort_order,
    CASE 
        WHEN enumlabel = 'PATIENT' THEN 'Default user role'
        WHEN enumlabel = 'DOCTOR' THEN 'Medical professional'
        WHEN enumlabel = 'ADMIN' THEN 'System administrator'
    END AS description
FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userrole')
ORDER BY enumsortorder;

-- Step 5: Test the enum values
SELECT 
    'Testing enum values:' AS test_info,
    'PATIENT'::userrole AS patient_role,
    'DOCTOR'::userrole AS doctor_role,
    'ADMIN'::userrole AS admin_role;

-- Step 6: Show usage examples
SELECT 
    'Usage Examples:' AS examples,
    'ALTER TABLE users ADD COLUMN role userrole DEFAULT ''PATIENT'';' AS add_column_example,
    'INSERT INTO users (role) VALUES (''DOCTOR'');' AS insert_example,
    'SELECT * FROM users WHERE role = ''ADMIN'';' AS select_example;
