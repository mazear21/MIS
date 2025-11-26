"""
MIS Institute Management System
Main Flask Application
"""
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime, date
import os
import db
from config import config

# Initialize Flask app
app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# File Upload Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'txt', 'zip', 'rar', 'jpg', 'jpeg', 'png', 'gif'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# =============================================
# AUTHENTICATION DECORATORS
# =============================================

def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


def teacher_required(f):
    """Decorator to require teacher role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') not in ['admin', 'teacher']:
            flash('Access denied. Teacher privileges required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function


# =============================================
# CONTEXT PROCESSORS
# =============================================

@app.context_processor
def inject_user():
    """Make user info available to all templates"""
    if 'user_id' in session:
        return {
            'current_user': {
                'id': session.get('user_id'),
                'username': session.get('username'),
                'full_name': session.get('full_name'),
                'role': session.get('role')
            }
        }
    return {'current_user': None}


# =============================================
# AUTHENTICATION ROUTES
# =============================================

@app.route('/')
def index():
    """Home page - redirect to dashboard if logged in"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please enter both username and password.', 'warning')
            return render_template('login.html')
        
        user = db.get_user_by_username(username)
        
        if user and check_password_hash(user['password_hash'], password):
            # Set session variables
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout user"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# =============================================
# DASHBOARD ROUTES
# =============================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard - redirects based on role"""
    role = session.get('role')
    
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    elif role == 'student':
        return redirect(url_for('student_dashboard'))
    
    return render_template('dashboard.html')


@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard"""
    users = db.get_all_users() or []
    classes = db.get_all_classes() or []
    teachers = db.get_all_teachers() or []
    students = db.get_all_students() or []
    
    stats = {
        'total_users': len(users),
        'total_classes': len(classes),
        'total_teachers': len(teachers),
        'total_students': len(students)
    }
    
    return render_template('admin/dashboard.html', stats=stats)


@app.route('/teacher/dashboard')
@teacher_required
def teacher_dashboard():
    """Teacher dashboard"""
    teacher = db.get_teacher_by_user_id(session['user_id'])
    
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    subjects = db.get_subjects_by_teacher(teacher['id']) or []
    homework = db.get_homework_by_teacher(teacher['id']) or []
    timetable = db.get_timetable_by_teacher(teacher['id']) or []
    
    return render_template('teacher/dashboard.html', 
                         teacher=teacher,
                         subjects=subjects, 
                         homework=homework,
                         timetable=timetable)


@app.route('/student/dashboard')
@login_required
def student_dashboard():
    """Student dashboard"""
    from datetime import date
    if session.get('role') != 'student':
        return redirect(url_for('dashboard'))
    
    student = db.get_student_by_user_id(session['user_id'])
    
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    attendance = db.get_attendance_by_student(student['id']) or []
    grades = db.get_grades_by_student(student['id']) or []
    
    homework = []
    weekly_topics = []
    timetable = []
    
    if student['class_id']:
        homework = db.get_homework_by_class(student['class_id']) or []
        weekly_topics = db.get_weekly_topics_by_class(student['class_id']) or []
        timetable = db.get_timetable_by_class(student['class_id']) or []
    
    today = date.today().isoformat()
    return render_template('student/dashboard.html',
                         student=student,
                         attendance=attendance,
                         grades=grades,
                         homework=homework,
                         weekly_topics=weekly_topics,
                         timetable=timetable,
                         today=today)


# =============================================
# ADMIN - USER MANAGEMENT
# =============================================

@app.route('/admin/users')
@admin_required
def admin_users():
    """Manage users"""
    users = db.get_all_users() or []
    return render_template('admin/users.html', users=users)


@app.route('/admin/users/add', methods=['GET', 'POST'])
@admin_required
def admin_add_user():
    """Add new user"""
    classes = db.get_all_classes() or []
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        role = request.form.get('role', '')
        email = request.form.get('email', '').strip()
        
        # Validation
        if not all([username, password, full_name, role]):
            flash('Please fill in all required fields.', 'warning')
            return render_template('admin/add_user.html', classes=classes)
        
        # Check if username exists
        if db.get_user_by_username(username):
            flash('Username already exists.', 'danger')
            return render_template('admin/add_user.html', classes=classes)
        
        # Create user
        password_hash = generate_password_hash(password)
        user_id = db.create_user(username, password_hash, full_name, role, email)
        
        if user_id:
            # Create role-specific profile
            if role == 'teacher':
                department = request.form.get('department', '').strip()
                phone = request.form.get('phone', '').strip()
                db.create_teacher(user_id, department, phone)
            elif role == 'student':
                class_id = request.form.get('class_id')
                student_number = request.form.get('student_number', '').strip()
                phone = request.form.get('phone', '').strip()
                db.create_student(user_id, class_id if class_id else None, student_number, phone)
            
            flash(f'User "{username}" created successfully!', 'success')
            return redirect(url_for('admin_users'))
        else:
            flash('Error creating user.', 'danger')
    
    return render_template('admin/add_user.html', classes=classes)


@app.route('/admin/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    """Delete a user"""
    if user_id == session['user_id']:
        flash('You cannot delete your own account.', 'danger')
        return redirect(url_for('admin_users'))
    
    result = db.delete_user(user_id)
    if result:
        flash('User deleted successfully.', 'success')
    else:
        flash('Error deleting user.', 'danger')
    
    return redirect(url_for('admin_users'))


# =============================================
# ADMIN - CLASS MANAGEMENT
# =============================================

@app.route('/admin/classes')
@admin_required
def admin_classes():
    """Manage classes"""
    classes = db.get_all_classes() or []
    return render_template('admin/classes.html', classes=classes)


@app.route('/admin/classes/add', methods=['GET', 'POST'])
@admin_required
def admin_add_class():
    """Add new class"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        year = request.form.get('year', type=int)
        semester = request.form.get('semester', type=int)
        
        if not name:
            flash('Please enter a class name.', 'warning')
            return render_template('admin/add_class.html')
        
        class_id = db.create_class(name, description, year, semester)
        
        if class_id:
            flash(f'Class "{name}" created successfully!', 'success')
            return redirect(url_for('admin_classes'))
        else:
            flash('Error creating class.', 'danger')
    
    return render_template('admin/add_class.html')


@app.route('/admin/classes/<int:class_id>/students')
@admin_required
def admin_class_students(class_id):
    """View students in a class"""
    class_info = db.get_class_by_id(class_id)
    if not class_info:
        flash('Class not found.', 'danger')
        return redirect(url_for('admin_classes'))
    
    students = db.get_students_by_class(class_id) or []
    return render_template('admin/class_students.html', class_info=class_info, students=students)


# =============================================
# ADMIN - STUDENT MANAGEMENT
# =============================================

@app.route('/admin/students')
@admin_required
def admin_students():
    """Manage students"""
    year = request.args.get('year')
    class_id = request.args.get('class_id')
    
    if year or class_id:
        students = db.get_students_filtered(year=year, class_id=class_id) or []
    else:
        students = db.get_all_students() or []
    
    classes = db.get_all_classes() or []
    return render_template('admin/students.html', students=students, classes=classes)


@app.route('/admin/students/add', methods=['GET', 'POST'])
@admin_required
def admin_add_student():
    """Add new student"""
    classes = db.get_all_classes() or []
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        class_id = request.form.get('class_id')
        student_number = request.form.get('student_number', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # Validation
        if not all([username, password, full_name, class_id, student_number]):
            flash('Please fill in all required fields.', 'warning')
            return render_template('admin/add_student.html', classes=classes)
        
        # Check if username exists
        if db.get_user_by_username(username):
            flash('Username already exists.', 'danger')
            return render_template('admin/add_student.html', classes=classes)
        
        # Create user
        password_hash = generate_password_hash(password)
        user_id = db.create_user(username, password_hash, full_name, 'student', email)
        
        if user_id:
            db.create_student(user_id, class_id, student_number, phone)
            flash(f'Student "{full_name}" created successfully!', 'success')
            return redirect(url_for('admin_students'))
        else:
            flash('Error creating student.', 'danger')
    
    return render_template('admin/add_student.html', classes=classes)


@app.route('/admin/students/<int:student_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_student(student_id):
    """Edit student"""
    student = db.get_student_by_id(student_id)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('admin_students'))
    
    classes = db.get_all_classes() or []
    
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        class_id = request.form.get('class_id')
        student_number = request.form.get('student_number', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        
        if not full_name or not class_id:
            flash('Please fill in all required fields.', 'warning')
            return render_template('admin/edit_student.html', student=student, classes=classes)
        
        db.update_student(student_id, full_name, email, class_id, student_number, phone)
        
        # Update password if provided
        if password:
            password_hash = generate_password_hash(password)
            db.execute_query("UPDATE users SET password_hash = %s WHERE id = %s", 
                           (password_hash, student['user_id']))
        
        flash('Student updated successfully!', 'success')
        return redirect(url_for('admin_students'))
    
    return render_template('admin/edit_student.html', student=student, classes=classes)


@app.route('/admin/students/<int:student_id>/delete', methods=['POST'])
@admin_required
def admin_delete_student(student_id):
    """Delete student"""
    result = db.delete_student(student_id)
    if result:
        flash('Student deleted successfully.', 'success')
    else:
        flash('Error deleting student.', 'danger')
    return redirect(url_for('admin_students'))


# =============================================
# ADMIN - SUBJECT MANAGEMENT
# =============================================

@app.route('/admin/subjects')
@admin_required
def admin_subjects():
    """Manage subjects"""
    subjects = db.get_all_subjects() or []
    classes = db.get_all_classes() or []
    return render_template('admin/subjects.html', subjects=subjects, classes=classes)


@app.route('/admin/subjects/add', methods=['GET', 'POST'])
@admin_required
def admin_add_subject():
    """Add new subject"""
    classes = db.get_all_classes() or []
    teachers = db.get_all_teachers() or []
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        class_id = request.form.get('class_id')
        teacher_id = request.form.get('teacher_id')
        description = request.form.get('description', '').strip()
        
        if not name or not class_id:
            flash('Please enter subject name and select a class.', 'warning')
            return render_template('admin/add_subject.html', classes=classes, teachers=teachers)
        
        subject_id = db.create_subject(name, class_id, teacher_id if teacher_id else None, description)
        
        if subject_id:
            flash(f'Subject "{name}" created successfully!', 'success')
            return redirect(url_for('admin_subjects'))
        else:
            flash('Error creating subject.', 'danger')
    
    return render_template('admin/add_subject.html', classes=classes, teachers=teachers)


@app.route('/admin/subjects/<int:subject_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_subject(subject_id):
    """Edit subject"""
    subject = db.get_subject_by_id(subject_id)
    if not subject:
        flash('Subject not found.', 'danger')
        return redirect(url_for('admin_subjects'))
    
    classes = db.get_all_classes() or []
    teachers = db.get_all_teachers() or []
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        class_id = request.form.get('class_id')
        teacher_id = request.form.get('teacher_id')
        description = request.form.get('description', '').strip()
        
        if not name or not class_id:
            flash('Please enter subject name and select a semester.', 'warning')
            return render_template('admin/edit_subject.html', subject=subject, classes=classes, teachers=teachers)
        
        db.update_subject(subject_id, name, class_id, teacher_id if teacher_id else None, description)
        flash('Subject updated successfully!', 'success')
        return redirect(url_for('admin_subjects'))
    
    return render_template('admin/edit_subject.html', subject=subject, classes=classes, teachers=teachers)


@app.route('/admin/subjects/<int:subject_id>/delete', methods=['POST'])
@admin_required
def admin_delete_subject(subject_id):
    """Delete subject"""
    result = db.delete_subject(subject_id)
    if result:
        flash('Subject deleted successfully.', 'success')
    else:
        flash('Error deleting subject.', 'danger')
    return redirect(url_for('admin_subjects'))
    
    return render_template('admin/add_subject.html', classes=classes, teachers=teachers)


# =============================================
# TEACHER - ATTENDANCE
# =============================================

@app.route('/teacher/attendance')
@teacher_required
def teacher_attendance():
    """Attendance management page"""
    teacher = db.get_teacher_by_user_id(session['user_id'])
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    subjects = db.get_subjects_by_teacher(teacher['id']) or []
    return render_template('teacher/attendance.html', subjects=subjects, teacher=teacher)


@app.route('/teacher/attendance/take/<int:subject_id>', methods=['GET', 'POST'])
@teacher_required
def teacher_take_attendance(subject_id):
    """Take attendance for a subject"""
    teacher = db.get_teacher_by_user_id(session['user_id'])
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Get subject and class info
    subjects = db.get_subjects_by_teacher(teacher['id']) or []
    subject = next((s for s in subjects if s['id'] == subject_id), None)
    
    if not subject:
        flash('Subject not found or access denied.', 'danger')
        return redirect(url_for('teacher_attendance'))
    
    students = db.get_students_by_class(subject['class_id']) or []
    attendance_date = request.args.get('date', date.today().isoformat())
    
    if request.method == 'POST':
        attendance_date = request.form.get('date', date.today().isoformat())
        
        for student in students:
            status = request.form.get(f'status_{student["id"]}', 'absent')
            notes = request.form.get(f'notes_{student["id"]}', '')
            db.record_attendance(student['id'], subject_id, teacher['id'], attendance_date, status, notes)
        
        flash('Attendance recorded successfully!', 'success')
        return redirect(url_for('teacher_attendance'))
    
    # Get existing attendance for the date
    existing_attendance = db.get_attendance_by_subject_date(subject_id, attendance_date) or []
    attendance_dict = {a['student_id']: a for a in existing_attendance}
    
    return render_template('teacher/take_attendance.html',
                         subject=subject,
                         students=students,
                         attendance_date=attendance_date,
                         attendance_dict=attendance_dict)


@app.route('/teacher/attendance/logs/<int:subject_id>')
@teacher_required
def teacher_attendance_logs(subject_id):
    """View attendance logs with filtering"""
    teacher = db.get_teacher_by_user_id(session['user_id'])
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    subjects = db.get_subjects_by_teacher(teacher['id']) or []
    subject = next((s for s in subjects if s['id'] == subject_id), None)
    
    if not subject:
        flash('Subject not found or access denied.', 'danger')
        return redirect(url_for('teacher_attendance'))
    
    # Get filter parameters
    student_id = request.args.get('student_id', type=int)
    status = request.args.get('status', '')
    
    # Get students for filter dropdown
    students = db.get_students_by_class(subject['class_id']) or []
    
    # Get all logs (no filter for grouping by date)
    all_logs = db.get_attendance_logs(subject_id) or []
    
    # Group logs by date
    logs_by_date = {}
    for log in all_logs:
        date_str = log['date'].strftime('%A, %B %d, %Y') if log['date'] else 'Unknown'
        if date_str not in logs_by_date:
            logs_by_date[date_str] = []
        logs_by_date[date_str].append(log)
    
    # Get student-specific logs if filtered
    student_logs = []
    if student_id:
        student_logs = db.get_attendance_logs(
            subject_id,
            student_id=student_id,
            status=status if status else None
        ) or []
    
    # Get summary
    summary = db.get_attendance_summary(subject_id) or []
    
    # Get all dates for reference
    dates = db.get_attendance_dates(subject_id) or []
    
    return render_template('teacher/attendance_logs.html',
                         subject=subject,
                         students=students,
                         logs_by_date=logs_by_date,
                         student_logs=student_logs,
                         summary=summary,
                         dates=dates,
                         filters={
                             'student_id': student_id,
                             'status': status
                         })


# =============================================
# TEACHER - GRADES
# =============================================

@app.route('/teacher/grades')
@teacher_required
def teacher_grades():
    """Grades management page"""
    teacher = db.get_teacher_by_user_id(session['user_id'])
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    subjects = db.get_subjects_by_teacher(teacher['id']) or []
    return render_template('teacher/grades.html', subjects=subjects, teacher=teacher)


@app.route('/teacher/grades/add/<int:subject_id>', methods=['GET', 'POST'])
@teacher_required
def teacher_add_grades(subject_id):
    """Add grades for a subject"""
    teacher = db.get_teacher_by_user_id(session['user_id'])
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    subjects = db.get_subjects_by_teacher(teacher['id']) or []
    subject = next((s for s in subjects if s['id'] == subject_id), None)
    
    if not subject:
        flash('Subject not found or access denied.', 'danger')
        return redirect(url_for('teacher_grades'))
    
    students = db.get_students_by_class(subject['class_id']) or []
    
    if request.method == 'POST':
        grade_type = request.form.get('grade_type', '')
        title = request.form.get('title', '').strip()
        max_score = request.form.get('max_score', 100)
        grade_date = request.form.get('date', date.today().isoformat())
        
        if not grade_type or not title:
            flash('Please fill in grade type and title.', 'warning')
            return render_template('teacher/add_grades.html', subject=subject, students=students)
        
        for student in students:
            score = request.form.get(f'score_{student["id"]}', '')
            if score:
                notes = request.form.get(f'notes_{student["id"]}', '')
                db.add_grade(student['id'], subject_id, teacher['id'], grade_type, title, 
                           float(score), float(max_score), grade_date, notes)
        
        flash('Grades recorded successfully!', 'success')
        return redirect(url_for('teacher_grades'))
    
    return render_template('teacher/add_grades.html', subject=subject, students=students)


@app.route('/teacher/grades/view/<int:subject_id>')
@teacher_required
def teacher_view_grades(subject_id):
    """View grades for a subject"""
    teacher = db.get_teacher_by_user_id(session['user_id'])
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    subjects = db.get_subjects_by_teacher(teacher['id']) or []
    subject = next((s for s in subjects if s['id'] == subject_id), None)
    
    if not subject:
        flash('Subject not found or access denied.', 'danger')
        return redirect(url_for('teacher_grades'))
    
    grades = db.get_grades_by_subject(subject_id) or []
    return render_template('teacher/view_grades.html', subject=subject, grades=grades)


# =============================================
# TEACHER - HOMEWORK
# =============================================

@app.route('/teacher/homework')
@teacher_required
def teacher_homework():
    """Homework management page"""
    from datetime import date
    teacher = db.get_teacher_by_user_id(session['user_id'])
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    homework = db.get_homework_by_teacher(teacher['id']) or []
    subjects = db.get_subjects_by_teacher(teacher['id']) or []
    today = date.today().isoformat()
    return render_template('teacher/homework.html', homework=homework, subjects=subjects, today=today)


@app.route('/teacher/homework/add', methods=['GET', 'POST'])
@teacher_required
def teacher_add_homework():
    """Add new homework"""
    teacher = db.get_teacher_by_user_id(session['user_id'])
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    subjects = db.get_subjects_by_teacher(teacher['id']) or []
    
    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        due_date = request.form.get('due_date', '')
        
        if not all([subject_id, title, due_date]):
            flash('Please fill in all required fields.', 'warning')
            return render_template('teacher/add_homework.html', subjects=subjects)
        
        # Get class_id from subject
        subject = next((s for s in subjects if s['id'] == int(subject_id)), None)
        if not subject:
            flash('Invalid subject.', 'danger')
            return render_template('teacher/add_homework.html', subjects=subjects)
        
        hw_id = db.create_homework(subject['class_id'], subject_id, teacher['id'], title, description, due_date)
        
        if hw_id:
            flash('Homework created successfully!', 'success')
            return redirect(url_for('teacher_homework'))
        else:
            flash('Error creating homework.', 'danger')
    
    return render_template('teacher/add_homework.html', subjects=subjects)


# =============================================
# TEACHER - WEEKLY TOPICS
# =============================================

@app.route('/teacher/topics')
@teacher_required
def teacher_topics():
    """Weekly topics management"""
    teacher = db.get_teacher_by_user_id(session['user_id'])
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    subjects = db.get_subjects_by_teacher(teacher['id']) or []
    return render_template('teacher/topics.html', subjects=subjects)


@app.route('/teacher/topics/<int:subject_id>', methods=['GET', 'POST'])
@teacher_required
def teacher_manage_topics(subject_id):
    """Manage weekly topics for a subject"""
    teacher = db.get_teacher_by_user_id(session['user_id'])
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    subjects = db.get_subjects_by_teacher(teacher['id']) or []
    subject = next((s for s in subjects if s['id'] == subject_id), None)
    
    if not subject:
        flash('Subject not found or access denied.', 'danger')
        return redirect(url_for('teacher_topics'))
    
    if request.method == 'POST':
        week_number = request.form.get('week_number')
        topic = request.form.get('topic', '').strip()
        description = request.form.get('description', '').strip()
        date_covered = request.form.get('date_covered', '')
        
        if not week_number or not topic:
            flash('Please enter week number and topic.', 'warning')
        else:
            db.create_weekly_topic(subject['class_id'], subject_id, teacher['id'], 
                                 int(week_number), topic, description, date_covered if date_covered else None)
            flash('Topic saved successfully!', 'success')
    
    topics = db.get_weekly_topics_by_subject(subject_id) or []
    return render_template('teacher/manage_topics.html', subject=subject, topics=topics)


# =============================================
# TEACHER - LECTURE FILES MANAGEMENT
# =============================================

@app.route('/teacher/files')
@teacher_required
def teacher_files():
    """View all uploaded lecture files"""
    teacher = db.get_teacher_by_user_id(session['user_id'])
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    files = db.get_lecture_files_by_teacher(teacher['id']) or []
    subjects = db.get_subjects_by_teacher(teacher['id']) or []
    return render_template('teacher/files.html', files=files, subjects=subjects)


@app.route('/teacher/files/upload', methods=['GET', 'POST'])
@teacher_required
def teacher_upload_file():
    """Upload a new lecture file"""
    teacher = db.get_teacher_by_user_id(session['user_id'])
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    subjects = db.get_subjects_by_teacher(teacher['id']) or []
    
    if request.method == 'POST':
        subject_id = request.form.get('subject_id')
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        week_number = request.form.get('week_number', '')
        
        if 'file' not in request.files:
            flash('No file selected.', 'warning')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected.', 'warning')
            return redirect(request.url)
        
        if not subject_id or not title:
            flash('Please fill in all required fields.', 'warning')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # Create unique filename
            original_filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{original_filename}"
            
            # Create subject subfolder
            subject_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"subject_{subject_id}")
            os.makedirs(subject_folder, exist_ok=True)
            
            file_path = os.path.join(subject_folder, filename)
            file.save(file_path)
            
            # Get file info
            file_size = os.path.getsize(file_path)
            file_type = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'unknown'
            
            # Save to database
            week_num = int(week_number) if week_number else None
            db.create_lecture_file(
                subject_id=int(subject_id),
                teacher_id=teacher['id'],
                title=title,
                description=description,
                file_name=original_filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_type,
                week_number=week_num
            )
            
            flash(f'File "{original_filename}" uploaded successfully!', 'success')
            return redirect(url_for('teacher_files'))
        else:
            flash('File type not allowed. Allowed: PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX, TXT, ZIP, RAR, Images', 'danger')
    
    return render_template('teacher/upload_file.html', subjects=subjects)


@app.route('/teacher/files/delete/<int:file_id>', methods=['POST'])
@teacher_required
def teacher_delete_file(file_id):
    """Delete a lecture file"""
    teacher = db.get_teacher_by_user_id(session['user_id'])
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    file_info = db.get_lecture_file_by_id(file_id)
    if file_info and file_info['teacher_id'] == teacher['id']:
        # Delete physical file
        if os.path.exists(file_info['file_path']):
            os.remove(file_info['file_path'])
        # Delete from database
        db.delete_lecture_file(file_id)
        flash('File deleted successfully!', 'success')
    else:
        flash('File not found or access denied.', 'danger')
    
    return redirect(url_for('teacher_files'))


# =============================================
# FILE DOWNLOAD (For both teachers and students)
# =============================================

@app.route('/files/download/<int:file_id>')
@login_required
def download_file(file_id):
    """Download a lecture file"""
    file_info = db.get_lecture_file_by_id(file_id)
    
    if not file_info:
        flash('File not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check access rights
    user_role = session.get('role')
    
    if user_role == 'student':
        student = db.get_student_by_user_id(session['user_id'])
        if student:
            # Get subject's class_id to verify student belongs to that class
            subject = db.get_subject_by_id(file_info['subject_id'])
            if not subject or student['class_id'] != subject['class_id']:
                flash('Access denied.', 'danger')
                return redirect(url_for('dashboard'))
    
    if os.path.exists(file_info['file_path']):
        directory = os.path.dirname(file_info['file_path'])
        filename = os.path.basename(file_info['file_path'])
        return send_from_directory(directory, filename, as_attachment=True, download_name=file_info['file_name'])
    else:
        flash('File not found on server.', 'danger')
        return redirect(url_for('dashboard'))


@app.route('/files/view/<int:file_id>')
@login_required
def view_file(file_id):
    """View a lecture file (for PDFs and images)"""
    file_info = db.get_lecture_file_by_id(file_id)
    
    if not file_info:
        flash('File not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Check access rights
    user_role = session.get('role')
    
    if user_role == 'student':
        student = db.get_student_by_user_id(session['user_id'])
        if student:
            subject = db.get_subject_by_id(file_info['subject_id'])
            if not subject or student['class_id'] != subject['class_id']:
                flash('Access denied.', 'danger')
                return redirect(url_for('dashboard'))
    
    if os.path.exists(file_info['file_path']):
        directory = os.path.dirname(file_info['file_path'])
        filename = os.path.basename(file_info['file_path'])
        return send_from_directory(directory, filename)
    else:
        flash('File not found on server.', 'danger')
        return redirect(url_for('dashboard'))


# =============================================
# STUDENT - VIEW LECTURE FILES
# =============================================

@app.route('/student/files')
@login_required
def student_files():
    """View lecture files for student's class"""
    if session.get('role') != 'student':
        return redirect(url_for('dashboard'))
    
    student = db.get_student_by_user_id(session['user_id'])
    if not student:
        flash('Student profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    files = []
    grouped_files = {}
    if student['class_id']:
        files = db.get_lecture_files_by_class(student['class_id']) or []
        # Group files by subject
        for file in files:
            subject_name = file['subject_name']
            if subject_name not in grouped_files:
                grouped_files[subject_name] = []
            grouped_files[subject_name].append(file)
    
    return render_template('student/files.html', files=files, grouped_files=grouped_files, student=student)


# =============================================
# INITIALIZE DEFAULT ADMIN
# =============================================

def init_admin():
    """Create default admin user if not exists"""
    admin = db.get_user_by_username('admin')
    if not admin:
        password_hash = generate_password_hash('admin123')
        db.create_user('admin', password_hash, 'System Administrator', 'admin', 'admin@mis.edu')
        print("Default admin created. Username: admin, Password: admin123")


# =============================================
# RUN APPLICATION
# =============================================

if __name__ == '__main__':
    init_admin()
    app.run(debug=True, host='0.0.0.0', port=5000)
