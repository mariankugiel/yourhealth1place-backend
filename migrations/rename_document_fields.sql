-- Migration: Rename document_type to lab_doc_type and source to general_doc_type
-- Date: 2025-01-05

-- Step 1: Add new columns
ALTER TABLE health_record_doc_lab 
ADD COLUMN lab_doc_type VARCHAR(100),
ADD COLUMN general_doc_type VARCHAR(50);

-- Step 2: Migrate existing data
-- For document_type -> lab_doc_type (keep existing values)
UPDATE health_record_doc_lab 
SET lab_doc_type = document_type 
WHERE document_type IS NOT NULL;

-- For source -> general_doc_type (map to GeneralDocumentType enum values)
UPDATE health_record_doc_lab 
SET general_doc_type = CASE 
    WHEN source = 'lab_document_upload' THEN 'lab_result'
    WHEN source = 'lab_result' THEN 'lab_result'
    ELSE 'lab_result'  -- Default fallback
END
WHERE source IS NOT NULL;

-- Step 3: Make new columns NOT NULL after data migration
ALTER TABLE health_record_doc_lab 
ALTER COLUMN lab_doc_type SET NOT NULL,
ALTER COLUMN general_doc_type SET NOT NULL;

-- Step 4: Drop old columns
ALTER TABLE health_record_doc_lab 
DROP COLUMN document_type,
DROP COLUMN source;

-- Step 5: Add indexes for better performance
CREATE INDEX idx_health_record_doc_lab_lab_doc_type ON health_record_doc_lab(lab_doc_type);
CREATE INDEX idx_health_record_doc_lab_general_doc_type ON health_record_doc_lab(general_doc_type);

-- Verify the migration
SELECT 
    column_name, 
    data_type, 
    is_nullable 
FROM information_schema.columns 
WHERE table_name = 'health_record_doc_lab' 
ORDER BY ordinal_position;
