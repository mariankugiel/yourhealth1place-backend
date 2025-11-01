-- PostgreSQL script to drop UserRole enum
-- WARNING: This will remove the enum and any columns using it
-- Only run this if you need to recreate the enum

-- Check if any columns are using the enum
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns 
WHERE udt_name = 'userrole';

-- If the above query returns any results, you may need to:
-- 1. Drop or alter the columns using the enum first
-- 2. Then drop the enum

-- Drop the enum (uncomment the line below if you're sure)
-- DROP TYPE IF EXISTS userrole;

-- Verify the enum was dropped
SELECT typname FROM pg_type WHERE typname = 'userrole';
