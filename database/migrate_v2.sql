-- =============================================
-- MIS INSTITUTE - NEW ACADEMIC STRUCTURE
-- Migration Script
-- =============================================

-- =============================================
-- NEW STRUCTURE EXPLANATION:
-- 
-- STUDENTS: Assigned Year + Shift first, Section later
--   - year (1 or 2)
--   - shift (morning/night)  
--   - section (A/B/C) - can be NULL initially
--
-- SUBJECTS: Defined per Semester (not per class)
--   - Each semester has 5 subjects
--   - Same subject taught across all sections
--
-- TEACHERS: Assigned to teach Subject for Year+Shift
--   - Can teach same subject to multiple sections
--   - Easy switching between sections
--
-- SECTIONS: Virtual groupings within Year+Shift
--   - Students grouped into A, B, C
--   - Teacher sees all their sections
-- =============================================

-- 1. Add year and shift columns to students (if not exists)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'students' AND column_name = 'year') THEN
        ALTER TABLE students ADD COLUMN year INTEGER CHECK (year IN (1, 2));
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'students' AND column_name = 'shift') THEN
        ALTER TABLE students ADD COLUMN shift VARCHAR(10) CHECK (shift IN ('morning', 'night'));
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'students' AND column_name = 'section') THEN
        ALTER TABLE students ADD COLUMN section VARCHAR(1) CHECK (section IN ('A', 'B', 'C'));
    END IF;
END $$;

-- 2. Create a new subject structure table (subjects per semester, not per class)
-- This allows same subject to be taught across all sections
CREATE TABLE IF NOT EXISTS semester_subjects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL CHECK (year IN (1, 2)),
    semester INTEGER NOT NULL CHECK (semester IN (1, 2, 3, 4)),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name, year, semester)
);

-- 3. Teacher assignments - which teacher teaches which subject for which year/shift
CREATE TABLE IF NOT EXISTS teacher_assignments (
    id SERIAL PRIMARY KEY,
    teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES semester_subjects(id) ON DELETE CASCADE,
    shift VARCHAR(10) NOT NULL CHECK (shift IN ('morning', 'night')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(teacher_id, subject_id, shift)
);

-- 4. Update existing students with year/shift from their class
UPDATE students s
SET 
    year = c.year,
    shift = c.shift,
    section = c.section
FROM classes c
WHERE s.class_id = c.id AND s.year IS NULL;

-- 5. Insert standard subjects for each semester
-- Year 1 - Semester 1
INSERT INTO semester_subjects (name, year, semester, description) VALUES
('Introduction to Programming', 1, 1, 'Learn basics of programming with Python'),
('Computer Fundamentals', 1, 1, 'Basic computer concepts and hardware'),
('Mathematics for IT', 1, 1, 'Discrete math and statistics'),
('English Communication', 1, 1, 'Technical English skills'),
('Introduction to MIS', 1, 1, 'Overview of Management Information Systems')
ON CONFLICT (name, year, semester) DO NOTHING;

-- Year 1 - Semester 2
INSERT INTO semester_subjects (name, year, semester, description) VALUES
('Object-Oriented Programming', 1, 2, 'OOP concepts with Java/Python'),
('Database Fundamentals', 1, 2, 'Introduction to databases'),
('Web Technologies', 1, 2, 'HTML, CSS basics'),
('Business Communication', 1, 2, 'Professional communication skills'),
('Statistics for Business', 1, 2, 'Business statistics and analysis')
ON CONFLICT (name, year, semester) DO NOTHING;

-- Year 2 - Semester 3
INSERT INTO semester_subjects (name, year, semester, description) VALUES
('Database Management', 2, 3, 'SQL and database design'),
('Web Development', 2, 3, 'Full-stack web development'),
('System Analysis', 2, 3, 'Business requirements and system design'),
('Network Fundamentals', 2, 3, 'Networking basics and protocols'),
('Project Management', 2, 3, 'IT project planning and execution')
ON CONFLICT (name, year, semester) DO NOTHING;

-- Year 2 - Semester 4
INSERT INTO semester_subjects (name, year, semester, description) VALUES
('Advanced Database Systems', 2, 4, 'Advanced SQL and NoSQL'),
('Software Engineering', 2, 4, 'Software development lifecycle'),
('Information Security', 2, 4, 'Security fundamentals'),
('E-Commerce Systems', 2, 4, 'Online business systems'),
('Graduation Project', 2, 4, 'Final year project')
ON CONFLICT (name, year, semester) DO NOTHING;

-- Show results
SELECT 'Migration completed!' as status;
SELECT 'Semester Subjects:' as info, COUNT(*) as count FROM semester_subjects;
