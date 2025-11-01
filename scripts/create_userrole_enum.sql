-- PostgreSQL script to create UserRole enum
-- Run this script in your PostgreSQL database

-- Create the UserRole enum type
CREATE TYPE userrole AS ENUM ('PATIENT', 'DOCTOR', 'ADMIN');

-- Verify the enum was created
SELECT enumlabel, enumsortorder 
FROM pg_enum 
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userrole')
ORDER BY enumsortorder;

-- Optional: Add a comment to document the enum
COMMENT ON TYPE userrole IS 'User roles for the application: PATIENT (default), DOCTOR (medical professional), ADMIN (system administrator)';

-- Verify the enum values
SELECT unnest(enum_range(NULL::userrole)) AS role_values;
