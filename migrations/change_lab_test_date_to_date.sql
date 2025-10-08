-- Migration: Change lab_test_date column from DateTime to Date
-- Date: 2025-01-05

-- Step 1: Add new date column
ALTER TABLE health_record_doc_lab 
ADD COLUMN lab_test_date_new DATE;

-- Step 2: Migrate existing data (extract date part from datetime)
UPDATE health_record_doc_lab 
SET lab_test_date_new = lab_test_date::date 
WHERE lab_test_date IS NOT NULL;

-- Step 3: Drop old column
ALTER TABLE health_record_doc_lab 
DROP COLUMN lab_test_date;

-- Step 4: Rename new column to original name
ALTER TABLE health_record_doc_lab 
RENAME COLUMN lab_test_date_new TO lab_test_date;

-- Step 5: Add index for better performance
CREATE INDEX idx_health_record_doc_lab_lab_test_date ON health_record_doc_lab(lab_test_date);

-- Verify the migration
SELECT 
    column_name, 
    data_type, 
    is_nullable 
FROM information_schema.columns 
WHERE table_name = 'health_record_doc_lab' 
AND column_name = 'lab_test_date';
