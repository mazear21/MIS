"""
Migration script for new academic structure
Run this to update the database
"""
import pg8000
from config import config

def main():
    conn = pg8000.connect(
        host=config.DB_HOST,
        port=int(config.DB_PORT),
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD
    )
    cur = conn.cursor()

    # 1. Add columns to students
    print('1. Adding columns to students table...')
    for col, sql in [
        ('year', "ALTER TABLE students ADD COLUMN year INTEGER CHECK (year IN (1, 2))"),
        ('shift', "ALTER TABLE students ADD COLUMN shift VARCHAR(10) CHECK (shift IN ('morning', 'night'))"),
        ('section', "ALTER TABLE students ADD COLUMN section VARCHAR(1) CHECK (section IN ('A', 'B', 'C'))")
    ]:
        try:
            cur.execute(sql)
            conn.commit()
            print(f'   + Added {col} column')
        except Exception as e:
            conn.rollback()
            print(f'   - {col} column exists')

    # 2. Create semester_subjects table
    print('\n2. Creating semester_subjects table...')
    try:
        cur.execute('''
            CREATE TABLE semester_subjects (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                year INTEGER NOT NULL CHECK (year IN (1, 2)),
                semester INTEGER NOT NULL CHECK (semester IN (1, 2, 3, 4)),
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(name, year, semester)
            )
        ''')
        conn.commit()
        print('   + Created semester_subjects table')
    except:
        conn.rollback()
        print('   - semester_subjects exists')

    # 3. Create teacher_assignments table
    print('\n3. Creating teacher_assignments table...')
    try:
        cur.execute('''
            CREATE TABLE teacher_assignments (
                id SERIAL PRIMARY KEY,
                teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
                subject_id INTEGER NOT NULL REFERENCES semester_subjects(id) ON DELETE CASCADE,
                shift VARCHAR(10) NOT NULL CHECK (shift IN ('morning', 'night')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(teacher_id, subject_id, shift)
            )
        ''')
        conn.commit()
        print('   + Created teacher_assignments table')
    except:
        conn.rollback()
        print('   - teacher_assignments exists')

    # 4. Update students with year/shift from their class
    print('\n4. Updating students with year/shift from class...')
    cur.execute('''
        UPDATE students s
        SET year = c.year, shift = c.shift, section = c.section
        FROM classes c
        WHERE s.class_id = c.id AND s.year IS NULL
    ''')
    conn.commit()
    print(f'   Updated {cur.rowcount} students')

    # 5. Insert semester subjects
    print('\n5. Inserting semester subjects...')
    subjects = [
        # Year 1 - Semester 1
        ('Introduction to Programming', 1, 1, 'Learn basics of programming'),
        ('Computer Fundamentals', 1, 1, 'Basic computer concepts'),
        ('Mathematics for IT', 1, 1, 'Discrete math and statistics'),
        ('English Communication', 1, 1, 'Technical English skills'),
        ('Introduction to MIS', 1, 1, 'Overview of MIS'),
        # Year 1 - Semester 2
        ('Object-Oriented Programming', 1, 2, 'OOP concepts'),
        ('Database Fundamentals', 1, 2, 'Introduction to databases'),
        ('Web Technologies', 1, 2, 'HTML, CSS basics'),
        ('Business Communication', 1, 2, 'Professional communication'),
        ('Statistics for Business', 1, 2, 'Business statistics'),
        # Year 2 - Semester 3
        ('Database Management', 2, 3, 'SQL and database design'),
        ('Web Development', 2, 3, 'Full-stack web development'),
        ('System Analysis', 2, 3, 'System design'),
        ('Network Fundamentals', 2, 3, 'Networking basics'),
        ('Project Management', 2, 3, 'IT project management'),
        # Year 2 - Semester 4
        ('Advanced Database Systems', 2, 4, 'Advanced SQL and NoSQL'),
        ('Software Engineering', 2, 4, 'Software development'),
        ('Information Security', 2, 4, 'Security fundamentals'),
        ('E-Commerce Systems', 2, 4, 'Online business systems'),
        ('Graduation Project', 2, 4, 'Final year project'),
    ]
    
    inserted = 0
    for name, year, semester, desc in subjects:
        try:
            cur.execute('''
                INSERT INTO semester_subjects (name, year, semester, description)
                VALUES (%s, %s, %s, %s)
            ''', (name, year, semester, desc))
            conn.commit()
            inserted += 1
        except:
            conn.rollback()
    print(f'   Inserted {inserted} subjects (others already exist)')

    # 6. Show summary
    print('\n' + '='*50)
    print('MIGRATION SUMMARY')
    print('='*50)
    
    cur.execute('SELECT COUNT(*) FROM semester_subjects')
    print(f'Semester Subjects: {cur.fetchone()[0]}')
    
    cur.execute('''
        SELECT year, semester, COUNT(*) 
        FROM semester_subjects 
        GROUP BY year, semester 
        ORDER BY year, semester
    ''')
    for r in cur.fetchall():
        print(f'  Year {r[0]} Sem {r[1]}: {r[2]} subjects')
    
    cur.execute('''
        SELECT year, shift, section, COUNT(*) 
        FROM students 
        WHERE year IS NOT NULL 
        GROUP BY year, shift, section 
        ORDER BY year, shift, section
    ''')
    rows = cur.fetchall()
    if rows:
        print('\nStudents by Year/Shift/Class:')
        for r in rows:
            print(f'  Year {r[0]} - {r[1]} - Class {r[2]}: {r[3]} students')
    
    conn.close()
    print('\nMigration completed!')

if __name__ == '__main__':
    main()
