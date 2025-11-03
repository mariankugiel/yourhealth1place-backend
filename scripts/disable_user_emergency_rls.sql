-- Disable RLS on user_emergency table for development/testing
-- Run this script in your Supabase SQL editor

-- Disable RLS (this allows both service role and anon key to access without restrictions)
ALTER TABLE user_emergency DISABLE ROW LEVEL SECURITY;

-- Warning: This removes all security from the user_emergency table
-- Only use this for development/testing
-- In production, you should re-enable RLS with proper policies

