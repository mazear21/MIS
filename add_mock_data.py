"""
Add mock data to MIS database
Run this script to populate the database with sample data
"""
import pg8000
from config import config
from werkzeug.security import generate_password_hash

def main():
    conn = pg8000.connect(
        host=config.DB_HOST,
        port=int(config.DB_PORT),
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD
    )
    cursor = conn.cursor()
    
    # =============================================
    # 1. CREATE MORE CLASSES
    # =============================================
    print('Creating additional classes...')
    new_classes = [
        # Year 1 - Sem 1
        ('Year 1 - Sem 1 - Class B - Morning', 1, 1, 'B', 'morning'),
        ('Year 1 - Sem 1 - Class C - Morning', 1, 1, 'C', 'morning'),
        ('Year 1 - Sem 1 - Class A - Night', 1, 1, 'A', 'night'),
        ('Year 1 - Sem 1 - Class B - Night', 1, 1, 'B', 'night'),
        # Year 2 - Sem 3
        ('Year 2 - Sem 3 - Class B - Morning', 2, 3, 'B', 'morning'),
        ('Year 2 - Sem 3 - Class C - Morning', 2, 3, 'C', 'morning'),
        ('Year 2 - Sem 3 - Class A - Night', 2, 3, 'A', 'night'),
    ]
    
    for name, year, sem, sec, shift in new_classes:
        try:
            cursor.execute('''
                INSERT INTO classes (name, year, semester, section, shift, is_active)
                VALUES (%s, %s, %s, %s, %s, true)
            ''', (name, year, sem, sec, shift))
            conn.commit()
            print(f'  + {name}')
        except Exception as e:
            conn.rollback()
            if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
                print(f'  - {name} (exists)')
            else:
                print(f'  ! Error: {e}')
    
    # =============================================
    # 2. CREATE TEACHERS
    # =============================================
    print('\nCreating teachers...')
    teachers = [
        ('teacher1', 'Dr. Ahmed Hassan', 'ahmed@mis.edu', 'Computer Science'),
        ('teacher2', 'Dr. Sara Ali', 'sara@mis.edu', 'Information Systems'),
        ('teacher3', 'Prof. Omar Khalid', 'omar@mis.edu', 'Database Systems'),
        ('teacher4', 'Dr. Fatima Noor', 'fatima@mis.edu', 'Web Development'),
        ('teacher5', 'Mr. Karwan Aziz', 'karwan@mis.edu', 'Programming'),
    ]
    
    teacher_ids = {}
    for username, full_name, email, dept in teachers:
        try:
            # Check if exists
            cursor.execute('SELECT t.id FROM teachers t JOIN users u ON t.user_id = u.id WHERE u.username = %s', (username,))
            result = cursor.fetchone()
            if result:
                teacher_ids[username] = result[0]
                print(f'  - {full_name} (exists, ID: {result[0]})')
                continue
            
            pwd_hash = generate_password_hash('teacher123')
            cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, role, email)
                VALUES (%s, %s, %s, 'teacher', %s)
                RETURNING id
            ''', (username, pwd_hash, full_name, email))
            user_id = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT INTO teachers (user_id, department, phone)
                VALUES (%s, %s, '0750-XXX-XXXX')
                RETURNING id
            ''', (user_id, dept))
            teacher_id = cursor.fetchone()[0]
            conn.commit()
            teacher_ids[username] = teacher_id
            print(f'  + {full_name} (ID: {teacher_id})')
        except Exception as e:
            conn.rollback()
            print(f'  ! Error creating {full_name}: {e}')
    
    # =============================================
    # 3. CREATE SUBJECTS (5 per class for class 1)
    # =============================================
    print('\nCreating subjects for Year 1 - Sem 1 - Class A - Morning (class_id=1)...')
    
    # Get teacher IDs
    cursor.execute('SELECT id FROM teachers ORDER BY id LIMIT 5')
    t_ids = [row[0] for row in cursor.fetchall()]
    
    subjects_sem1 = [
        ('Introduction to Programming', 'Learn basics of programming with Python'),
        ('Computer Fundamentals', 'Basic computer concepts and hardware'),
        ('Mathematics for IT', 'Discrete math and statistics'),
        ('English Communication', 'Technical English skills'),
        ('Introduction to MIS', 'Overview of Management Information Systems'),
    ]
    
    for i, (name, desc) in enumerate(subjects_sem1):
        try:
            teacher_id = t_ids[i] if i < len(t_ids) else None
            cursor.execute('''
                INSERT INTO subjects (name, class_id, teacher_id, description)
                VALUES (%s, 1, %s, %s)
            ''', (name, teacher_id, desc))
            conn.commit()
            print(f'  + {name}')
        except Exception as e:
            conn.rollback()
            if 'duplicate' in str(e).lower():
                print(f'  - {name} (exists)')
            else:
                print(f'  ! Error: {e}')
    
    # Subjects for Year 2 - Sem 3 (class_id=3)
    print('\nCreating subjects for Year 2 - Sem 3 - Class A - Morning (class_id=3)...')
    subjects_sem3 = [
        ('Database Management', 'SQL and database design'),
        ('Web Development', 'HTML, CSS, JavaScript, Flask'),
        ('System Analysis', 'Business requirements and system design'),
        ('Network Fundamentals', 'Networking basics and protocols'),
        ('Project Management', 'IT project planning and execution'),
    ]
    
    for i, (name, desc) in enumerate(subjects_sem3):
        try:
            teacher_id = t_ids[i] if i < len(t_ids) else None
            cursor.execute('''
                INSERT INTO subjects (name, class_id, teacher_id, description)
                VALUES (%s, 3, %s, %s)
            ''', (name, teacher_id, desc))
            conn.commit()
            print(f'  + {name}')
        except Exception as e:
            conn.rollback()
            if 'duplicate' in str(e).lower():
                print(f'  - {name} (exists)')
            else:
                print(f'  ! Error: {e}')
    
    # =============================================
    # 4. CREATE STUDENTS
    # =============================================
    print('\nCreating students...')
    
    # Students for Year 1 - Sem 1 - Section A - Morning (class_id=1)
    students_class1 = [
        ('std101', 'MIS25101', 'Aram Rashid'),
        ('std102', 'MIS25102', 'Bana Hassan'),
        ('std103', 'MIS25103', 'Chnar Ahmed'),
        ('std104', 'MIS25104', 'Dilan Karim'),
        ('std105', 'MIS25105', 'Eman Saeed'),
        ('std106', 'MIS25106', 'Faris Jalal'),
        ('std107', 'MIS25107', 'Goran Mustafa'),
        ('std108', 'MIS25108', 'Hana Omer'),
    ]
    
    for username, student_num, full_name in students_class1:
        try:
            cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
            if cursor.fetchone():
                print(f'  - {full_name} (exists)')
                continue
            
            pwd_hash = generate_password_hash('student123')
            cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, role, email)
                VALUES (%s, %s, %s, 'student', %s)
                RETURNING id
            ''', (username, pwd_hash, full_name, f'{username}@student.mis.edu'))
            user_id = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT INTO students (user_id, class_id, student_number, phone)
                VALUES (%s, 1, %s, '0750-XXX-XXXX')
            ''', (user_id, student_num))
            conn.commit()
            print(f'  + {full_name} ({student_num}) -> Class 1')
        except Exception as e:
            conn.rollback()
            print(f'  ! Error: {e}')
    
    # Students for Year 2 - Sem 3 - Section A - Morning (class_id=3)
    students_class3 = [
        ('std201', 'MIS24201', 'Ibrahim Aziz'),
        ('std202', 'MIS24202', 'Jana Kareem'),
        ('std203', 'MIS24203', 'Karzan Amin'),
        ('std204', 'MIS24204', 'Lana Sharif'),
        ('std205', 'MIS24205', 'Mohammed Ali'),
        ('std206', 'MIS24206', 'Naz Hamid'),
    ]
    
    for username, student_num, full_name in students_class3:
        try:
            cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
            if cursor.fetchone():
                print(f'  - {full_name} (exists)')
                continue
            
            pwd_hash = generate_password_hash('student123')
            cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, role, email)
                VALUES (%s, %s, %s, 'student', %s)
                RETURNING id
            ''', (username, pwd_hash, full_name, f'{username}@student.mis.edu'))
            user_id = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT INTO students (user_id, class_id, student_number, phone)
                VALUES (%s, 3, %s, '0750-XXX-XXXX')
            ''', (user_id, student_num))
            conn.commit()
            print(f'  + {full_name} ({student_num}) -> Class 3')
        except Exception as e:
            conn.rollback()
            print(f'  ! Error: {e}')
    
    # =============================================
    # SUMMARY
    # =============================================
    print('\n' + '='*50)
    print('MOCK DATA SUMMARY')
    print('='*50)
    
    cursor.execute('SELECT COUNT(*) FROM classes')
    print(f'Total Classes: {cursor.fetchone()[0]}')
    
    cursor.execute('SELECT COUNT(*) FROM teachers')
    print(f'Total Teachers: {cursor.fetchone()[0]}')
    
    cursor.execute('SELECT COUNT(*) FROM students')
    print(f'Total Students: {cursor.fetchone()[0]}')
    
    cursor.execute('SELECT COUNT(*) FROM subjects')
    print(f'Total Subjects: {cursor.fetchone()[0]}')
    
    print('\n' + '='*50)
    print('LOGIN CREDENTIALS')
    print('='*50)
    print('Admin:    admin / admin123')
    print('Teachers: teacher1-5 / teacher123')
    print('Students: std101-108, std201-206 / student123')
    print('='*50)
    
    cursor.close()
    conn.close()
    print('\nDone!')

if __name__ == '__main__':
    main()
