import db

print("Testing student file access...")
print("=" * 100)

# Get a student (Hana Ibrahim - ID 43, Class 11 - Sem 3 Night A)
student_id = 43
query_student = """
    SELECT s.id, s.class_id, u.full_name, c.name as class_name
    FROM students s
    JOIN users u ON s.user_id = u.id
    LEFT JOIN classes c ON s.class_id = c.id
    WHERE s.id = %s
"""

student = db.execute_query(query_student, (student_id,), fetch_one=True)

if student:
    print(f"\nStudent: {student['full_name']}")
    print(f"Class ID: {student['class_id']}")
    print(f"Class Name: {student['class_name']}")
    
    # Get files for this student's class
    print("\n" + "=" * 100)
    print(f"\nFiles for class {student['class_id']}:")
    print("-" * 100)
    
    files = db.get_lecture_files_by_class(student['class_id'])
    
    if files:
        print(f"Found {len(files)} file(s):\n")
        for f in files:
            print(f"ID: {f['id']}")
            print(f"  Title: {f['title']}")
            print(f"  Subject: {f['subject_name']}")
            print(f"  File: {f['file_name']}")
            print(f"  Class ID in file: {f.get('class_id', 'N/A')}")
            print(f"  Teacher: {f['teacher_name']}")
            print()
    else:
        print("No files found!")
        print("\nThis means either:")
        print("1. No files have been uploaded for this class")
        print("2. The query is not finding files properly")
else:
    print("Student not found!")

print("=" * 100)
