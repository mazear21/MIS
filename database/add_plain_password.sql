-- Add plain_password column to users table
-- This allows admins to view and manage user passwords
ALTER TABLE users ADD COLUMN IF NOT EXISTS plain_password VARCHAR(255);

-- Update existing users to have a default plain password (change these as needed)
UPDATE users SET plain_password = 'admin123' WHERE username = 'admin' AND plain_password IS NULL;
UPDATE users SET plain_password = 'password123' WHERE role = 'teacher' AND plain_password IS NULL;
UPDATE users SET plain_password = 'password123' WHERE role = 'student' AND plain_password IS NULL;
