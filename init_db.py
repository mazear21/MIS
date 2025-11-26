"""
Script to initialize the database tables
Run this once to set up the database
"""
import psycopg2
from werkzeug.security import generate_password_hash

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'mis_system',
    'user': 'postgres',
    'password': '0998'
}

# SQL Schema
SCHEMA = """
-- Drop tables if they exist (for fresh setup)
DROP TABLE IF EXISTS homework CASCADE;
DROP TABLE IF EXISTS weekly_topics CASCADE;
DROP TABLE IF EXISTS grades CASCADE;
DROP TABLE IF EXISTS attendance CASCADE;
DROP TABLE IF EXISTS timetable CASCADE;
DROP TABLE IF EXISTS subjects CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS teachers CASCADE;
DROP TABLE IF EXISTS classes CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 1. USERS TABLE
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'teacher', 'student')),
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. CLASSES TABLE (Semesters)
CREATE TABLE classes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    year INTEGER CHECK (year IN (1, 2)),
    semester INTEGER CHECK (semester IN (1, 2, 3, 4)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. TEACHERS TABLE
CREATE TABLE teachers (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    department VARCHAR(100),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. STUDENTS TABLE
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    class_id INTEGER REFERENCES classes(id) ON DELETE SET NULL,
    student_number VARCHAR(50) UNIQUE,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. SUBJECTS TABLE
CREATE TABLE subjects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE,
    teacher_id INTEGER REFERENCES teachers(id) ON DELETE SET NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. ATTENDANCE TABLE
CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    teacher_id INTEGER REFERENCES teachers(id) ON DELETE SET NULL,
    date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('present', 'absent', 'late', 'excused')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, subject_id, date)
);

-- 7. GRADES TABLE
CREATE TABLE grades (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    teacher_id INTEGER REFERENCES teachers(id) ON DELETE SET NULL,
    grade_type VARCHAR(50) NOT NULL CHECK (grade_type IN ('quiz', 'exam', 'homework', 'midterm', 'final', 'project')),
    title VARCHAR(100),
    score DECIMAL(5,2) NOT NULL,
    max_score DECIMAL(5,2) DEFAULT 100,
    date DATE NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. WEEKLY TOPICS TABLE
CREATE TABLE weekly_topics (
    id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    teacher_id INTEGER REFERENCES teachers(id) ON DELETE SET NULL,
    week_number INTEGER NOT NULL,
    topic VARCHAR(255) NOT NULL,
    description TEXT,
    date_covered DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(class_id, subject_id, week_number)
);

-- 9. HOMEWORK TABLE
CREATE TABLE homework (
    id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    teacher_id INTEGER REFERENCES teachers(id) ON DELETE SET NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    due_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 10. TIMETABLE TABLE
CREATE TABLE timetable (
    id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    teacher_id INTEGER REFERENCES teachers(id) ON DELETE SET NULL,
    day_of_week VARCHAR(20) NOT NULL CHECK (day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    room VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. LECTURE FILES TABLE
CREATE TABLE lecture_files (
    id SERIAL PRIMARY KEY,
    subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    file_type VARCHAR(50),
    week_number INTEGER,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- INDEXES
CREATE INDEX idx_attendance_student ON attendance(student_id);
CREATE INDEX idx_attendance_date ON attendance(date);
CREATE INDEX idx_grades_student ON grades(student_id);
CREATE INDEX idx_grades_subject ON grades(subject_id);
CREATE INDEX idx_students_class ON students(class_id);
CREATE INDEX idx_subjects_class ON subjects(class_id);
"""

# MIS Program Structure: 4 Semesters
SEMESTERS = [
    ('Year 1 - Semester 1', 'MIS First Year, First Semester', 1, 1),
    ('Year 1 - Semester 2', 'MIS First Year, Second Semester', 1, 2),
    ('Year 2 - Semester 3', 'MIS Second Year, Third Semester', 2, 3),
    ('Year 2 - Semester 4', 'MIS Second Year, Fourth Semester', 2, 4),
]

def init_database():
    """Initialize the database with schema and default admin"""
    print("🔄 Connecting to database...")
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        print("✅ Connected to database!")
        print("🔄 Creating tables...")
        
        # Execute schema
        cursor.execute(SCHEMA)
        conn.commit()
        
        print("✅ Tables created successfully!")
        
        # Create default admin user
        print("🔄 Creating default admin user...")
        password_hash = generate_password_hash('admin123')
        
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, role, email)
            VALUES (%s, %s, %s, %s, %s)
        """, ('admin', password_hash, 'System Administrator', 'admin', 'admin@mis.edu'))
        
        conn.commit()
        print("✅ Default admin created!")
        
        # Create 4 semesters
        print("🔄 Creating 4 semesters...")
        for name, description, year, semester in SEMESTERS:
            cursor.execute("""
                INSERT INTO classes (name, description, year, semester)
                VALUES (%s, %s, %s, %s)
            """, (name, description, year, semester))
        
        conn.commit()
        print("✅ 4 Semesters created!")
        
        print("")
        print("=" * 50)
        print("🎉 DATABASE INITIALIZED SUCCESSFULLY!")
        print("=" * 50)
        print("")
        print("MIS Program Structure:")
        print("  📚 Year 1 - Semester 1")
        print("  📚 Year 1 - Semester 2")
        print("  📚 Year 2 - Semester 3")
        print("  📚 Year 2 - Semester 4")
        print("")
        print("Default Admin Credentials:")
        print("  Username: admin")
        print("  Password: admin123")
        print("")
        print("Now run: python app.py")
        print("=" * 50)
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    init_database()
