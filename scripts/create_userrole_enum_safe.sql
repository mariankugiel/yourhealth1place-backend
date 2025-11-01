-- Safe PostgreSQL script to create UserRole enum
-- This script checks if the enum exists before creating it
-- Run this script in your PostgreSQL database

-- Check if the enum already exists
DO $$
BEGIN
    -- Create the enum only if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'userrole') THEN
        -- Create the UserRole enum type
        CREATE TYPE userrole AS ENUM ('PATIENT', 'DOCTOR', 'ADMIN');
        
        -- Add a comment to document the enum
        COMMENT ON TYPE userrole IS 'User roles for the application: PATIENT (default), DOCTOR (medical professional), ADMIN (system administrator)';
        
        RAISE NOTICE 'UserRole enum created successfully';
    ELSE
        RAISE NOTICE 'UserRole enum already exists, skipping creation';
    END IF;
END $$;

-- Verify the enum exists and show its values
SELECT 
    typname AS enum_name,
    array_agg(enumlabel ORDER BY enumsortorder) AS enum_values
FROM pg_type 
JOIN pg_enum ON pg_type.oid = pg_enum.enumtypid 
WHERE typname = 'userrole'
GROUP BY typname;

-- Show all enum values with their sort order
SELECT 
    enumlabel AS role_value,
    enumsortorder AS sort_order
FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userrole')
ORDER BY enumsortorder;
