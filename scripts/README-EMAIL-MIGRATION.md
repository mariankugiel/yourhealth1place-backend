# Email Migration for User Profiles

This migration script populates the `email` field in the `user_profiles` table from `auth.users` and sets up automatic synchronization.

## What it does:

1. **Adds email column** to `user_profiles` if it doesn't exist
2. **Populates existing emails** from `auth.users` for all existing users
3. **Creates triggers** to automatically sync email when:
   - New users sign up
   - Users update their email address

## How to run:

### First, verify your schema:

Run this query to check if your table uses `id` or `user_id`:

```sql
SELECT column_name 
FROM information_schema.columns 
WHERE table_name = 'user_profiles' 
  AND column_name IN ('id', 'user_id');
```

**If you see `id`** → Your table uses `id UUID` as the primary key (matches `auth.users.id`)  
**If you see `user_id`** → Your table uses `user_id UUID` as a foreign key

### Then run the migration:

1. Open your **Supabase Dashboard**
2. Go to **SQL Editor**
3. Copy the contents of the appropriate migration file:
   - **If you have `id` column**: Use `populate_user_profile_email.sql`
   - **If you have `user_id` column**: Use `populate_user_profile_email-user_id.sql`
4. Paste and **Run** the query

## Verification:

After running the migration, verify it worked by running this query:

**If your table uses `id`**:
```sql
SELECT id, email, full_name 
FROM user_profiles 
WHERE email IS NOT NULL 
LIMIT 10;
```

**If your table uses `user_id`**:
```sql
SELECT user_id, email, full_name 
FROM user_profiles 
WHERE email IS NOT NULL 
LIMIT 10;
```

You should see emails populated for your existing users.

## Troubleshooting:

### Issue: "relation user_profiles does not exist"
- Make sure your table is named `user_profiles`

### Issue: "column X does not exist"
- Run the schema verification query first to check if you have `id` or `user_id`
- Use the correct migration file for your schema

### Issue: "duplicate key value violates unique constraint"
- You may have duplicate user_profiles. Check with:

**If your table uses `id`**:
```sql
SELECT id, COUNT(*) 
FROM user_profiles 
GROUP BY id 
HAVING COUNT(*) > 1;
```

**If your table uses `user_id`**:
```sql
SELECT user_id, COUNT(*) 
FROM user_profiles 
GROUP BY user_id 
HAVING COUNT(*) > 1;
```

### Issue: Triggers not working
- Check if triggers are enabled:
```sql
SELECT * FROM pg_trigger WHERE tgname LIKE '%email%';
```

