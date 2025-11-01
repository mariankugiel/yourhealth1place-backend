# Supabase User Profiles Migration Guide

## Overview
This guide helps you remove unnecessary fields from the `user_profiles` table in Supabase to clean up the schema and improve performance.

## Fields to Remove
- `cellphone` - Redundant with `phone_number`
- `cellphone_country_code` - Redundant with `phone_country_code`
- `location` - Not needed for user profiles
- `country` - Not needed for user profiles

## Fields to Add
- `avatar_url` - User profile picture URL
- `role` - User role (stored as lowercase: patient, doctor, admin)

## Migration Steps

### 1. Backup Your Data (Recommended)
Before making any changes, backup your Supabase database:
```sql
-- Export user_profiles table data
SELECT * FROM user_profiles;
```

### 2. Verify Current Structure
Run the verification script to see the current table structure:
```sql
-- Run: scripts/verify_user_profile_structure.sql
```

### 3. Remove Unnecessary Fields
Execute the cleanup script:
```sql
-- Run: scripts/remove_unnecessary_user_profile_fields.sql
```

### 4. Verify Changes
Run the verification script again to confirm the changes:
```sql
-- Run: scripts/verify_user_profile_structure.sql
```

### 5. Test Your Application
After the migration:
1. Test user registration
2. Test profile updates
3. Test profile retrieval
4. Verify that phone numbers are saved correctly with `phone_country_code`

## Expected Result

### Before Migration
```sql
user_profiles table columns:
- id, user_id, full_name, date_of_birth
- phone_number, phone_country_code
- cellphone, cellphone_country_code  -- REMOVE
- address, location, country         -- REMOVE
- emergency_contact_*
- gender, height, weight, etc.
- onboarding_*
- created_at, updated_at
```

### After Migration
```sql
user_profiles table columns:
- id, user_id, full_name, date_of_birth
- phone_number, phone_country_code    -- KEEP
- address                            -- KEEP
- avatar_url, role                   -- NEW
- emergency_contact_*
- gender, height, weight, etc.
- onboarding_*
- created_at, updated_at
```

## Rollback (If Needed)
If you need to restore the removed columns:
```sql
-- Run: scripts/rollback_user_profile_fields.sql
```

## Frontend Updates Required

### Phone Number Handling
Update your frontend to use the new schema:

```typescript
// Before
interface UserProfile {
  cellphone?: string;
  cellphone_country_code?: string;
  location?: string;
  country?: string;
}

// After
interface UserProfile {
  phone_number?: string;
  phone_country_code?: string;
  avatar_url?: string;  // NEW
  role?: string;        // NEW
  // Remove: cellphone, cellphone_country_code, location, country
}
```

### Form Updates
Update your profile forms to use:
- `phone_number` instead of `cellphone`
- `phone_country_code` instead of `cellphone_country_code`
- Add `avatar_url` field for profile pictures
- Add `role` field for user roles
- Remove `location` and `country` fields

## Backend Updates
The backend has already been updated to:
- Remove references to unnecessary fields
- Use `phone_country_code` instead of `country`
- Update Supabase client select statements
- Update user schemas
- Handle role conversion between Supabase (lowercase) and PostgreSQL enum (uppercase)

## Verification Checklist
- [ ] Run verification script before migration
- [ ] Execute cleanup script
- [ ] Run verification script after migration
- [ ] Test user registration
- [ ] Test profile updates
- [ ] Test profile retrieval
- [ ] Update frontend forms
- [ ] Test frontend integration

## Support
If you encounter any issues:
1. Check the verification script output
2. Review the rollback script if needed
3. Ensure your backend code is updated
4. Verify frontend forms are updated
