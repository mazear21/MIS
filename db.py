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
        return None
    
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        result = None
        if fetch_one:
            row = cursor.fetchone()
            result = row_to_dict(cursor, row)
        elif fetch_all:
            rows = cursor.fetchall()
            result = [row_to_dict(cursor, row) for row in rows]
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
        return None


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


# =============================================
# CLASS QUERIES
# =============================================

def get_all_classes():
    """Get all classes"""
    query = "SELECT * FROM classes ORDER BY name"
    return execute_query(query, fetch_all=True)


def get_class_by_id(class_id):
    """Get class by ID"""
    query = "SELECT * FROM classes WHERE id = %s"
    return execute_query(query, (class_id,), fetch_one=True)


def create_class(name, description=None, year=None, semester=None):
    """Create a new class/semester"""
    query = """
        INSERT INTO classes (name, description, year, semester)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """
    return execute_insert_returning(query, (name, description, year, semester))


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
    """Get student by ID"""
    query = """
        SELECT s.*, u.full_name, u.username, u.email, c.name as class_name, c.year
        FROM students s
        JOIN users u ON s.user_id = u.id
        LEFT JOIN classes c ON s.class_id = c.id
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

def create_subject(name, class_id, teacher_id=None, description=None):
    """Create a new subject"""
    query = """
        INSERT INTO subjects (name, class_id, teacher_id, description)
        VALUES (%s, %s, %s, %s)
        RETURNING id
    """
    return execute_insert_returning(query, (name, class_id, teacher_id, description))


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
    """Get all subjects"""
    query = """
        SELECT s.*, c.name as class_name, c.year, u.full_name as teacher_name
        FROM subjects s
        JOIN classes c ON s.class_id = c.id
        LEFT JOIN teachers t ON s.teacher_id = t.id
        LEFT JOIN users u ON t.user_id = u.id
        ORDER BY c.year, c.semester, s.name
    """
    return execute_query(query, fetch_all=True)


def get_subject_by_id(subject_id):
    """Get subject by ID"""
    query = """
        SELECT s.*, c.name as class_name, c.year, u.full_name as teacher_name
        FROM subjects s
        JOIN classes c ON s.class_id = c.id
        LEFT JOIN teachers t ON s.teacher_id = t.id
        LEFT JOIN users u ON t.user_id = u.id
        WHERE s.id = %s
    """
    return execute_query(query, (subject_id,), fetch_one=True)


def update_subject(subject_id, name, class_id, teacher_id, description):
    """Update a subject"""
    query = """
        UPDATE subjects SET name = %s, class_id = %s, teacher_id = %s, description = %s
        WHERE id = %s
    """
    return execute_query(query, (name, class_id, teacher_id, description, subject_id))


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

