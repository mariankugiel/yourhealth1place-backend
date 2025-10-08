-- Migration to fix template linking issues
-- 1. Add metric_tmp_id to health_record_metrics table
-- 2. Update existing user-defined sections to have correct section_template_id

-- Add metric_tmp_id column to health_record_metrics table
ALTER TABLE health_record_metrics 
ADD COLUMN metric_tmp_id INTEGER REFERENCES health_record_metrics_tmp(id);

-- Create index for better performance
CREATE INDEX idx_health_record_metrics_metric_tmp_id ON health_record_metrics(metric_tmp_id);

-- Update existing user-defined sections to link to their templates
-- This fixes sections that were created without section_template_id
UPDATE health_record_sections 
SET section_template_id = (
    SELECT hrst.id 
    FROM health_record_sections_tmp hrst 
    WHERE hrst.name = health_record_sections.name 
    AND hrst.health_record_type_id = health_record_sections.health_record_type_id
    AND hrst.created_by = health_record_sections.created_by
    AND hrst.is_default = false
)
WHERE health_record_sections.is_default = false 
AND health_record_sections.section_template_id IS NULL;

-- Update existing user-defined metrics to link to their templates
-- This links metrics to their corresponding template metrics
UPDATE health_record_metrics 
SET metric_tmp_id = (
    SELECT hrmt.id 
    FROM health_record_metrics_tmp hrmt
    JOIN health_record_sections hrs ON hrs.id = health_record_metrics.section_id
    JOIN health_record_sections_tmp hrst ON hrst.id = hrmt.section_template_id
    WHERE hrmt.name = health_record_metrics.name
    AND hrst.name = hrs.name
    AND hrst.health_record_type_id = hrs.health_record_type_id
    AND hrmt.created_by = health_record_metrics.created_by
    AND hrmt.is_default = false
    AND health_record_metrics.is_default = false
)
WHERE health_record_metrics.is_default = false 
AND health_record_metrics.metric_tmp_id IS NULL;

-- Add comments for documentation
COMMENT ON COLUMN health_record_metrics.metric_tmp_id IS 'Links to corresponding template metric in health_record_metrics_tmp table';
