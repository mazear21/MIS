import db

print("Debugging schedule and file upload issues...")
print("=" * 100)

# 1. Check if student has a class_id
query_student = """
    SELECT s.id, s.student_number, u.full_name, s.class_id, c.name as class_name, 
           c.semester, c.shift, c.section
    FROM students s
    JOIN users u ON s.user_id = u.id
    LEFT JOIN classes c ON s.class_id = c.id
    WHERE u.role = 'student'
    ORDER BY s.id
    LIMIT 5
"""

students = db.execute_query(query_student, fetch_all=True)

print("\nStudent Information:")
print("-" * 100)
if students:
    for student in students:
        print(f"ID: {student['id']}, Name: {student['full_name']}, Class ID: {student['class_id']}")
        print(f"  Class: {student['class_name']}, Sem: {student['semester']}, Shift: {student['shift']}, Section: {student['section']}")
else:
    print("No students found!")

# 2. Check if schedule exists for Sem 3 Night Class A
print("\n" + "=" * 100)
print("\nChecking class_schedules table:")
print("-" * 100)

query_schedules = """
    SELECT semester, shift, section, 
           CASE WHEN schedule_data IS NULL THEN 'NULL' ELSE 'EXISTS' END as has_data
    FROM class_schedules
    ORDER BY semester, shift, section
"""

schedules = db.execute_query(query_schedules, fetch_all=True)

if schedules:
    print(f"{'Semester':<10} {'Shift':<10} {'Section':<10} {'Data':<10}")
    print("-" * 100)
    for sch in schedules:
        print(f"{sch['semester']:<10} {sch['shift']:<10} {sch['section']:<10} {sch['has_data']:<10}")
else:
    print("No schedules found in class_schedules table!")

# 3. Check lecture_files table
print("\n" + "=" * 100)
print("\nChecking lecture_files table:")
print("-" * 100)

query_files = """
    SELECT lf.id, lf.subject_id, lf.class_id, lf.title, lf.file_name, 
           s.name as subject_name, c.name as class_name
    FROM lecture_files lf
    LEFT JOIN subjects s ON lf.subject_id = s.id
    LEFT JOIN classes c ON lf.class_id = c.id
    ORDER BY lf.id DESC
    LIMIT 10
"""

files = db.execute_query(query_files, fetch_all=True)

if files:
    print(f"{'ID':<5} {'Subject ID':<12} {'Class ID':<10} {'Title':<30} {'File':<30}")
    print("-" * 100)
    for f in files:
        print(f"{f['id']:<5} {f['subject_id']:<12} {str(f['class_id']):<10} {f['title']:<30} {f['file_name']:<30}")
        print(f"      Subject: {f['subject_name']}, Class: {f['class_name']}")
else:
    print("No lecture files found!")

# 4. Check what the teacher sees
print("\n" + "=" * 100)
print("\nChecking what teacher sees (get_lecture_files_by_teacher):")
print("-" * 100)

query_teacher_files = """
    SELECT lf.*, s.name as subject_name, c.name as class_name, u.full_name as teacher_name
    FROM lecture_files lf
    JOIN subjects s ON lf.subject_id = s.id
    LEFT JOIN classes c ON lf.class_id = c.id
    JOIN teachers t ON lf.teacher_id = t.id
    JOIN users u ON t.user_id = u.id
    ORDER BY lf.uploaded_at DESC
    LIMIT 5
"""

teacher_files = db.execute_query(query_teacher_files, fetch_all=True)

if teacher_files:
    print(f"{'ID':<5} {'Teacher':<20} {'Subject':<25} {'Class':<35} {'Title':<30}")
    print("-" * 100)
    for f in teacher_files:
        print(f"{f['id']:<5} {f['teacher_name']:<20} {f['subject_name']:<25} {str(f['class_name']):<35} {f['title']:<30}")
else:
    print("No files found for teachers!")

print("\n" + "=" * 100)
