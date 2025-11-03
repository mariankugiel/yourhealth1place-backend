# User Emergency Table Migration

This migration creates the `user_emergency` table in Supabase to store emergency contact information and medical data.

## How to Run

1. Open your **Supabase Dashboard**
2. Go to **SQL Editor**
3. Copy the contents of `create_user_emergency_table.sql`
4. Paste and **Run** the query

## Table Structure

The `user_emergency` table includes:
- `id`: UUID primary key
- `user_id`: Foreign key to auth.users (cascades on delete)
- `contacts`: JSONB array of emergency contacts
- `allergies`: Text field for allergies
- `health_problems`: Text field for health problems
- `pregnancy_status`: Text field for pregnancy status
- `organ_donor`: Boolean flag for organ donor status
- `created_at`: Timestamp for creation
- `updated_at`: Timestamp for last update

## Security

- Row Level Security (RLS) is enabled
- Users can only view, insert, update, and delete their own emergency data
- Policies use `auth.uid()` to ensure data isolation

## Verification

After running the migration, verify it worked by running:

```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'user_emergency' 
ORDER BY ordinal_position;
```

You should see all 10 columns.

