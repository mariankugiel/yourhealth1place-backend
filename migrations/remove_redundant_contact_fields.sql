-- Remove redundant contact fields from conversations table
-- These fields will be fetched from Supabase using contact_id

-- Remove the redundant columns
ALTER TABLE conversations 
DROP COLUMN IF EXISTS contact_name,
DROP COLUMN IF EXISTS contact_role,
DROP COLUMN IF EXISTS contact_avatar;

-- Keep contact_id and contact_type as they are needed for relationships
-- contact_id: Foreign key to users table
-- contact_type: Enum for sender type (user, doctor, admin, system)
