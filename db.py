"""
Database connection and helper functions for MIS System
"""
import pg8000
import pg8000.native
from config import config


def get_db_connection():
    """
    Create and return a database connection.
    Returns rows as dictionaries using pg8000.
    """
    try:
        conn = pg8000.connect(
            host=config.DB_HOST,
            port=int(config.DB_PORT),
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None


def row_to_dict(cursor, row):
    """Convert a row to a dictionary using cursor description"""
    if row is None:
        return None
    columns = [desc[0] for desc in cursor.description]
    return dict(zip(columns, row))


def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """
    Execute a database query safely.
    
    Args:
        query: SQL query string
        params: Query parameters (tuple or dict)
        fetch_one: Return single row
        fetch_all: Return all rows
    
    Returns:
        Query result or None
    """
    conn = get_db_connection()
    if not conn:
        return [] if fetch_all else None
    
    try:
        cursor = conn.cursor()
        # pg8000 requires params to be a tuple or None
        if params is None:
            cursor.execute(query)
        else:
            cursor.execute(query, params)
        
        result = None
        if fetch_one:
            row = cursor.fetchone()
            result = row_to_dict(cursor, row)
        elif fetch_all:
            rows = cursor.fetchall()
            result = [row_to_dict(cursor, row) for row in rows] if rows else []
        else:
            conn.commit()
            result = cursor.rowcount
        
        cursor.close()
        conn.close()
        return result
    
    except Exception as e:
        print(f"Query error: {e}")
        conn.rollback()
        conn.close()
        return [] if fetch_all else None


def execute_insert_returning(query, params=None):
    """
    Execute an INSERT query and return the inserted row's ID.
    
    Args:
        query: SQL INSERT query with RETURNING clause
        params: Query parameters
    
    Returns:
        Inserted row ID or None
    """
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        result = row_to_dict(cursor, row)
        conn.commit()
        cursor.close()
        conn.close()
        return result['id'] if result else None
    
    except Exception as e:
        print(f"Insert error: {e}")
        conn.rollback()
        conn.close()
        return None


# =============================================
# SYSTEM SETTINGS
# =============================================

def get_current_cycle():
    """Get the current academic cycle (1 or 2)"""
    query = "SELECT value FROM system_settings WHERE key = 'current_cycle'"
    result = execute_query(query, fetch_one=True)
    return int(result['value']) if result else 1


def set_current_cycle(cycle):
    """Set the current academic cycle (1 or 2)"""
    query = """
        INSERT INTO system_settings (key, value, description, updated_at) 
        VALUES ('current_cycle', %s, 'Academic cycle: 1 = Sem 1+3 active, 2 = Sem 2+4 active', CURRENT_TIMESTAMP)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP
    """
    return execute_query(query, (str(cycle),))


def get_semester_for_year(year, cycle=None):
    """Get the active semester for a year based on the current cycle"""
    if cycle is None:
        cycle = get_current_cycle()
    
    if year == 1:
        return 1 if cycle == 1 else 2
    else:  # year == 2
        return 3 if cycle == 1 else 4


# =============================================
# STUDENT QUERIES (UPDATED FOR YEAR/SHIFT/SECTION)
# =============================================

def get_students_by_year_shift_section(year, shift, section):
    """Get students by year, shift, and section (the new primary way to query students)"""
    query = """
        SELECT s.*, u.full_name, u.username, u.email
        FROM students s
        JOIN users u ON s.user_id = u.id
        WHERE s.year = %s AND s.shift = %s AND s.section = %s
        ORDER BY u.full_name
    """
    return execute_query(query, (year, shift, section), fetch_all=True)


def get_students_by_semester(semester, shift, section):
    """Get students by semester, shift, and section"""
    year = 1 if semester <= 2 else 2
    query = """
        SELECT s.*, u.full_name, u.username, u.email
        FROM students s
        JOIN users u ON s.user_id = u.id
        WHERE s.semester = %s AND s.shift = %s AND s.section = %s
        ORDER BY u.full_name
    """
    return execute_query(query, (semester, shift, section), fetch_all=True)


def get_student_count_by_year_shift_section(year, shift, section):
    """Get count of students in a year/shift/section"""
    query = """
        SELECT COUNT(*) as count FROM students
        WHERE year = %s AND shift = %s AND section = %s
    """
    result = execute_query(query, (year, shift, section), fetch_one=True)
    return result['count'] if result else 0


def create_student_with_semester(user_id, year, semester, shift, section, student_number=None, phone=None):
    """Create student with semester assignment"""
    query = """
        INSERT INTO students (user_id, year, semester, shift, section, student_number, phone)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    return execute_insert_returning(query, (user_id, year, semester, shift, section, student_number, phone))


def get_student_counts_by_semester():
    """Get student counts grouped by semester, shift"""
    query = """
        SELECT semester, shift, section, COUNT(*) as count
        FROM students
        WHERE semester IS NOT NULL
        GROUP BY semester, shift, section
        ORDER BY semester, shift, section
    """
    results = execute_query(query, fetch_all=True) or []
    
    # Organize into a structured format
    stats = {1: {'morning': 0, 'night': 0, 'total': 0},
             2: {'morning': 0, 'night': 0, 'total': 0},
             3: {'morning': 0, 'night': 0, 'total': 0},
             4: {'morning': 0, 'night': 0, 'total': 0}}
    
    for r in results:
        sem = r['semester']
        shift = r['shift']
        count = r['count']
        if sem in stats and shift in stats[sem]:
            stats[sem][shift] += count
            stats[sem]['total'] += count
    
    return stats


# =============================================
# USER QUERIES
# =============================================

def get_user_by_username(username):
    """Get user by username"""
    query = "SELECT * FROM users WHERE username = %s"
    return execute_query(query, (username,), fetch_one=True)


def get_user_by_id(user_id):
    """Get user by ID"""
    query = "SELECT * FROM users WHERE id = %s"
    return execute_query(query, (user_id,), fetch_one=True)


def create_user(username, password_hash, full_name, role, email=None):
    """Create a new user"""
    query = """
        INSERT INTO users (username, password_hash, full_name, role, email)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """
    return execute_insert_returning(query, (username, password_hash, full_name, role, email))


def get_all_users():
    """Get all users"""
    query = "SELECT id, username, full_name, role, email, created_at FROM users ORDER BY id"
    return execute_query(query, fetch_all=True)


def delete_user(user_id):
    """Delete a user"""
    query = "DELETE FROM users WHERE id = %s"
    return execute_query(query, (user_id,))


def update_user(user_id, full_name, email=None):
    """Update user basic info"""
    query = "UPDATE users SET full_name = %s, email = %s WHERE id = %s"
    return execute_query(query, (full_name, email, user_id))


def update_user_password(user_id, password_hash):
    """Update user password"""
    query = "UPDATE users SET password_hash = %s WHERE id = %s"
    return execute_query(query, (password_hash, user_id))


# =============================================
# CLASS QUERIES
# =============================================

def get_all_classes():
    """Get all classes ordered by year, semester, section, shift"""
    query = """
        SELECT * FROM classes 
        ORDER BY year, semester, section, shift
    """
    return execute_query(query, fetch_all=True)


def get_class_by_id(class_id):
    """Get class by ID"""
    query = "SELECT * FROM classes WHERE id = %s"
    return execute_query(query, (class_id,), fetch_one=True)


def get_active_classes():
    """Get only active classes"""
    query = """
        SELECT * FROM classes 
        WHERE is_active = true
        ORDER BY year, semester, section, shift
    """
    return execute_query(query, fetch_all=True)


def get_classes_by_year_semester(year, semester):
    """Get classes for a specific year and semester"""
    query = """
        SELECT * FROM classes 
        WHERE year = %s AND semester = %s
        ORDER BY section, shift
    """
    return execute_query(query, (year, semester), fetch_all=True)


def create_class(name, year, semester, section, shift, description=None):
    """Create a new class with all required fields"""
    query = """
        INSERT INTO classes (name, year, semester, section, shift, description)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    return execute_insert_returning(query, (name, year, semester, section, shift, description))


def update_class(class_id, name, year, semester, section, shift, description=None, is_active=True):
    """Update a class"""
    query = """
        UPDATE classes 
        SET name = %s, year = %s, semester = %s, section = %s, shift = %s, description = %s, is_active = %s
        WHERE id = %s
    """
    return execute_query(query, (name, year, semester, section, shift, description, is_active, class_id))


def toggle_class_active(class_id, is_active):
    """Toggle class active status"""
    query = "UPDATE classes SET is_active = %s WHERE id = %s"
    return execute_query(query, (is_active, class_id))


def delete_class(class_id):
    """Delete a class"""
    query = "DELETE FROM classes WHERE id = %s"
    return execute_query(query, (class_id,))


# =============================================
# TEACHER QUERIES
# =============================================

def create_teacher(user_id, department=None, phone=None):
    """Create teacher profile"""
    query = """
        INSERT INTO teachers (user_id, department, phone)
        VALUES (%s, %s, %s)
        RETURNING id
    """
    return execute_insert_returning(query, (user_id, department, phone))


def get_teacher_by_user_id(user_id):
    """Get teacher by user ID"""
    query = """
        SELECT t.*, u.full_name, u.username, u.email
        FROM teachers t
        JOIN users u ON t.user_id = u.id
        WHERE t.user_id = %s
    """
    return execute_query(query, (user_id,), fetch_one=True)


def get_all_teachers():
    """Get all teachers with user info"""
    query = """
        SELECT t.*, u.full_name, u.username, u.email
        FROM teachers t
        JOIN users u ON t.user_id = u.id
        ORDER BY u.full_name
    """
    return execute_query(query, fetch_all=True)


def get_all_teachers_with_subjects():
    """Get all teachers with their assigned subjects"""
    query = """
        SELECT t.id as teacher_id, t.department, t.phone, u.full_name, u.username, u.email,
               COALESCE(
                   (SELECT COUNT(*) FROM subjects WHERE teacher_id = t.id), 0
               ) as subject_count
        FROM teachers t
        JOIN users u ON t.user_id = u.id
        ORDER BY u.full_name
    """
    return execute_query(query, fetch_all=True)


def get_subjects_by_teacher_id(teacher_id):
    """Get all subjects assigned to a teacher with class info"""
    query = """
        SELECT s.id, s.name, c.name as class_name, c.year, c.semester, c.section, c.shift
        FROM subjects s
        LEFT JOIN classes c ON s.class_id = c.id
        WHERE s.teacher_id = %s
        ORDER BY s.name, c.year, c.section
    """
    return execute_query(query, (teacher_id,), fetch_all=True)


# =============================================
# STUDENT QUERIES
# =============================================

def create_student(user_id, class_id=None, student_number=None, phone=None):
    """Create student profile"""
    query = """
        INSERT INTO students (user_id, class_id, student_number, phone)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """
    return execute_insert_returning(query, (user_id, class_id, student_number, phone))


def get_student_by_user_id(user_id):
    """Get student by user ID"""
    query = """
        SELECT s.*, u.full_name, u.username, u.email, c.name as class_name
        FROM students s
        JOIN users u ON s.user_id = u.id
        LEFT JOIN classes c ON s.class_id = c.id
        WHERE s.user_id = %s
    """
    return execute_query(query, (user_id,), fetch_one=True)


def get_students_by_class(class_id):
    """Get all students in a class"""
    query = """
        SELECT s.*, u.full_name, u.username, u.email
        FROM students s
        JOIN users u ON s.user_id = u.id
        WHERE s.class_id = %s
        ORDER BY u.full_name
    """
    return execute_query(query, (class_id,), fetch_all=True)


def get_all_students():
    """Get all students"""
    query = """
        SELECT s.*, u.full_name, u.username, u.email, c.name as class_name, c.year
        FROM students s
        JOIN users u ON s.user_id = u.id
        LEFT JOIN classes c ON s.class_id = c.id
        ORDER BY u.full_name
    """
    return execute_query(query, fetch_all=True)


def get_student_by_id(student_id):
    """Get student by ID with year/shift/section"""
    query = """
        SELECT s.*, u.full_name, u.username, u.email
        FROM students s
        JOIN users u ON s.user_id = u.id
        WHERE s.id = %s
    """
    return execute_query(query, (student_id,), fetch_one=True)


def update_student(student_id, full_name, email, class_id, student_number, phone):
    """Update student information"""
    query = """
        UPDATE students SET class_id = %s, student_number = %s, phone = %s
        WHERE id = %s
    """
    result = execute_query(query, (class_id, student_number, phone, student_id))
    
    # Also update user info
    student = get_student_by_id(student_id)
    if student:
        query2 = "UPDATE users SET full_name = %s, email = %s WHERE id = %s"
        execute_query(query2, (full_name, email, student['user_id']))
    
    return result


def delete_student(student_id):
    """Delete a student and their user account"""
    student = get_student_by_id(student_id)
    if student:
        # Delete student profile
        execute_query("DELETE FROM students WHERE id = %s", (student_id,))
        # Delete user account
        execute_query("DELETE FROM users WHERE id = %s", (student['user_id'],))
        return True
    return False


def get_students_filtered(year=None, class_id=None):
    """Get students filtered by year and/or class"""
    query = """
        SELECT s.*, u.full_name, u.username, u.email, c.name as class_name, c.year
        FROM students s
        JOIN users u ON s.user_id = u.id
        LEFT JOIN classes c ON s.class_id = c.id
        WHERE 1=1
    """
    params = []
    
    if year:
        query += " AND c.year = %s"
        params.append(year)
    
    if class_id:
        query += " AND s.class_id = %s"
        params.append(class_id)
    
    query += " ORDER BY u.full_name"
    
    return execute_query(query, tuple(params) if params else None, fetch_all=True)


# =============================================
# SUBJECT QUERIES
# =============================================

def get_subject_count_by_class(class_id):
    """Get the number of subjects for a class (max should be 5)"""
    query = "SELECT COUNT(*) as count FROM subjects WHERE class_id = %s"
    result = execute_query(query, (class_id,), fetch_one=True)
    return result['count'] if result else 0


def create_subject(name, class_id, teacher_id=None, practical_teacher_id=None, description=None):
    """Create a new subject (enforces max 5 per class)"""
    # Check if class already has 5 subjects
    current_count = get_subject_count_by_class(class_id)
    if current_count >= 5:
        print(f"Cannot add subject: Class already has {current_count} subjects (max 5)")
        return None
    
    query = """
        INSERT INTO subjects (name, class_id, teacher_id, practical_teacher_id, description)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """
    return execute_insert_returning(query, (name, class_id, teacher_id, practical_teacher_id, description))


def get_subject_by_name_and_class(name, class_id):
    """Get a subject by name and class_id"""
    query = """
        SELECT * FROM subjects
        WHERE name = %s AND class_id = %s
    """
    return execute_query(query, (name, class_id), fetch_one=True)


def get_subjects_by_class(class_id):
    """Get all subjects for a class"""
    query = """
        SELECT s.*, t.id as teacher_id, u.full_name as teacher_name
        FROM subjects s
        LEFT JOIN teachers t ON s.teacher_id = t.id
        LEFT JOIN users u ON t.user_id = u.id
        WHERE s.class_id = %s
        ORDER BY s.name
    """
    return execute_query(query, (class_id,), fetch_all=True)


def get_subjects_by_teacher(teacher_id):
    """Get all subjects taught by a teacher"""
    query = """
        SELECT s.*, c.name as class_name
        FROM subjects s
        JOIN classes c ON s.class_id = c.id
        WHERE s.teacher_id = %s
        ORDER BY c.name, s.name
    """
    return execute_query(query, (teacher_id,), fetch_all=True)


def get_all_subjects():
    """Get all subjects with both theory and practical teachers"""
    query = """
        SELECT s.*, c.name as class_name, c.year, c.semester, c.section, c.shift,
               u.full_name as teacher_name,
               u2.full_name as practical_teacher_name
        FROM subjects s
        JOIN classes c ON s.class_id = c.id
        LEFT JOIN teachers t ON s.teacher_id = t.id
        LEFT JOIN users u ON t.user_id = u.id
        LEFT JOIN teachers t2 ON s.practical_teacher_id = t2.id
        LEFT JOIN users u2 ON t2.user_id = u2.id
        ORDER BY c.year, c.semester, s.name
    """
    return execute_query(query, fetch_all=True)


def get_unique_subjects_by_semester():
    """Get unique subjects grouped by year/semester (for dropdown selection)"""
    query = """
        SELECT DISTINCT s.name, c.year, c.semester
        FROM subjects s
        JOIN classes c ON s.class_id = c.id
        ORDER BY c.year, c.semester, s.name
    """
    return execute_query(query, fetch_all=True)


def get_subjects_grouped_by_semester():
    """Get unique subjects grouped by semester (not by class/shift)"""
    query = """
        SELECT DISTINCT ON (s.name, c.year, c.semester) 
            s.id, s.name, s.description, c.year, c.semester,
            u.full_name as teacher_name, t.id as teacher_id,
            u2.full_name as practical_teacher_name, t2.id as practical_teacher_id
        FROM subjects s
        JOIN classes c ON s.class_id = c.id
        LEFT JOIN teachers t ON s.teacher_id = t.id
        LEFT JOIN users u ON t.user_id = u.id
        LEFT JOIN teachers t2 ON s.practical_teacher_id = t2.id
        LEFT JOIN users u2 ON t2.user_id = u2.id
        ORDER BY c.year, c.semester, s.name, s.id
    """
    return execute_query(query, fetch_all=True)


def get_semesters():
    """Get list of unique semesters (year/semester combinations)"""
    return [
        {'year': 1, 'semester': 1, 'name': 'Year 1 - Semester 1'},
        {'year': 1, 'semester': 2, 'name': 'Year 1 - Semester 2'},
        {'year': 2, 'semester': 3, 'name': 'Year 2 - Semester 3'},
        {'year': 2, 'semester': 4, 'name': 'Year 2 - Semester 4'},
    ]


def get_first_class_for_semester(year, semester):
    """Get the first class ID for a given year/semester (for subject creation)"""
    query = """
        SELECT id FROM classes 
        WHERE year = %s AND semester = %s 
        ORDER BY id LIMIT 1
    """
    result = execute_query(query, (year, semester), fetch_one=True)
    return result['id'] if result else None


def get_subject_by_id(subject_id):
    """Get subject by ID with both theory and practical teachers"""
    query = """
        SELECT s.*, c.name as class_name, c.year, c.semester, 
               u.full_name as teacher_name,
               u2.full_name as practical_teacher_name
        FROM subjects s
        JOIN classes c ON s.class_id = c.id
        LEFT JOIN teachers t ON s.teacher_id = t.id
        LEFT JOIN users u ON t.user_id = u.id
        LEFT JOIN teachers t2 ON s.practical_teacher_id = t2.id
        LEFT JOIN users u2 ON t2.user_id = u2.id
        WHERE s.id = %s
    """
    return execute_query(query, (subject_id,), fetch_one=True)


def update_subject(subject_id, name, class_id, teacher_id, practical_teacher_id, description):
    """Update a subject with both theory and practical teachers"""
    query = """
        UPDATE subjects SET name = %s, class_id = %s, teacher_id = %s, practical_teacher_id = %s, description = %s
        WHERE id = %s
    """
    return execute_query(query, (name, class_id, teacher_id, practical_teacher_id, description, subject_id))


def update_subject_teacher(subject_id, teacher_id):
    """Update only the teacher assignment for a subject"""
    query = "UPDATE subjects SET teacher_id = %s WHERE id = %s"
    return execute_query(query, (teacher_id, subject_id))


def delete_subject(subject_id):
    """Delete a subject"""
    query = "DELETE FROM subjects WHERE id = %s"
    return execute_query(query, (subject_id,))


# =============================================
# ATTENDANCE QUERIES
# =============================================

def record_attendance(student_id, subject_id, teacher_id, date, status, notes=None):
    """Record attendance for a student"""
    query = """
        INSERT INTO attendance (student_id, subject_id, teacher_id, date, status, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (student_id, subject_id, date) 
        DO UPDATE SET status = EXCLUDED.status, notes = EXCLUDED.notes
        RETURNING id
    """
    return execute_insert_returning(query, (student_id, subject_id, teacher_id, date, status, notes))


def get_attendance_by_student(student_id):
    """Get all attendance records for a student"""
    query = """
        SELECT a.*, s.name as subject_name
        FROM attendance a
        JOIN subjects s ON a.subject_id = s.id
        WHERE a.student_id = %s
        ORDER BY a.date DESC
    """
    return execute_query(query, (student_id,), fetch_all=True)


def get_attendance_by_subject_date(subject_id, date):
    """Get attendance for a subject on a specific date"""
    query = """
        SELECT a.*, u.full_name as student_name, st.student_number
        FROM attendance a
        JOIN students st ON a.student_id = st.id
        JOIN users u ON st.user_id = u.id
        WHERE a.subject_id = %s AND a.date = %s
        ORDER BY u.full_name
    """
    return execute_query(query, (subject_id, date), fetch_all=True)


def get_attendance_logs(subject_id, student_id=None, date_from=None, date_to=None, status=None):
    """Get attendance logs with filtering"""
    query = """
        SELECT a.*, u.full_name as student_name, st.student_number, s.name as subject_name
        FROM attendance a
        JOIN students st ON a.student_id = st.id
        JOIN users u ON st.user_id = u.id
        JOIN subjects s ON a.subject_id = s.id
        WHERE a.subject_id = %s
    """
    params = [subject_id]
    
    if student_id:
        query += " AND a.student_id = %s"
        params.append(student_id)
    if date_from:
        query += " AND a.date >= %s"
        params.append(date_from)
    if date_to:
        query += " AND a.date <= %s"
        params.append(date_to)
    if status:
        query += " AND a.status = %s"
        params.append(status)
    
    query += " ORDER BY a.date DESC, u.full_name"
    return execute_query(query, tuple(params), fetch_all=True)


def get_attendance_summary(subject_id):
    """Get attendance summary by student for a subject"""
    query = """
        SELECT st.id as student_id, u.full_name as student_name, st.student_number,
               COUNT(*) as total_classes,
               SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present_count,
               SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) as absent_count,
               SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END) as late_count,
               SUM(CASE WHEN a.status = 'excused' THEN 1 ELSE 0 END) as excused_count
        FROM attendance a
        JOIN students st ON a.student_id = st.id
        JOIN users u ON st.user_id = u.id
        WHERE a.subject_id = %s
        GROUP BY st.id, u.full_name, st.student_number
        ORDER BY u.full_name
    """
    return execute_query(query, (subject_id,), fetch_all=True)


def get_attendance_dates(subject_id):
    """Get all unique dates for attendance in a subject"""
    query = """
        SELECT DISTINCT date FROM attendance 
        WHERE subject_id = %s ORDER BY date DESC
    """
    return execute_query(query, (subject_id,), fetch_all=True)


# =============================================
# GRADES QUERIES
# =============================================

def add_grade(student_id, subject_id, teacher_id, grade_type, title, score, max_score, date, notes=None):
    """Add a grade for a student"""
    query = """
        INSERT INTO grades (student_id, subject_id, teacher_id, grade_type, title, score, max_score, date, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    return execute_insert_returning(query, (student_id, subject_id, teacher_id, grade_type, title, score, max_score, date, notes))


def get_grades_by_student(student_id):
    """Get all grades for a student"""
    query = """
        SELECT g.*, s.name as subject_name
        FROM grades g
        JOIN subjects s ON g.subject_id = s.id
        WHERE g.student_id = %s
        ORDER BY g.date DESC
    """
    return execute_query(query, (student_id,), fetch_all=True)


def get_grades_by_subject(subject_id):
    """Get all grades for a subject"""
    query = """
        SELECT g.*, u.full_name as student_name, st.student_number
        FROM grades g
        JOIN students st ON g.student_id = st.id
        JOIN users u ON st.user_id = u.id
        WHERE g.subject_id = %s
        ORDER BY g.date DESC, u.full_name
    """
    return execute_query(query, (subject_id,), fetch_all=True)


# =============================================
# HOMEWORK QUERIES
# =============================================

def create_homework(class_id, subject_id, teacher_id, title, description, due_date):
    """Create a new homework assignment"""
    query = """
        INSERT INTO homework (class_id, subject_id, teacher_id, title, description, due_date)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    return execute_insert_returning(query, (class_id, subject_id, teacher_id, title, description, due_date))


def get_homework_by_class(class_id):
    """Get all homework for a class"""
    query = """
        SELECT h.*, s.name as subject_name, u.full_name as teacher_name
        FROM homework h
        JOIN subjects s ON h.subject_id = s.id
        LEFT JOIN teachers t ON h.teacher_id = t.id
        LEFT JOIN users u ON t.user_id = u.id
        WHERE h.class_id = %s
        ORDER BY h.due_date DESC
    """
    return execute_query(query, (class_id,), fetch_all=True)


def get_homework_by_teacher(teacher_id):
    """Get all homework created by a teacher"""
    query = """
        SELECT h.*, s.name as subject_name, c.name as class_name
        FROM homework h
        JOIN subjects s ON h.subject_id = s.id
        JOIN classes c ON h.class_id = c.id
        WHERE h.teacher_id = %s
        ORDER BY h.due_date DESC
    """
    return execute_query(query, (teacher_id,), fetch_all=True)


# =============================================
# WEEKLY TOPICS QUERIES
# =============================================

def create_weekly_topic(class_id, subject_id, teacher_id, week_number, topic, description=None, date_covered=None):
    """Create a weekly topic"""
    query = """
        INSERT INTO weekly_topics (class_id, subject_id, teacher_id, week_number, topic, description, date_covered)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (class_id, subject_id, week_number) 
        DO UPDATE SET topic = EXCLUDED.topic, description = EXCLUDED.description, date_covered = EXCLUDED.date_covered
        RETURNING id
    """
    return execute_insert_returning(query, (class_id, subject_id, teacher_id, week_number, topic, description, date_covered))


def get_weekly_topics_by_class(class_id):
    """Get all weekly topics for a class"""
    query = """
        SELECT wt.*, s.name as subject_name, u.full_name as teacher_name
        FROM weekly_topics wt
        JOIN subjects s ON wt.subject_id = s.id
        LEFT JOIN teachers t ON wt.teacher_id = t.id
        LEFT JOIN users u ON t.user_id = u.id
        WHERE wt.class_id = %s
        ORDER BY s.name, wt.week_number
    """
    return execute_query(query, (class_id,), fetch_all=True)


def get_weekly_topics_by_subject(subject_id):
    """Get weekly topics for a subject"""
    query = """
        SELECT wt.*, u.full_name as teacher_name
        FROM weekly_topics wt
        LEFT JOIN teachers t ON wt.teacher_id = t.id
        LEFT JOIN users u ON t.user_id = u.id
        WHERE wt.subject_id = %s
        ORDER BY wt.week_number
    """
    return execute_query(query, (subject_id,), fetch_all=True)


# =============================================
# TIMETABLE QUERIES
# =============================================

def create_timetable_entry(class_id, subject_id, teacher_id, day_of_week, start_time, end_time, room=None):
    """Create a timetable entry"""
    query = """
        INSERT INTO timetable (class_id, subject_id, teacher_id, day_of_week, start_time, end_time, room)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    return execute_insert_returning(query, (class_id, subject_id, teacher_id, day_of_week, start_time, end_time, room))


def get_timetable_by_class(class_id):
    """Get timetable for a class"""
    query = """
        SELECT tt.*, s.name as subject_name, u.full_name as teacher_name
        FROM timetable tt
        JOIN subjects s ON tt.subject_id = s.id
        LEFT JOIN teachers t ON tt.teacher_id = t.id
        LEFT JOIN users u ON t.user_id = u.id
        WHERE tt.class_id = %s
        ORDER BY 
            CASE tt.day_of_week
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7
            END,
            tt.start_time
    """
    return execute_query(query, (class_id,), fetch_all=True)


def get_timetable_by_teacher(teacher_id):
    """Get timetable for a teacher"""
    query = """
        SELECT tt.*, s.name as subject_name, c.name as class_name
        FROM timetable tt
        JOIN subjects s ON tt.subject_id = s.id
        JOIN classes c ON tt.class_id = c.id
        WHERE tt.teacher_id = %s
        ORDER BY 
            CASE tt.day_of_week
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                WHEN 'Sunday' THEN 7
            END,
            tt.start_time
    """
    return execute_query(query, (teacher_id,), fetch_all=True)


# =============================================
# LECTURE FILES MANAGEMENT
# =============================================

def create_lecture_file(subject_id, teacher_id, title, description, file_name, file_path, file_size, file_type, week_number=None):
    """Upload a new lecture file"""
    query = """
        INSERT INTO lecture_files (subject_id, teacher_id, title, description, file_name, file_path, file_size, file_type, week_number)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    return execute_insert_returning(query, (subject_id, teacher_id, title, description, file_name, file_path, file_size, file_type, week_number))


def get_lecture_files_by_subject(subject_id):
    """Get all lecture files for a subject"""
    query = """
        SELECT lf.*, u.full_name as teacher_name
        FROM lecture_files lf
        JOIN teachers t ON lf.teacher_id = t.id
        JOIN users u ON t.user_id = u.id
        WHERE lf.subject_id = %s
        ORDER BY lf.week_number NULLS LAST, lf.uploaded_at DESC
    """
    return execute_query(query, (subject_id,), fetch_all=True)


def get_lecture_files_by_teacher(teacher_id):
    """Get all lecture files uploaded by a teacher"""
    query = """
        SELECT lf.*, s.name as subject_name, c.name as class_name
        FROM lecture_files lf
        JOIN subjects s ON lf.subject_id = s.id
        JOIN classes c ON s.class_id = c.id
        WHERE lf.teacher_id = %s
        ORDER BY lf.uploaded_at DESC
    """
    return execute_query(query, (teacher_id,), fetch_all=True)


def get_lecture_files_by_class(class_id):
    """Get all lecture files for a class"""
    query = """
        SELECT lf.*, s.name as subject_name, u.full_name as teacher_name
        FROM lecture_files lf
        JOIN subjects s ON lf.subject_id = s.id
        JOIN teachers t ON lf.teacher_id = t.id
        JOIN users u ON t.user_id = u.id
        WHERE s.class_id = %s
        ORDER BY s.name, lf.week_number NULLS LAST, lf.uploaded_at DESC
    """
    return execute_query(query, (class_id,), fetch_all=True)


def get_lecture_file_by_id(file_id):
    """Get a specific lecture file"""
    query = """
        SELECT lf.*, s.name as subject_name, u.full_name as teacher_name
        FROM lecture_files lf
        JOIN subjects s ON lf.subject_id = s.id
        JOIN teachers t ON lf.teacher_id = t.id
        JOIN users u ON t.user_id = u.id
        WHERE lf.id = %s
    """
    return execute_query(query, (file_id,), fetch_one=True)


def delete_lecture_file(file_id):
    """Delete a lecture file"""
    query = "DELETE FROM lecture_files WHERE id = %s"
    return execute_query(query, (file_id,))


# =============================================
# SEMESTER SUBJECTS QUERIES (NEW STRUCTURE)
# =============================================

def get_all_semester_subjects():
    """Get all semester subjects"""
    query = """
        SELECT * FROM semester_subjects
        ORDER BY year, semester, name
    """
    return execute_query(query, fetch_all=True)


def get_semester_subjects(year, semester):
    """Get subjects for a specific year and semester"""
    query = """
        SELECT * FROM semester_subjects
        WHERE year = %s AND semester = %s
        ORDER BY name
    """
    return execute_query(query, (year, semester), fetch_all=True)


def get_semester_subject_by_id(subject_id):
    """Get a semester subject by ID"""
    query = "SELECT * FROM semester_subjects WHERE id = %s"
    return execute_query(query, (subject_id,), fetch_one=True)


def create_semester_subject(name, year, semester, description=None):
    """Create a new semester subject"""
    query = """
        INSERT INTO semester_subjects (name, year, semester, description)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """
    return execute_insert_returning(query, (name, year, semester, description))


# =============================================
# TEACHER ASSIGNMENTS (NEW STRUCTURE)
# =============================================

def get_teacher_assignments(teacher_id):
    """Get all subject assignments for a teacher"""
    query = """
        SELECT ta.*, ss.name as subject_name, ss.year, ss.semester
        FROM teacher_assignments ta
        JOIN semester_subjects ss ON ta.subject_id = ss.id
        WHERE ta.teacher_id = %s
        ORDER BY ss.year, ss.semester, ta.shift
    """
    return execute_query(query, (teacher_id,), fetch_all=True)


def assign_teacher_to_subject(teacher_id, subject_id, shift):
    """Assign a teacher to teach a subject for a specific shift"""
    query = """
        INSERT INTO teacher_assignments (teacher_id, subject_id, shift)
        VALUES (%s, %s, %s)
        ON CONFLICT (teacher_id, subject_id, shift) DO NOTHING
        RETURNING id
    """
    return execute_insert_returning(query, (teacher_id, subject_id, shift))


def remove_teacher_assignment(assignment_id):
    """Remove a teacher assignment"""
    query = "DELETE FROM teacher_assignments WHERE id = %s"
    return execute_query(query, (assignment_id,))


def get_teachers_for_subject(subject_id, shift=None):
    """Get all teachers assigned to a subject"""
    query = """
        SELECT ta.*, t.id as teacher_id, u.full_name as teacher_name
        FROM teacher_assignments ta
        JOIN teachers t ON ta.teacher_id = t.id
        JOIN users u ON t.user_id = u.id
        WHERE ta.subject_id = %s
    """
    params = [subject_id]
    if shift:
        query += " AND ta.shift = %s"
        params.append(shift)
    query += " ORDER BY u.full_name"
    return execute_query(query, tuple(params), fetch_all=True)


# =============================================
# STUDENT QUERIES (UPDATED FOR NEW STRUCTURE)
# =============================================

def create_student_v2(user_id, year, shift, section=None, student_number=None, phone=None):
    """Create student with year/shift (section assigned later)"""
    query = """
        INSERT INTO students (user_id, year, shift, section, student_number, phone)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """
    return execute_insert_returning(query, (user_id, year, shift, section, student_number, phone))


def update_student_v2(student_id, full_name, email, year, semester, shift, section, student_number, phone):
    """Update student with new structure including semester"""
    query = """
        UPDATE students 
        SET year = %s, semester = %s, shift = %s, section = %s, student_number = %s, phone = %s
        WHERE id = %s
    """
    result = execute_query(query, (year, semester, shift, section, student_number, phone, student_id))
    
    # Also update user info
    student = get_student_by_id(student_id)
    if student:
        query2 = "UPDATE users SET full_name = %s, email = %s WHERE id = %s"
        execute_query(query2, (full_name, email, student['user_id']))
    
    return result


def get_students_by_year_shift(year, shift, section=None):
    """Get students by year and shift, optionally filtered by section"""
    query = """
        SELECT s.*, u.full_name, u.username, u.email
        FROM students s
        JOIN users u ON s.user_id = u.id
        WHERE s.year = %s AND s.shift = %s
    """
    params = [year, shift]
    if section:
        query += " AND s.section = %s"
        params.append(section)
    query += " ORDER BY s.section, u.full_name"
    return execute_query(query, tuple(params), fetch_all=True)


def get_students_without_section(year=None, shift=None):
    """Get students not yet assigned to a section"""
    query = """
        SELECT s.*, u.full_name, u.username, u.email
        FROM students s
        JOIN users u ON s.user_id = u.id
        WHERE s.section IS NULL
    """
    params = []
    if year:
        query += " AND s.year = %s"
        params.append(year)
    if shift:
        query += " AND s.shift = %s"
        params.append(shift)
    query += " ORDER BY s.year, s.shift, u.full_name"
    return execute_query(query, tuple(params) if params else None, fetch_all=True)


def assign_student_section(student_id, section):
    """Assign a student to a section"""
    query = "UPDATE students SET section = %s WHERE id = %s"
    return execute_query(query, (section, student_id))


def update_student_v2(student_id, full_name, email, year, semester, shift, section, student_number, phone):
    """Update student with new year/semester/shift/section structure"""
    # Update student record
    query = """
        UPDATE students 
        SET year = %s, semester = %s, shift = %s, section = %s, student_number = %s, phone = %s
        WHERE id = %s
    """
    result = execute_query(query, (year, semester, shift, section, student_number, phone, student_id))
    
    # Also update user info
    student = get_student_by_id(student_id)
    if student:
        query2 = "UPDATE users SET full_name = %s, email = %s WHERE id = %s"
        execute_query(query2, (full_name, email, student['user_id']))
    
    return result


def get_all_students_v2():
    """Get all students with new structure fields"""
    query = """
        SELECT s.*, u.full_name, u.username, u.email
        FROM students s
        JOIN users u ON s.user_id = u.id
        ORDER BY s.year, s.shift, s.section, u.full_name
    """
    return execute_query(query, fetch_all=True)


def get_student_by_id_v2(student_id):
    """Get student by ID with new structure"""
    query = """
        SELECT s.*, u.full_name, u.username, u.email
        FROM students s
        JOIN users u ON s.user_id = u.id
        WHERE s.id = %s
    """
    return execute_query(query, (student_id,), fetch_one=True)


# =============================================
# TEACHER VIEW HELPERS
# =============================================

def get_teacher_sections(teacher_id, year, semester, shift):
    """Get all sections a teacher teaches for a year/semester/shift"""
    # Get distinct sections where students exist
    query = """
        SELECT DISTINCT s.section
        FROM students s
        WHERE s.year = %s AND s.shift = %s AND s.section IS NOT NULL
        ORDER BY s.section
    """
    # For year 1, semester is 1 or 2; for year 2, semester is 3 or 4
    return execute_query(query, (year, shift), fetch_all=True)


def get_teacher_current_context(teacher_id):
    """Get teacher's assigned subjects grouped by year/shift"""
    query = """
        SELECT ta.shift, ss.year, ss.semester, ss.id as subject_id, ss.name as subject_name,
               (SELECT COUNT(DISTINCT s.section) FROM students s 
                WHERE s.year = ss.year AND s.shift = ta.shift AND s.section IS NOT NULL) as section_count
        FROM teacher_assignments ta
        JOIN semester_subjects ss ON ta.subject_id = ss.id
        WHERE ta.teacher_id = %s
        ORDER BY ss.year, ss.semester, ta.shift, ss.name
    """
    return execute_query(query, (teacher_id,), fetch_all=True)


# =============================================
# CLASS SCHEDULE QUERIES
# =============================================

def get_schedule(semester, shift, section):
    """Get schedule for a specific semester/shift/section"""
    query = """
        SELECT * FROM class_schedules
        WHERE semester = %s AND shift = %s AND section = %s
    """
    return execute_query(query, (semester, shift, section), fetch_one=True)


def save_schedule(semester, shift, section, schedule_data):
    """Save or update schedule for a semester/shift/section"""
    import json
    # Convert to JSON string if needed
    if isinstance(schedule_data, (list, dict)):
        schedule_data = json.dumps(schedule_data)
    
    query = """
        INSERT INTO class_schedules (semester, shift, section, schedule_data, updated_at)
        VALUES (%s, %s, %s, %s::jsonb, CURRENT_TIMESTAMP)
        ON CONFLICT (semester, shift, section)
        DO UPDATE SET schedule_data = EXCLUDED.schedule_data, updated_at = CURRENT_TIMESTAMP
        RETURNING id
    """
    return execute_insert_returning(query, (semester, shift, section, schedule_data))


def delete_schedule(semester, shift, section):
    """Delete a schedule"""
    query = """
        DELETE FROM class_schedules
        WHERE semester = %s AND shift = %s AND section = %s
    """
    return execute_query(query, (semester, shift, section))


def get_all_schedules():
    """Get all schedules"""
    query = """
        SELECT * FROM class_schedules
        ORDER BY semester, shift, section
    """
    return execute_query(query, fetch_all=True)


