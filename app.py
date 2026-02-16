"""
MIS Institute Management System
Main Flask Application
"""
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory, jsonify
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
    from datetime import datetime
    context = {'now': datetime.now}
    if 'user_id' in session:
        context['current_user'] = {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'full_name': session.get('full_name'),
            'role': session.get('role')
        }
    else:
        context['current_user'] = None
    return context


# =============================================
# TEMPLATE FILTERS
# =============================================

@app.template_filter('replace_section')
def replace_section_filter(text):
    """Replace 'Section' with 'Class' in text"""
    if text:
        return text.replace('Section', 'Class')
    return text


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
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please enter both email and password.', 'warning')
            return render_template('login.html')
        
        user = db.get_user_by_email(email)
        
        if user and (check_password_hash(user['password_hash'], password) or (user.get('plain_password') and user['plain_password'] == password)):
            # Set session variables
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
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
    """Admin dashboard with semester statistics"""
    users = db.get_all_users() or []
    teachers = db.get_all_teachers() or []
    
    # Get total student count directly from students table
    student_count_result = db.execute_query("SELECT COUNT(*) as count FROM students", fetch_one=True)
    total_students = student_count_result['count'] if student_count_result else 0
    
    # Get total unique subject count (count unique subject names)
    subject_count_result = db.execute_query(
        "SELECT COUNT(DISTINCT name) as count FROM subjects", 
        fetch_one=True
    )
    total_subjects = subject_count_result['count'] if subject_count_result else 0
    
    # Get student counts per semester
    semester_stats = db.get_student_counts_by_semester()
    
    stats = {
        'total_users': len(users),
        'total_teachers': len(teachers),
        'total_students': total_students,
        'total_subjects': total_subjects,
        'semesters': semester_stats
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
    
    # Group subjects by name for cleaner display
    grouped_subjects = {}
    for s in subjects:
        name = s['name']
        if name not in grouped_subjects:
            grouped_subjects[name] = {'count': 0, 'classes': []}
        grouped_subjects[name]['count'] += 1
        grouped_subjects[name]['classes'].append(s.get('class_name', ''))
    
    return render_template('teacher/dashboard.html', 
                         teacher=teacher,
                         subjects=subjects,
                         grouped_subjects=grouped_subjects,
                         homework=homework)


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
    schedule_data = None
    
    if student['class_id']:
        homework = db.get_homework_by_class(student['class_id']) or []
        weekly_topics = db.get_weekly_topics_by_class(student['class_id']) or []
        
        # Get student's class details from the student record
        # student record should have year, semester, section info
        class_info = db.execute_query('SELECT year, semester, section, shift FROM classes WHERE id = %s', (student['class_id'],), fetch_one=True)
        if class_info:
            schedule_data = db.get_class_schedule_data(
                class_info['semester'],
                class_info['shift'],
                class_info['section']
            )
    
    today = date.today().isoformat()
    return render_template('student/dashboard.html',
                         student=student,
                         attendance=attendance,
                         grades=grades,
                         homework=homework,
                         weekly_topics=weekly_topics,
                         schedule_data=schedule_data,
                         today=today)


# =============================================
# ADMIN - USER MANAGEMENT
# =============================================

@app.route('/admin/users')
@admin_required
def admin_users():
    """Manage users"""
    users = db.get_all_users() or []
    
    # Get extended data for smart filters
    teachers_raw = db.get_all_teachers_with_subjects() or []
    students_data = db.get_all_students_v2() or []
    
    # Enrich teacher data with subjects
    teachers_data = []
    for teacher in teachers_raw:
        teacher_id = teacher.get('teacher_id')
        subjects = db.get_subjects_by_teacher_id(teacher_id) or []
        teacher['subjects'] = subjects
        teachers_data.append(teacher)
    
    # Create lookup dictionaries
    teacher_lookup = {t['user_id']: t for t in teachers_data}
    student_lookup = {s['user_id']: s for s in students_data}
    
    return render_template('admin/users.html', 
                          users=users, 
                          teacher_lookup=teacher_lookup,
                          student_lookup=student_lookup)


@app.route('/admin/users/add', methods=['GET', 'POST'])
@admin_required
def admin_add_user():
    """Add new user"""
    classes = db.get_all_classes() or []
    default_role = request.args.get('role', '')  # Get role from URL parameter
    
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
        user_id = db.create_user(username, password_hash, full_name, role, email, password)
        
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
    
    return render_template('admin/add_user.html', classes=classes, default_role=default_role)


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


@app.route('/admin/users/<int:user_id>/edit', methods=['POST'])
@admin_required
def admin_edit_user(user_id):
    """Edit user details"""
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')
    
    if not full_name:
        flash('Full name is required.', 'warning')
        return redirect(url_for('admin_users'))
    
    # Update basic info
    result = db.update_user(user_id, full_name, email)
    
    # Update password if provided
    if new_password:
        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('admin_users'))
        
        password_hash = generate_password_hash(new_password)
        db.update_user_password(user_id, password_hash)
    
    if result:
        flash('User updated successfully.', 'success')
    else:
        flash('Error updating user.', 'danger')
    
    return redirect(url_for('admin_users'))


# =============================================
# ADMIN - TEACHER MANAGEMENT
# =============================================

@app.route('/admin/teachers')
@admin_required
def admin_teachers():
    """View all teachers with their subjects"""
    teachers = db.get_all_teachers_with_subjects() or []
    classes = db.get_all_classes() or []
    unique_subjects = db.get_unique_subjects_by_semester() or []
    # Get subjects for each teacher
    for teacher in teachers:
        teacher['subjects'] = db.get_subjects_by_teacher_id(teacher['teacher_id']) or []
    return render_template('admin/teachers.html', teachers=teachers, classes=classes, unique_subjects=unique_subjects)


@app.route('/admin/teachers/<int:teacher_id>/assign-subject', methods=['POST'])
@admin_required
def admin_assign_subject_to_teacher(teacher_id):
    """Quick assign a subject to a teacher for multiple classes"""
    subject_name = request.form.get('subject_name', '').strip()
    class_ids = request.form.getlist('class_ids')  # Get multiple class IDs
    
    if not subject_name or not class_ids:
        flash('Please enter subject name and select at least one class.', 'warning')
        return redirect(url_for('admin_teachers'))
    
    # Get the subject's actual semester from the subjects table
    conn = db.get_db_connection()
    semester = None
    if conn:
        cur = conn.cursor()
        # Look up the subject's semester
        cur.execute("""
            SELECT semester FROM subjects
            WHERE LOWER(name) = LOWER(%s) AND semester IS NOT NULL
            LIMIT 1
        """, (subject_name,))
        subj_row = cur.fetchone()
        if subj_row:
            semester = subj_row[0]
        
        if semester:
            # VALIDATION: Ensure all selected classes belong to this semester
            cur.execute("""
                SELECT id FROM classes 
                WHERE id = ANY(%s) AND semester != %s
            """, (class_ids, semester))
            wrong_classes = cur.fetchall()
            if wrong_classes:
                cur.close()
                conn.close()
                flash(f'⚠️ ERROR: "{subject_name}" belongs to Semester {semester}. You can only assign it to Semester {semester} classes!', 'danger')
                return redirect(url_for('admin_teachers'))
        
        cur.close()
        conn.close()
    
    if not semester:
        # Subject doesn't exist yet — derive semester from selected classes
        conn2 = db.get_db_connection()
        if conn2:
            cur2 = conn2.cursor()
            cur2.execute("SELECT DISTINCT semester FROM classes WHERE id = ANY(%s)", (class_ids,))
            rows = cur2.fetchall()
            if len(rows) == 1:
                semester = rows[0][0]
            else:
                cur2.close()
                conn2.close()
                flash('⚠️ ERROR: Select classes from only ONE semester!', 'danger')
                return redirect(url_for('admin_teachers'))
            cur2.close()
            conn2.close()
    
    if not semester:
        flash('Error determining semester for classes.', 'danger')
        return redirect(url_for('admin_teachers'))
    
    success_count = 0
    for class_id in class_ids:
        # Create or get the subject for this semester
        subject_id = db.create_subject(subject_name, semester)
        if subject_id:
            # Check if assignment already exists
            existing = db.get_subject_by_name_and_class(subject_name, class_id)
            if existing and existing.get('assignment_id'):
                # Update the existing assignment's teacher
                result = db.update_subject_teacher(existing['assignment_id'], teacher_id)
                if result:
                    success_count += 1
            else:
                # Assign teacher to this subject for this class
                assignment_id = db.assign_teacher_to_subject(teacher_id, subject_id, class_id)
                if assignment_id:
                    success_count += 1
    
    if success_count > 0:
        flash(f'Subject "{subject_name}" assigned to {success_count} class(es) in Semester {semester} successfully!', 'success')
    else:
        flash('Error assigning subject.', 'danger')
    
    return redirect(url_for('admin_teachers'))


@app.route('/admin/teachers/unassign-subject/<int:assignment_id>', methods=['POST'])
@admin_required
def admin_unassign_subject(assignment_id):
    """Remove a teacher assignment"""
    result = db.remove_teacher_assignment(assignment_id)
    
    if result:
        flash('Subject unassigned successfully.', 'success')
    else:
        flash('Error unassigning subject.', 'danger')
    
    return redirect(url_for('admin_teachers'))


# =============================================
# ADMIN - CLASS MANAGEMENT
# =============================================

@app.route('/admin/classes')
@admin_required
def admin_classes():
    """Manage classes - shows all 4 semesters"""
    classes = db.get_all_classes() or []
    class_counts, semester_totals = db.get_class_student_counts()
    return render_template('admin/classes.html', classes=classes, class_counts=class_counts, semester_totals=semester_totals)


@app.route('/admin/semester/<int:semester>/<shift>/<section>')
@admin_required
def admin_semester_students(semester, shift, section):
    """View students by Semester/Shift/Class"""
    students = db.get_students_by_semester(semester, shift, section) or []
    year = 1 if semester <= 2 else 2
    
    # Build class_info for the template
    class_info = {
        'year': year,
        'semester': semester,
        'shift': shift,
        'section': section
    }
    
    return render_template('admin/class_students.html', class_info=class_info, students=students)


@app.route('/admin/classes/add', methods=['GET', 'POST'])
@admin_required
def admin_add_class():
    """Add new class"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        year = request.form.get('year', type=int)
        semester = request.form.get('semester', type=int)
        section = request.form.get('section', '').strip()
        shift = request.form.get('shift', '').strip()
        
        # Validation
        if not all([name, year, semester, section, shift]):
            flash('Please fill in all required fields.', 'warning')
            return render_template('admin/add_class.html')
        
        # Validate year-semester combination
        if year == 1 and semester not in [1, 2]:
            flash('Year 1 can only have Semester 1 or 2.', 'danger')
            return render_template('admin/add_class.html')
        if year == 2 and semester not in [3, 4]:
            flash('Year 2 can only have Semester 3 or 4.', 'danger')
            return render_template('admin/add_class.html')
        
        class_id = db.create_class(name, year, semester, section, shift, description)
        
        if class_id:
            flash(f'Class "{name}" created successfully!', 'success')
            return redirect(url_for('admin_classes'))
        else:
            flash('Error creating class. This class combination may already exist.', 'danger')
    
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
    """Manage students with Year/Semester/Shift/Class filters"""
    year = request.args.get('year')
    semester = request.args.get('semester')
    shift = request.args.get('shift')
    section = request.args.get('section')
    
    # Get all students with new structure
    students = db.get_all_students_v2() or []
    
    # Apply filters
    if year:
        students = [s for s in students if s.get('year') == int(year)]
    if semester:
        students = [s for s in students if s.get('semester') == int(semester)]
    if shift:
        students = [s for s in students if s.get('shift') == shift]
    if section:
        if section == 'none':
            students = [s for s in students if not s.get('section')]
        else:
            students = [s for s in students if s.get('section') == section]
    
    return render_template('admin/students.html', students=students)


@app.route('/admin/students/assign-sections', methods=['GET', 'POST'])
@admin_required
def admin_assign_sections():
    """Assign classes to students who don't have one"""
    if request.method == 'POST':
        # Process class assignments
        for key, value in request.form.items():
            if key.startswith('section_') and value:
                student_id = int(key.replace('section_', ''))
                db.assign_student_section(student_id, value)
        flash('Classes assigned successfully!', 'success')
        return redirect(url_for('admin_students'))
    
    # Get students without sections, grouped by year and shift
    students = db.get_students_without_section() or []
    
    # Group students by year and shift
    grouped = {}
    for s in students:
        key = f"Year {s.get('year', '?')} - {(s.get('shift') or 'unknown').title()}"
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(s)
    
    return render_template('admin/assign_sections.html', grouped_students=grouped)


@app.route('/admin/students/add', methods=['GET', 'POST'])
@admin_required
def admin_add_student():
    """Add new student with Semester + Shift + Class (optional)"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip() or None  # Empty string becomes None
        semester = request.form.get('semester', type=int)
        shift = request.form.get('shift')
        section = request.form.get('section') or None  # Optional now
        phone = request.form.get('phone', '').strip() or None  # Empty string becomes None
        
        # Validation - removed username, student_number, and section from required
        if not all([password, full_name, semester, shift]):
            flash('Please fill in all required fields.', 'warning')
            return render_template('admin/add_student.html')
        
        # Derive year from semester
        year = 1 if semester <= 2 else 2
        
        # Auto-generate unique student number (MIS + year + 5-digit sequence)
        import datetime
        current_year = datetime.datetime.now().year
        
        # Get the highest student number to generate next one
        result = db.execute_query(
            "SELECT student_number FROM students WHERE student_number LIKE %s ORDER BY student_number DESC LIMIT 1",
            (f'MIS{current_year}%',),
            fetch_one=True
        )
        
        if result and result['student_number']:
            # Extract the sequence number and increment
            last_num = result['student_number']
            try:
                seq = int(last_num[-5:]) + 1
            except:
                seq = 1
        else:
            seq = 1
        
        student_number = f"MIS{current_year}{seq:05d}"
        
        # Auto-generate username from student number
        username = student_number.lower()
        
        # Check if username exists (shouldn't happen with unique student numbers)
        if db.get_user_by_username(username):
            flash('Error generating unique student ID. Please try again.', 'danger')
            return render_template('admin/add_student.html')
        
        # Create user
        password_hash = generate_password_hash(password)
        user_id = db.create_user(username, password_hash, full_name, 'student', email, password)
        
        if user_id:
            db.create_student_with_semester(user_id, year, semester, shift, section, student_number, phone)
            flash(f'Student "{full_name}" added with ID: {student_number}!', 'success')
            return redirect(url_for('admin_students'))
        else:
            flash('Error creating student.', 'danger')
    
    return render_template('admin/add_student.html')


@app.route('/admin/students/add-ajax', methods=['POST'])
@admin_required
def admin_add_student_ajax():
    """AJAX endpoint to add student without page reload"""
    from flask import jsonify
    
    try:
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip() or None
        semester = request.form.get('semester', type=int)
        shift = request.form.get('shift')
        section = request.form.get('section') or None
        phone = request.form.get('phone', '').strip() or None
        
        # Derive year from semester
        year = 1 if semester and semester <= 2 else 2
        
        # Validation
        if not all([password, full_name, semester, shift]):
            return jsonify({'success': False, 'message': 'Please fill in all required fields.'})
        
        # Auto-generate unique student number
        import datetime
        current_year = datetime.datetime.now().year
        
        result = db.execute_query(
            "SELECT student_number FROM students WHERE student_number LIKE %s ORDER BY student_number DESC LIMIT 1",
            (f'MIS{current_year}%',),
            fetch_one=True
        )
        
        if result and result.get('student_number'):
            try:
                seq = int(result['student_number'][-5:]) + 1
            except:
                seq = 1
        else:
            seq = 1
        
        student_number = f"MIS{current_year}{seq:05d}"
        username = student_number.lower()
        
        if db.get_user_by_username(username):
            return jsonify({'success': False, 'message': 'Error generating unique student ID. Please try again.'})
        
        # Create user
        password_hash = generate_password_hash(password)
        user_id = db.create_user(username, password_hash, full_name, 'student', email, password)
        
        if user_id:
            db.create_student_with_semester(user_id, year, semester, shift, section, student_number, phone)
            return jsonify({
                'success': True,
                'message': f'Student "{full_name}" added with ID: {student_number}',
                'student': {
                    'name': full_name,
                    'student_number': student_number,
                    'semester': semester,
                    'shift': shift,
                    'section': section
                }
            })
        else:
            return jsonify({'success': False, 'message': 'Error creating student user account.'})
    except Exception as e:
        print(f"Error adding student: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'})


@app.route('/admin/students/<int:student_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_student(student_id):
    """Edit student with Year/Shift/Section"""
    student = db.get_student_by_id(student_id)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('admin_students'))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        year = request.form.get('year')
        semester = request.form.get('semester')
        shift = request.form.get('shift')
        section = request.form.get('section') or None
        student_number = request.form.get('student_number', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        
        if not full_name or not year or not semester or not shift:
            flash('Please fill in all required fields (Full Name, Year, Semester, Shift).', 'warning')
            return render_template('admin/edit_student.html', student=student)
        
        # Update student with new fields including semester
        db.update_student_v2(student_id, full_name, email, int(year), int(semester), shift, section, student_number, phone)
        
        # Update password if provided
        if password:
            password_hash = generate_password_hash(password)
            db.execute_query("UPDATE users SET password_hash = %s WHERE id = %s", 
                           (password_hash, student['user_id']))
        
        flash('Student updated successfully!', 'success')
        return redirect(url_for('admin_students'))
    
    return render_template('admin/edit_student.html', student=student)


@app.route('/admin/students/<int:student_id>/edit-ajax', methods=['POST'])
@admin_required
def admin_edit_student_ajax(student_id):
    """Edit student via AJAX"""
    student = db.get_student_by_id(student_id)
    if not student:
        return jsonify({'success': False, 'message': 'Student not found.'})
    
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    year = request.form.get('year')
    semester = request.form.get('semester')
    shift = request.form.get('shift')
    section = request.form.get('section') or None
    student_number = request.form.get('student_number', '').strip()
    phone = request.form.get('phone', '').strip()
    password = request.form.get('password', '')
    
    if not full_name or not year or not semester or not shift:
        return jsonify({'success': False, 'message': 'Please fill in all required fields.'})
    
    # Update student
    db.update_student_v2(student_id, full_name, email, int(year), int(semester), shift, section, student_number, phone)
    
    # Update password if provided
    if password:
        password_hash = generate_password_hash(password)
        db.execute_query("UPDATE users SET password_hash = %s WHERE id = %s", 
                       (password_hash, student['user_id']))
    
    # Return updated student data
    return jsonify({
        'success': True,
        'message': 'Student updated successfully!',
        'student': {
            'id': student_id,
            'full_name': full_name,
            'email': email,
            'year': int(year),
            'semester': int(semester),
            'shift': shift,
            'section': section,
            'student_number': student_number,
            'phone': phone
        }
    })



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
    """Manage subjects - show general definitions only"""
    subjects = db.get_subjects_grouped_by_semester() or []
    return render_template('admin/subjects.html', subjects=subjects)


@app.route('/admin/subjects/add', methods=['GET', 'POST'])
@admin_required
def admin_add_subject():
    """Add new subject for a specific semester"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        year = request.form.get('year', type=int)
        semester = request.form.get('semester', type=int)
        description = request.form.get('description', '').strip()
        
        if not name or not semester:
            flash('Please enter subject name and select semester.', 'warning')
            return render_template('admin/add_subject.html')
        
        # Create subject for this semester
        subject_id = db.create_subject(name, semester, description)
        
        if subject_id:
            flash(f'Subject "{name}" created for Semester {semester} successfully!', 'success')
            return redirect(url_for('admin_subjects'))
        else:
            flash('Subject already exists or error creating subject.', 'info')
    
    return render_template('admin/add_subject.html')


@app.route('/admin/subjects/<int:subject_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_subject(subject_id):
    """Edit subject"""
    subject = db.get_subject_by_id(subject_id)
    if not subject:
        flash('Subject not found.', 'danger')
        return redirect(url_for('admin_subjects'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        year = request.form.get('year', type=int)
        semester = request.form.get('semester', type=int)
        description = request.form.get('description', '').strip()
        
        if not name or not semester:
            flash('Please enter subject name and select semester.', 'warning')
            return render_template('admin/edit_subject.html', subject=subject)
        
        db.update_subject(subject_id, name, semester, description)
        flash('Subject updated successfully!', 'success')
        return redirect(url_for('admin_subjects'))
    
    return render_template('admin/edit_subject.html', subject=subject)


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
# ADMIN - GRADE COMPONENTS (Grading Rubric)
# =============================================

@app.route('/admin/subjects/<int:subject_id>/grading')
@admin_required
def admin_subject_grading(subject_id):
    """Manage grade distribution/rubric for a subject"""
    subject = db.get_subject_by_id(subject_id)
    if not subject:
        flash('Subject not found!', 'danger')
        return redirect(url_for('admin_subjects'))
    
    # Get grade components for this subject
    components = db.get_grade_components_by_subject(subject_id) or []
    
    # DEBUG: Print component order
    print(f"\n=== Loading grading page for subject {subject_id} ===")
    print("Components in order retrieved:")
    for comp in components:
        print(f"  [{comp['display_order']}] {comp['component_type']}: {comp['component_name']}")
    print("=== End component list ===\n")
    
    # Calculate total weight
    total_weight = db.get_subject_total_weight(subject_id)
    
    # Get summary by type
    summary = db.get_grade_components_summary(subject_id) or []
    
    # Check if valid (total = 100%)
    is_valid = abs(total_weight - 100.0) < 0.01
    
    return render_template('admin/subject_grading.html',
                         subject=subject,
                         components=components,
                         total_weight=total_weight,
                         is_valid=is_valid,
                         summary=summary)


@app.route('/admin/subjects/<int:subject_id>/grading/add', methods=['POST'])
@admin_required
def admin_add_grade_component(subject_id):
    """Add grade component(s) to subject - supports multiple items of same type"""
    subject = db.get_subject_by_id(subject_id)
    if not subject:
        flash('Subject not found!', 'danger')
        return redirect(url_for('admin_subjects'))
    
    component_type = request.form.get('component_type')
    quantity = request.form.get('quantity', type=int, default=1)
    total_weight = request.form.get('weight_percentage', type=float)
    display_order = request.form.get('display_order', type=int, default=0)
    midterm_structure = request.form.get('midterm_structure', 'single')
    
    # Type display names
    type_names = {
        'homework': 'Homework',
        'quiz': 'Quiz',
        'report': 'Report',
        'project': 'Project',
        'exam': 'Exam',
        'midterm': 'Midterm',
        'final': 'Final',
        'lab_report': 'Lab Report',
        'activity': 'Activity',
        'seminar': 'Seminar'
    }
    
    # Handle split midterm specially
    if component_type == 'midterm' and midterm_structure == 'split':
        practical_weight = request.form.get('practical_weight', type=float)
        theoretical_weight = request.form.get('theoretical_weight', type=float)
        
        if not practical_weight or not theoretical_weight:
            flash('Both practical and theoretical weights are required for split midterm!', 'danger')
            return redirect(url_for('admin_subject_grading', subject_id=subject_id))
        
        total_midterm_weight = practical_weight + theoretical_weight
        
        # Check if adding this would exceed 100%
        current_total = db.get_subject_total_weight(subject_id)
        if current_total + total_midterm_weight > 100.01:
            flash(f'Cannot add! Total weight would be {current_total + total_midterm_weight:.2f}% (max 100%)', 'danger')
            return redirect(url_for('admin_subject_grading', subject_id=subject_id))
        
        # Max score equals weight for split midterm
        practical_max = practical_weight
        theoretical_max = theoretical_weight
        
        # Add Midterm Practical
        practical_id = db.add_grade_component(
            subject_id,
            'midterm',
            'Midterm Practical',
            practical_max,
            practical_weight,
            display_order
        )
        
        # Add Midterm Theoretical
        theoretical_id = db.add_grade_component(
            subject_id,
            'midterm',
            'Midterm Theoretical',
            theoretical_max,
            theoretical_weight,
            display_order + 1
        )
        
        if practical_id and theoretical_id:
            flash(f'Midterm split added! Practical: {practical_weight}% ({practical_max} pts), Theoretical: {theoretical_weight}% ({theoretical_max} pts)', 'success')
        else:
            flash('Error adding split midterm!', 'danger')
        
        return redirect(url_for('admin_subject_grading', subject_id=subject_id))
    
    # Validation for regular components
    if not all([component_type, total_weight is not None]):
        flash('All fields are required!', 'danger')
        return redirect(url_for('admin_subject_grading', subject_id=subject_id))
    
    if component_type != 'midterm' or midterm_structure == 'single':
        if quantity < 1 or quantity > 20:
            flash('Quantity must be between 1 and 20!', 'danger')
            return redirect(url_for('admin_subject_grading', subject_id=subject_id))
    
    if total_weight < 0 or total_weight > 100:
        flash('Weight percentage must be between 0 and 100!', 'danger')
        return redirect(url_for('admin_subject_grading', subject_id=subject_id))
    
    # Check if adding this would exceed 100%
    current_total = db.get_subject_total_weight(subject_id)
    if current_total + total_weight > 100.01:
        flash(f'Cannot add! Total weight would be {current_total + total_weight:.2f}% (max 100%)', 'danger')
        return redirect(url_for('admin_subject_grading', subject_id=subject_id))
    
    # Get existing count of this type for numbering
    existing_count = db.get_component_count_by_type(subject_id, component_type)
    
    # CRITICAL: All items use the SAME max_score = total_weight
    # This way teachers enter scores 0-[total_weight] for each item
    # Example: 3 homeworks, 5% total → each max_score = 5
    max_scores = [total_weight] * quantity
    
    # Calculate individual weight per item with HIGH PRECISION
    # Use Decimal for exact calculation to avoid rounding errors
    from decimal import Decimal, ROUND_HALF_UP
    
    total_decimal = Decimal(str(total_weight))
    quantity_decimal = Decimal(str(quantity))
    individual_weight = total_decimal / quantity_decimal
    
    # Distribute weights ensuring EXACT total
    weights = []
    running_total = Decimal('0')
    
    for i in range(quantity - 1):
        # Round to 2 decimal places
        weight = individual_weight.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        weights.append(float(weight))
        running_total += weight
    
    # Last item gets the remainder to ensure EXACT total
    last_weight = total_decimal - running_total
    weights.append(float(last_weight))
    
    # Verify total is EXACT (critical for legal compliance)
    actual_total = sum(weights)
    if abs(actual_total - total_weight) > 0.001:
        flash(f'ERROR: Weight calculation mismatch! Expected {total_weight}%, got {actual_total}%. Please report this bug!', 'danger')
        return redirect(url_for('admin_subject_grading', subject_id=subject_id))
    
    # Add components
    added_count = 0
    type_display = type_names.get(component_type, component_type.title())
    
    for i in range(quantity):
        component_number = existing_count + i + 1
        if quantity == 1:
            # Single item - just use type name
            component_name = type_display
        else:
            # Multiple items - numbered
            component_name = f"{type_display} {component_number}"
        
        component_id = db.add_grade_component(
            subject_id, 
            component_type, 
            component_name, 
            max_scores[i], 
            weights[i], 
            display_order + i
        )
        
        if component_id:
            added_count += 1
    
    if added_count == quantity:
        if quantity == 1:
            flash(f'Component "{type_display}" added! Weight: {total_weight}%, Max Score: {total_weight} pts', 'success')
        else:
            flash(f'{quantity} {type_display} components added! Total: {total_weight}%, Each max: {total_weight} pts. Average of scores → final {total_weight}%', 'success')
    else:
        flash(f'Error: Only {added_count} of {quantity} components were added!', 'warning')
    
    return redirect(url_for('admin_subject_grading', subject_id=subject_id))


@app.route('/admin/subjects/<int:subject_id>/grading/<int:component_id>/delete', methods=['POST'])
@admin_required
def admin_delete_grade_component(subject_id, component_id):
    """Delete a grade component"""
    result = db.delete_grade_component(component_id)
    if result:
        flash('Component deleted successfully!', 'success')
    else:
        flash('Error deleting component!', 'danger')
    
    return redirect(url_for('admin_subject_grading', subject_id=subject_id))


@app.route('/admin/subjects/<int:subject_id>/grading/<int:component_id>/edit', methods=['POST'])
@admin_required
def admin_edit_grade_component(subject_id, component_id):
    """Edit a grade component"""
    component_type = request.form.get('component_type')
    component_name = request.form.get('component_name', '').strip()
    max_score = request.form.get('max_score', type=float)
    weight_percentage = request.form.get('weight_percentage', type=float)
    display_order = request.form.get('display_order', type=int, default=0)
    
    # Validation
    if not all([component_type, component_name, max_score, weight_percentage is not None]):
        flash('All fields are required!', 'danger')
        return redirect(url_for('admin_subject_grading', subject_id=subject_id))
    
    # Update component
    result = db.update_grade_component(component_id, component_type, component_name, max_score, weight_percentage, display_order)
    
    if result:
        flash('Component updated successfully!', 'success')
    else:
        flash('Error updating component!', 'danger')
    
    return redirect(url_for('admin_subject_grading', subject_id=subject_id))


@app.route('/admin/subjects/<int:subject_id>/grading/delete-category/<component_type>', methods=['POST'])
@admin_required
def admin_delete_grade_category(subject_id, component_type):
    """Delete all components of a specific type"""
    print(f"=== DELETE CATEGORY: subject_id={subject_id}, component_type={component_type} ===")
    
    result = db.delete_grade_components_by_type(subject_id, component_type)
    print(f"Delete result: {result}")
    
    type_names = {
        'homework': 'Homework',
        'quiz': 'Quiz',
        'report': 'Report',
        'project': 'Project',
        'exam': 'Exam',
        'midterm': 'Midterm',
        'final': 'Final',
        'lab_report': 'Lab Report',
        'activity': 'Activity',
        'seminar': 'Seminar'
    }
    
    type_display = type_names.get(component_type, component_type.title())
    
    if result and len(result) > 0:
        flash(f'✓ All {type_display} components deleted successfully! ({len(result)} items removed)', 'success')
    else:
        flash(f'No {type_display} components found to delete!', 'warning')
    
    return redirect(url_for('admin_subject_grading', subject_id=subject_id))


@app.route('/admin/subjects/<int:subject_id>/grading/edit-category/<component_type>', methods=['POST'])
@admin_required
def admin_edit_grade_category(subject_id, component_type):
    """Edit total weight for all components of a specific type"""
    new_total_weight = request.form.get('new_total_weight', type=float)
    
    if not new_total_weight or new_total_weight < 0:
        flash('Invalid weight value!', 'danger')
        return redirect(url_for('admin_subject_grading', subject_id=subject_id))
    
    # Get current weight of this type
    components = db.get_grade_components_by_subject(subject_id)
    current_type_weight = float(sum(c['weight_percentage'] for c in components if c['component_type'] == component_type))
    other_weight = float(sum(c['weight_percentage'] for c in components if c['component_type'] != component_type))
    
    # Check if new total would exceed 100%
    if other_weight + new_total_weight > 100.01:
        flash(f'Cannot update! Total would be {other_weight + new_total_weight:.2f}% (max 100%)', 'danger')
        return redirect(url_for('admin_subject_grading', subject_id=subject_id))
    
    result = db.update_grade_components_by_type(subject_id, component_type, new_total_weight)
    
    type_names = {
        'homework': 'Homework',
        'quiz': 'Quiz',
        'report': 'Report',
        'project': 'Project',
        'exam': 'Exam',
        'midterm': 'Midterm',
        'final': 'Final',
        'lab_report': 'Lab Report',
        'activity': 'Activity',
        'seminar': 'Seminar'
    }
    
    type_display = type_names.get(component_type, component_type.title())
    
    if result:
        flash(f'{type_display} category updated! New total: {new_total_weight}%', 'success')
    else:
        flash(f'Error updating {type_display} category!', 'danger')
    
    return redirect(url_for('admin_subject_grading', subject_id=subject_id))


@app.route('/admin/subjects/<int:subject_id>/grading/reorder', methods=['POST'])
@admin_required
def admin_reorder_grade_components(subject_id):
    """Update display order for component categories based on new ordering"""
    category_order = request.form.get('category_order')
    
    if not category_order:
        flash('No order data received!', 'danger')
        return redirect(url_for('admin_subject_grading', subject_id=subject_id))
    
    # Parse category order: "homework,quiz,exam,final"
    categories = [c.strip() for c in category_order.split(',') if c.strip()]
    
    if not categories:
        flash('Invalid order data!', 'danger')
        return redirect(url_for('admin_subject_grading', subject_id=subject_id))
    
    # Debug output
    print(f"Reordering categories for subject {subject_id}: {categories}")
    
    # Update display order for all components based on category position
    result = db.reorder_categories_by_type(subject_id, categories)
    
    if result:
        flash(f'Successfully reordered {len(categories)} categories!', 'success')
    else:
        flash('Failed to update category order!', 'danger')
    
    return redirect(url_for('admin_subject_grading', subject_id=subject_id))


# =============================================
# TEACHER - ATTENDANCE
# =============================================

@app.route('/teacher/attendance')
@teacher_required
def teacher_attendance():
    """Attendance management page - grouped by subject name"""
    teacher = db.get_teacher_by_user_id(session['user_id'])
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    subjects = db.get_subjects_by_teacher(teacher['id']) or []
    
    # Group subjects by name - ONE card per subject, with classes inside
    grouped_subjects = {}
    for s in subjects:
        name = s['name']
        if name not in grouped_subjects:
            grouped_subjects[name] = {'classes': []}
        
        # Parse class info from class_name (e.g., "Year 1 - Sem 1 - Section A - Morning")
        class_name = s.get('class_name', '')
        parts = class_name.split(' - ')
        year = parts[0].replace('Year ', '') if len(parts) > 0 else '?'
        semester = parts[1].replace('Sem ', '') if len(parts) > 1 else '?'
        section = parts[2].replace('Section ', '') if len(parts) > 2 else ''
        shift = parts[3].lower() if len(parts) > 3 else 'morning'
        
        grouped_subjects[name]['classes'].append({
            'subject_id': s['id'],
            'class_id': s.get('class_id'),
            'class_name': class_name,
            'year': year,
            'semester': semester,
            'section': section,
            'shift': shift
        })
    
    return render_template('teacher/attendance.html', grouped_subjects=grouped_subjects, teacher=teacher)


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
        # Stay on the same page instead of redirecting
        return redirect(url_for('teacher_take_attendance', subject_id=subject_id, date=attendance_date))
    
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
    """Grades management page - grouped by subject name"""
    teacher = db.get_teacher_by_user_id(session['user_id'])
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    subjects = db.get_subjects_by_teacher(teacher['id']) or []
    
    # Group subjects by name
    grouped_subjects = {}
    for s in subjects:
        name = s['name']
        if name not in grouped_subjects:
            grouped_subjects[name] = {'classes': []}
        
        class_name = s.get('class_name', '')
        parts = class_name.split(' - ')
        year = parts[0].replace('Year ', '') if len(parts) > 0 else '?'
        semester = parts[1].replace('Sem ', '') if len(parts) > 1 else '?'
        section = parts[2].replace('Section ', '') if len(parts) > 2 else ''
        shift = parts[3].lower() if len(parts) > 3 else 'morning'
        
        grouped_subjects[name]['classes'].append({
            'subject_id': s['id'],
            'class_id': s.get('class_id'),
            'class_name': class_name,
            'year': year,
            'semester': semester,
            'section': section,
            'shift': shift
        })
    
    return render_template('teacher/grades.html', grouped_subjects=grouped_subjects, teacher=teacher)


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
    
    # Get grade components (templates) created by admin
    components = db.get_grade_components_by_subject(subject_id) or []
    
    if request.method == 'POST':
        try:
            print("=== GRADE SUBMISSION DEBUG ===")
            print(f"Form data: {dict(request.form)}")
            
            student_id = request.form.get('student_id', '')
            grade_date_str = request.form.get('date', '').strip()
            
            # Use today's date if empty or invalid
            if not grade_date_str:
                grade_date = date.today().isoformat()
            else:
                grade_date = grade_date_str
            
            print(f"Student ID: {student_id}, Date: {grade_date}")
            print(f"\n=== PROCESSING GRADES FOR STUDENT {student_id} ===")
            
            if not student_id:
                return jsonify({'success': False, 'message': 'Student ID is required'}), 400
            
            # Process all component scores for this student
            grades_saved = 0
            errors = []
            saved_details = []
            
            for key in request.form.keys():
                if key.startswith('component_'):
                    component_id = int(key.replace('component_', ''))
                    score_str = request.form.get(key, '').strip()
                    
                    print(f"\n[{key}] Processing component_id={component_id}, score='{score_str}'")
                    
                    # Only save if score is provided (not empty string)
                    # This allows "0" as a valid score but ignores blank fields
                    if score_str != '':
                        try:
                            score = float(score_str)
                            
                            # Get component details
                            component = next((c for c in components if c['id'] == component_id), None)
                            if component:
                                print(f"[{key}] Component found: {component['component_name']}")
                                print(f"[{key}] Calling upsert_grade...")
                                
                                # Use upsert to update existing or insert new
                                result = db.upsert_grade(
                                    int(student_id), 
                                    subject_id, 
                                    teacher['id'], 
                                    component['component_type'],
                                    component['component_name'],
                                    score, 
                                    float(component['max_score']), 
                                    grade_date,
                                    component_id,
                                    None  # notes
                                )
                                
                                if result:
                                    print(f"[{key}] ✓ SUCCESS! Grade ID: {result}")
                                    grades_saved += 1
                                    saved_details.append(f"{component['component_name']}={score}")
                                else:
                                    error_msg = f"Failed to save {component['component_name']}"
                                    print(f"[{key}] ✗ FAILED! Result was None")
                                    errors.append(error_msg)
                            else:
                                error_msg = f"Component {component_id} not found"
                                errors.append(error_msg)
                                print(f"[{key}] ✗ ERROR: {error_msg}")
                        except ValueError as e:
                            error_msg = f"Invalid score value for component {component_id}: {e}"
                            errors.append(error_msg)
                            print(f"[{key}] ✗ VALUE ERROR: {e}")
                        except Exception as e:
                            error_msg = f"Exception for component {component_id}: {e}"
                            errors.append(error_msg)
                            print(f"[{key}] ✗ EXCEPTION: {e}")
                            import traceback
                            traceback.print_exc()
                    else:
                        print(f"[{key}] Skipped (empty)")
            
            print(f"\n=== SUMMARY ===")
            print(f"Total grades saved: {grades_saved}")
            print(f"Saved: {saved_details}")
            print(f"Errors: {errors}")
            print(f"==================\n")
            
            if grades_saved > 0:
                message = f'{grades_saved} grade(s) saved successfully'
                if errors:
                    message += f'. Errors: {"; ".join(errors)}'
                return jsonify({'success': True, 'message': message}), 200
            else:
                error_msg = 'No valid grades were entered'
                if errors:
                    error_msg += f': {"; ".join(errors)}'
                return jsonify({'success': False, 'message': error_msg}), 400
                
        except Exception as e:
            print(f"ERROR SAVING GRADES: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return render_template('teacher/add_grades.html', 
                          subject=subject, 
                          students=students, 
                          components=components,
                          today=date.today().isoformat())


@app.route('/teacher/grades/student/<int:student_id>/subject/<int:subject_id>')
@teacher_required
def teacher_get_student_grades(student_id, subject_id):
    """Get existing grades for a specific student and subject (for pre-filling the modal)"""
    try:
        print(f"\n=== FETCHING GRADES: student_id={student_id}, subject_id={subject_id} ===")
        
        # Get grades for this student and subject
        query = """
            SELECT g.*, gc.component_name, gc.component_type, gc.max_score as component_max_score, gc.weight_percentage
            FROM grades g
            LEFT JOIN grade_components gc ON g.component_id = gc.id
            WHERE g.student_id = %s AND g.subject_id = %s
            ORDER BY g.date DESC, g.id DESC
        """
        grades = db.execute_query(query, (student_id, subject_id), fetch_all=True) or []
        
        print(f"Raw query returned {len(grades)} grade records")
        for g in grades:
            print(f"  - Grade ID {g.get('id')}: component_id={g.get('component_id')}, score={g.get('score')}, component_name={g.get('component_name')}")
        
        # Group by component_id to get the most recent grade for each component
        latest_grades = {}
        for grade in grades:
            comp_id = grade.get('component_id')
            if comp_id:
                if comp_id not in latest_grades:
                    latest_grades[comp_id] = {
                        'component_id': comp_id,
                        'score': grade['score'],
                        'max_score': grade['max_score'],
                        'weight_percentage': grade.get('weight_percentage', 0),
                        'component_name': grade.get('component_name', ''),
                        'date': grade['date'].isoformat() if hasattr(grade['date'], 'isoformat') else str(grade['date'])
                    }
                    print(f"  \u2713 Added component_id {comp_id}: score={grade['score']}")
                else:
                    print(f"  \u2717 Skipped duplicate component_id {comp_id}")
            else:
                print(f"  \u2717 Skipped grade with no component_id")
        
        result = {
            'success': True,
            'grades': list(latest_grades.values()),
            'debug': {
                'total_records': len(grades),
                'unique_components': len(latest_grades)
            }
        }
        
        print(f"Returning {len(latest_grades)} unique grades")
        print(f"Response: {result}")
        print("=== END FETCH ===\n")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error fetching student grades: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


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
    
    # Get unique subject names for dropdown
    unique_subjects = sorted(set(s['name'] for s in subjects))
    
    if request.method == 'POST':
        assignment_ids = request.form.getlist('assignment_ids')  # Get list of selected assignment IDs
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        due_date = request.form.get('due_date', '')
        
        if not all([assignment_ids, title, due_date]):
            flash('Please fill in all required fields.', 'warning')
            return render_template('teacher/add_homework.html', subjects=subjects, unique_subjects=unique_subjects)
        
        # Create homework for each selected assignment (subject/class combination)
        success_count = 0
        for assignment_id in assignment_ids:
            assignment = next((s for s in subjects if s['assignment_id'] == int(assignment_id)), None)
            if assignment:
                hw_id = db.create_homework(assignment['class_id'], assignment['id'], teacher['id'], title, description, due_date)
                if hw_id:
                    success_count += 1
        
        if success_count > 0:
            flash(f'Homework created successfully for {success_count} class(es)!', 'success')
            return redirect(url_for('teacher_homework'))
        else:
            flash('Error creating homework.', 'danger')
    
    return render_template('teacher/add_homework.html', subjects=subjects, unique_subjects=unique_subjects)


@app.route('/teacher/homework/delete/<int:homework_id>', methods=['POST'])
@teacher_required
def teacher_delete_homework(homework_id):
    """Mark homework as done (delete it)"""
    teacher = db.get_teacher_by_user_id(session['user_id'])
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    # Delete homework - the database will verify teacher_id matches
    result = db.delete_homework(homework_id, teacher['id'])
    
    if result:
        flash('Homework marked as done and removed successfully!', 'success')
    else:
        flash('Error: Could not delete homework. You can only delete your own homework.', 'danger')
    
    return redirect(url_for('teacher_homework'))


# =============================================
# TEACHER - SCHEDULE (View Only)
# =============================================

@app.route('/teacher/schedule')
@teacher_required
def teacher_schedule():
    """View class schedules (read-only)"""
    return render_template('teacher/schedule.html')


@app.route('/teacher/api/schedule/<int:semester>/<shift>/<section>', methods=['GET'])
@teacher_required
def teacher_api_get_schedule(semester, shift, section):
    """API: Get schedule for a semester/shift/section (teacher read-only)"""
    import json
    schedule = db.get_schedule(semester, shift, section)
    if schedule and schedule.get('schedule_data'):
        data = schedule['schedule_data']
        if isinstance(data, (list, dict)):
            return {'success': True, 'data': data}
        return {'success': True, 'data': json.loads(data)}
    return {'success': True, 'data': []}


# =============================================
# TEACHER - WEEKLY TOPICS
# =============================================

@app.route('/teacher/topics')
@teacher_required
def teacher_topics():
    """Weekly topics management - grouped by subject name"""
    teacher = db.get_teacher_by_user_id(session['user_id'])
    if not teacher:
        flash('Teacher profile not found.', 'danger')
        return redirect(url_for('dashboard'))
    
    subjects = db.get_subjects_by_teacher(teacher['id']) or []
    
    # Group subjects by name
    grouped_subjects = {}
    for s in subjects:
        name = s['name']
        if name not in grouped_subjects:
            grouped_subjects[name] = {'classes': []}
        
        class_name = s.get('class_name', '')
        parts = class_name.split(' - ')
        year = parts[0].replace('Year ', '') if len(parts) > 0 else '?'
        semester = parts[1].replace('Sem ', '') if len(parts) > 1 else '?'
        section = parts[2].replace('Section ', '') if len(parts) > 2 else ''
        shift = parts[3].lower() if len(parts) > 3 else 'morning'
        
        grouped_subjects[name]['classes'].append({
            'subject_id': s['id'],
            'class_name': class_name,
            'year': year,
            'semester': semester,
            'section': section,
            'shift': shift
        })
    
    return render_template('teacher/topics.html', grouped_subjects=grouped_subjects)


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
    
    # Get unique subject names for dropdown
    unique_subjects = sorted(set(s['name'] for s in subjects))
    
    if request.method == 'POST':
        assignment_ids = request.form.getlist('assignment_ids')  # Get list of selected assignment IDs
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
        
        if not assignment_ids or not title:
            flash('Please fill in all required fields.', 'warning')
            return render_template('teacher/upload_file.html', subjects=subjects, unique_subjects=unique_subjects)
        
        if file and allowed_file(file.filename):
            # Create unique filename
            original_filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{original_filename}"
            
            # Read file content once to avoid permission issues
            file_content = file.read()
            file_size = len(file_content)
            file_type = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'unknown'
            week_num = int(week_number) if week_number else None
            
            # Upload to each selected subject/class
            success_count = 0
            for assignment_id in assignment_ids:
                # Find the assignment (subject/class combination)
                assignment = next((s for s in subjects if s['assignment_id'] == int(assignment_id)), None)
                if not assignment:
                    continue
                    
                subject_id = assignment['id']
                class_id = assignment['class_id']
                
                # Create subject subfolder
                subject_folder = os.path.join(app.config['UPLOAD_FOLDER'], f"subject_{subject_id}")
                os.makedirs(subject_folder, exist_ok=True)
                
                file_path_individual = os.path.join(subject_folder, filename)
                
                # Write file content to each location
                with open(file_path_individual, 'wb') as f:
                    f.write(file_content)
                
                # Save to database with class_id
                db.create_lecture_file(
                    subject_id=subject_id,
                    teacher_id=teacher['id'],
                    class_id=class_id,
                    title=title,
                    description=description,
                    file_name=original_filename,
                    file_path=file_path_individual,
                    file_size=file_size,
                    file_type=file_type,
                    week_number=week_num
                )
                success_count += 1
            
            flash(f'File "{original_filename}" uploaded successfully to {success_count} class(es)!', 'success')
            return redirect(url_for('teacher_upload_file'))
        else:
            flash('File type not allowed. Allowed: PDF, DOC, DOCX, PPT, PPTX, XLS, XLSX, TXT, ZIP, RAR, Images', 'danger')
    
    return render_template('teacher/upload_file.html', subjects=subjects, unique_subjects=unique_subjects)


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
            # Check if student's class_id matches the file's class_id
            if student['class_id'] != file_info['class_id']:
                flash('Access denied. This file is not for your class.', 'danger')
                return redirect(url_for('student_files'))
    
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
            # Check if student's class_id matches the file's class_id
            if student['class_id'] != file_info['class_id']:
                flash('Access denied. This file is not for your class.', 'danger')
                return redirect(url_for('student_files'))
    
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

# =============================================
# ADMIN - SCHEDULE BUILDER API
# =============================================

@app.route('/admin/api/schedule/<int:semester>/<shift>/<section>', methods=['GET'])
@admin_required
def api_get_schedule(semester, shift, section):
    """API: Get schedule for a semester/shift/section"""
    import json
    schedule = db.get_schedule(semester, shift, section)
    if schedule and schedule.get('schedule_data'):
        data = schedule['schedule_data']
        # If it's already a list/dict, return as-is
        if isinstance(data, (list, dict)):
            return {'success': True, 'data': data}
        # If it's a string, parse it
        return {'success': True, 'data': json.loads(data)}
    return {'success': True, 'data': []}


@app.route('/admin/api/schedule/<int:semester>/<shift>/<section>', methods=['POST'])
@admin_required
def api_save_schedule(semester, shift, section):
    """API: Save schedule for a semester/shift/section"""
    import json
    data = request.get_json()
    schedule_data = data.get('schedule_data', [])
    
    result = db.save_schedule(semester, shift, section, json.dumps(schedule_data))
    if result:
        return {'success': True, 'message': 'Schedule saved successfully!'}
    return {'success': False, 'message': 'Error saving schedule'}, 500


@app.route('/admin/api/teachers-subjects/<int:semester>')
@admin_required
def api_get_teachers_subjects_by_semester(semester):
    """API: Get subjects for this semester + their teacher assignments"""
    conn = db.get_db_connection()
    if not conn:
        return {'subjects': [], 'assignments': []}
    
    cur = conn.cursor()
    
    try:
        # 1) Get all subjects for this semester
        cur.execute("""
            SELECT id, name, description
            FROM subjects
            WHERE semester = %s
            ORDER BY name
        """, (semester,))
        sem_subjects = cur.fetchall()
        
        print(f"Found {len(sem_subjects)} subjects for semester {semester}")
        
        # 2) Build subjects list
        subject_list = []
        for row in sem_subjects:
            subject_list.append({
                'id': row[0],
                'name': row[1],
                'description': row[2] or ''
            })
        
        # 3) Get actual teacher assignments from teacher_assignments table
        subject_ids = [s[0] for s in sem_subjects]
        assignment_list = []
        
        if subject_ids:
            cur.execute("""
                SELECT
                    ta.id AS assignment_id,
                    ta.subject_id,
                    s.name AS subject_name,
                    ta.shift,
                    t.id AS teacher_id,
                    u.full_name AS teacher_name
                FROM teacher_assignments ta
                JOIN subjects s ON ta.subject_id = s.id
                JOIN teachers t ON ta.teacher_id = t.id
                JOIN users u ON t.user_id = u.id
                WHERE ta.subject_id = ANY(%s)
                ORDER BY s.name, ta.shift
            """, (subject_ids,))
            assignments = cur.fetchall()
            
            print(f"Found {len(assignments)} teacher assignments")
            
            # Build assignment list - expand to all sections (A, B, C) since assignments are per shift
            for row in assignments:
                # Each teacher assignment is for a shift, apply to all sections
                for section in ['A', 'B', 'C']:
                    assignment_list.append({
                        'assignment_id': row[0],
                        'subject_id': row[1],
                        'subject_name': row[2],
                        'shift': row[3] or '',
                        'section': section,
                        'teacher_id': row[4],
                        'teacher_name': row[5] or ''
                    })
        
        print(f"API Response: {len(subject_list)} subjects, {len(assignment_list)} assignment entries (expanded) for semester {semester}")
        
        return {
            'subjects': subject_list,
            'assignments': assignment_list
        }
        
    except Exception as e:
        print(f"ERROR in api_get_teachers_subjects_by_semester: {e}")
        import traceback
        traceback.print_exc()
        return {'subjects': [], 'assignments': [], 'error': str(e)}
    finally:
        cur.close()
        conn.close()


@app.route('/admin/api/teachers-subjects')
@admin_required
def api_get_teachers_subjects():
    """API: Get all teachers and subjects for schedule dropdown"""
    teachers = db.get_all_teachers() or []
    subjects = db.get_all_subjects() or []
    
    return {
        'teachers': [{'id': t['id'], 'name': t['full_name']} for t in teachers],
        'subjects': [{
            'id': s['id'], 
            'name': s['name'], 
            'semester': s.get('semester'), 
            'year': s.get('year'), 
            'teacher_name': s.get('teacher_name'),
            'practical_teacher_name': s.get('practical_teacher_name')
        } for s in subjects]
    }


def init_admin():
    """Create default admin user if not exists"""
    admin = db.get_user_by_username('admin')
    if not admin:
        password_hash = generate_password_hash('admin123')
        db.create_user('admin', password_hash, 'System Administrator', 'admin', 'admin@mis.edu', 'admin123')
        print("Default admin created. Username: admin, Password: admin123")


# =============================================
# AJAX ROUTES FOR MODAL EDITING
# =============================================

@app.route('/admin/users/<int:user_id>/edit-ajax', methods=['POST'])
@admin_required
def admin_edit_user_ajax(user_id):
    """Edit user via AJAX"""
    from flask import jsonify
    username = request.form.get('username', '').strip()
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    role = request.form.get('role', '').strip()
    new_password = request.form.get('new_password', '')
    
    if not username or not full_name or not role:
        return jsonify({'success': False, 'message': 'Username, full name, and role are required.'})
    
    # Check if username is being changed and if it exists
    current_user = db.get_user_by_id(user_id)
    if current_user and username != current_user['username']:
        existing = db.get_user_by_username(username)
        if existing:
            return jsonify({'success': False, 'message': 'Username already exists.'})
    
    # Validate password if provided
    if new_password:
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters long.'})
    
    # Update user with username and role
    result = db.update_user_complete(user_id, username, full_name, email, role)
    
    # Update password if provided
    plain_pass = None
    if new_password:
        password_hash = generate_password_hash(new_password)
        plain_pass = new_password
        password_result = db.update_user_password(user_id, password_hash, plain_pass)
        if password_result is None:
            return jsonify({'success': False, 'message': 'Error updating password.'})
    
    if result is not None:
        return jsonify({
            'success': True,
            'message': 'User updated successfully!' + (' Password changed.' if new_password else ''),
            'user': {
                'id': user_id,
                'username': username,
                'full_name': full_name,
                'email': email,
                'role': role,
                'plain_password': plain_pass if plain_pass else None
            }
        })
    return jsonify({'success': False, 'message': 'Error updating user.'})


@app.route('/admin/users/add-ajax', methods=['POST'])
@admin_required
def admin_add_user_ajax():
    """Add user via AJAX"""
    from flask import jsonify
    username = request.form.get('username', '').strip()
    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip()
    role = request.form.get('role', '').strip()
    password = request.form.get('password', '')
    
    if not username or not full_name or not role or not password:
        return jsonify({'success': False, 'message': 'Please fill in all required fields.'})
    
    # Check if username exists
    existing = db.get_user_by_username(username)
    if existing:
        return jsonify({'success': False, 'message': 'Username already exists.'})
    
    password_hash = generate_password_hash(password)
    user_id = db.create_user(username, password_hash, full_name, role, email, password)
    
    if user_id:
        # Fetch the newly created user to return full data
        new_user = db.get_user_by_id(user_id)
        if new_user:
            user_data = {
                'id': new_user['id'],
                'username': new_user['username'],
                'full_name': new_user['full_name'],
                'email': new_user.get('email'),
                'role': new_user['role'],
                'plain_password': new_user.get('plain_password')
            }
            
            # Add additional info based on role
            if role == 'teacher':
                teacher = db.get_teacher_by_user_id(user_id)
                if teacher:
                    subjects = db.get_subjects_by_teacher_id(teacher['id'])
                    user_data['subjects'] = ','.join([str(s['id']) for s in subjects]) if subjects else None
                    user_data['department'] = teacher.get('department')
            elif role == 'student':
                student = db.get_student_by_user_id(user_id)
                if student:
                    user_data['year'] = student.get('year')
                    user_data['semester'] = student.get('semester')
                    user_data['shift'] = student.get('shift')
                    user_data['section'] = student.get('section')
            
            return jsonify({'success': True, 'message': 'User created successfully!', 'user': user_data})
    
    return jsonify({'success': False, 'message': 'Error creating user.'})


@app.route('/admin/subjects/<int:subject_id>/edit-ajax', methods=['POST'])
@admin_required
def admin_edit_subject_ajax(subject_id):
    """Edit subject via AJAX"""
    from flask import jsonify
    try:
        name = request.form.get('name', '').strip()
        year = request.form.get('year', type=int)
        semester = request.form.get('semester', type=int)
        description = request.form.get('description', '').strip()
        
        if not name or not semester:
            return jsonify({'success': False, 'message': 'Please enter subject name and select semester.'})
        
        result = db.update_subject(subject_id, name, semester, description)
        
        if result is not None:
            return jsonify({
                'success': True,
                'message': 'Subject updated successfully!',
                'subject': {
                    'id': subject_id,
                    'name': name
                }
            })
        return jsonify({'success': False, 'message': 'Error updating subject.'})
    except Exception as e:
        print(f'Error in admin_edit_subject_ajax: {e}')
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


@app.route('/admin/subjects/add-ajax', methods=['POST'])
@admin_required
def admin_add_subject_ajax():
    """Add subject via AJAX"""
    from flask import jsonify
    try:
        name = request.form.get('name', '').strip()
        year = request.form.get('year', type=int)
        semester = request.form.get('semester', type=int)
        description = request.form.get('description', '').strip()
        
        if not name or not semester:
            return jsonify({'success': False, 'message': 'Please enter subject name and select semester.'})
        
        result = db.create_subject(name, semester, description)
        
        if result:
            return jsonify({'success': True, 'message': 'Subject created successfully!'})
        return jsonify({'success': False, 'message': 'Subject already exists or error creating subject.'})
    except Exception as e:
        print(f'Error in admin_add_subject_ajax: {e}')
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})


# =============================================
# RUN APPLICATION
# =============================================

if __name__ == '__main__':
    init_admin()
    app.run(debug=True, host='0.0.0.0', port=5000)
