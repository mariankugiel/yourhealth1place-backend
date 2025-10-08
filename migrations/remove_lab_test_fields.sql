-- Migration: Remove lab_test_name and lab_test_type columns from health_record_doc_lab table
-- Date: 2025-01-05

-- Step 1: Drop the columns
ALTER TABLE health_record_doc_lab 
DROP COLUMN IF EXISTS lab_test_name,
DROP COLUMN IF EXISTS lab_test_type;

-- Verify the migration
SELECT 
    column_name, 
    data_type, 
    is_nullable 
FROM information_schema.columns 
WHERE table_name = 'health_record_doc_lab' 
ORDER BY ordinal_position;
