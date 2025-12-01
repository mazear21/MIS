-- =============================================
-- MIGRATION: Update classes table structure
-- Run this SQL in pgAdmin to update your existing database
-- =============================================

-- Step 1: Add new columns to classes table
ALTER TABLE classes 
ADD COLUMN IF NOT EXISTS year INTEGER,
ADD COLUMN IF NOT EXISTS semester INTEGER,
ADD COLUMN IF NOT EXISTS section VARCHAR(1),
ADD COLUMN IF NOT EXISTS shift VARCHAR(10),
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true;

-- Step 2: Add constraints (run these one by one if you get errors)
-- Note: If you have existing data that doesn't match, you'll need to update it first

-- Add check constraint for year
ALTER TABLE classes 
ADD CONSTRAINT check_year CHECK (year IN (1, 2));

-- Add check constraint for semester
ALTER TABLE classes 
ADD CONSTRAINT check_semester CHECK (semester IN (1, 2, 3, 4));

-- Add check constraint for section
ALTER TABLE classes 
ADD CONSTRAINT check_section CHECK (section IN ('A', 'B', 'C'));

-- Add check constraint for shift
ALTER TABLE classes 
ADD CONSTRAINT check_shift CHECK (shift IN ('morning', 'night'));

-- Add unique constraint for the combination
ALTER TABLE classes 
ADD CONSTRAINT unique_class_combo UNIQUE (year, semester, section, shift);

-- =============================================
-- OPTIONAL: Delete existing classes and start fresh
-- WARNING: This will delete ALL existing class data!
-- Uncomment the lines below only if you want to start fresh
-- =============================================

-- DELETE FROM homework;
-- DELETE FROM weekly_topics;
-- DELETE FROM grades;
-- DELETE FROM attendance;
-- DELETE FROM subjects;
-- DELETE FROM students;
-- DELETE FROM classes;

-- =============================================
-- OPTIONAL: Insert sample classes
-- Uncomment to create all possible classes for current semesters
-- =============================================

-- Year 1 - Semester 1 (Active when Year 1 students start)
-- INSERT INTO classes (name, year, semester, section, shift, description, is_active) VALUES
-- ('Year 1 - Sem 1 - Section A - Morning', 1, 1, 'A', 'morning', 'Year 1 Semester 1 Section A Morning Shift', true),
-- ('Year 1 - Sem 1 - Section A - Night', 1, 1, 'A', 'night', 'Year 1 Semester 1 Section A Night Shift', true),
-- ('Year 1 - Sem 1 - Section B - Morning', 1, 1, 'B', 'morning', 'Year 1 Semester 1 Section B Morning Shift', true),
-- ('Year 1 - Sem 1 - Section B - Night', 1, 1, 'B', 'night', 'Year 1 Semester 1 Section B Night Shift', true),
-- ('Year 1 - Sem 1 - Section C - Morning', 1, 1, 'C', 'morning', 'Year 1 Semester 1 Section C Morning Shift', true),
-- ('Year 1 - Sem 1 - Section C - Night', 1, 1, 'C', 'night', 'Year 1 Semester 1 Section C Night Shift', true);

-- Year 2 - Semester 3 (Runs at the same time as Year 1 Sem 1)
-- INSERT INTO classes (name, year, semester, section, shift, description, is_active) VALUES
-- ('Year 2 - Sem 3 - Section A - Morning', 2, 3, 'A', 'morning', 'Year 2 Semester 3 Section A Morning Shift', true),
-- ('Year 2 - Sem 3 - Section A - Night', 2, 3, 'A', 'night', 'Year 2 Semester 3 Section A Night Shift', true),
-- ('Year 2 - Sem 3 - Section B - Morning', 2, 3, 'B', 'morning', 'Year 2 Semester 3 Section B Morning Shift', true),
-- ('Year 2 - Sem 3 - Section B - Night', 2, 3, 'B', 'night', 'Year 2 Semester 3 Section B Night Shift', true),
-- ('Year 2 - Sem 3 - Section C - Morning', 2, 3, 'C', 'morning', 'Year 2 Semester 3 Section C Morning Shift', true),
-- ('Year 2 - Sem 3 - Section C - Night', 2, 3, 'C', 'night', 'Year 2 Semester 3 Section C Night Shift', true);
