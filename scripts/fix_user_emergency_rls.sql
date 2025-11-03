-- Fix RLS policies for user_emergency table to allow service role access
-- Run this script in your Supabase SQL editor

-- Drop existing policies
DROP POLICY IF EXISTS "Users can view their own emergency data" ON user_emergency;
DROP POLICY IF EXISTS "Users can insert their own emergency data" ON user_emergency;
DROP POLICY IF EXISTS "Users can update their own emergency data" ON user_emergency;
DROP POLICY IF EXISTS "Users can delete their own emergency data" ON user_emergency;

-- Create new policies that allow service role (authenticated with service_role key) to bypass RLS
-- Service role key automatically bypasses RLS, but we still need policies for user access

-- Create policy: Users can view their own emergency data
CREATE POLICY "Users can view their own emergency data"
    ON user_emergency FOR SELECT
    USING (auth.uid() = user_id);

-- Create policy: Users can insert their own emergency data
CREATE POLICY "Users can insert their own emergency data"
    ON user_emergency FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Create policy: Users can update their own emergency data
CREATE POLICY "Users can update their own emergency data"
    ON user_emergency FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Create policy: Users can delete their own emergency data
CREATE POLICY "Users can delete their own emergency data"
    ON user_emergency FOR DELETE
    USING (auth.uid() = user_id);

-- Note: Service role key automatically bypasses RLS, so backend operations will work
-- These policies are for when using the anon key

