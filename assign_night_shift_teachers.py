import db

print("Assigning teachers to Sem 3 Night shift classes...")
print("=" * 100)

# First, let's see what subjects exist for Sem 3
query_subjects = """
    SELECT DISTINCT s.id, s.name, s.semester
    FROM subjects s
    WHERE s.semester = 3
    ORDER BY s.name
"""

subjects = db.execute_query(query_subjects, fetch_all=True)

print("\nAvailable Sem 3 Subjects:")
print("-" * 100)
for i, subject in enumerate(subjects, 1):
    print(f"{i}. {subject['name']} (ID: {subject['id']})")

# Get Sem 3 Night shift classes
query_classes = """
    SELECT id, name, semester, section
    FROM classes
    WHERE semester = 3 AND LOWER(shift) = 'night'
    ORDER BY section
"""

night_classes = db.execute_query(query_classes, fetch_all=True)

print("\nSem 3 Night Shift Classes:")
print("-" * 100)
for cls in night_classes:
    print(f"Class ID {cls['id']}: {cls['name']}")

# Get all teachers
query_teachers = """
    SELECT t.id, u.full_name, u.username
    FROM teachers t
    JOIN users u ON t.user_id = u.id
    ORDER BY u.full_name
"""

teachers = db.execute_query(query_teachers, fetch_all=True)

print("\nAvailable Teachers:")
print("-" * 100)
for i, teacher in enumerate(teachers, 1):
    print(f"{i}. {teacher['full_name']} (@{teacher['username']}) - Teacher ID: {teacher['id']}")

print("\n" + "=" * 100)
print("\nTo assign a teacher to Sem 3 Night shift classes:")
print("1. Choose a teacher ID from the list above")
print("2. Choose a subject ID from the subjects list")
print("3. The teacher will be assigned to teach that subject for ALL Sem 3 Night classes (A, B, C)")
print("\nExample assignment commands:")
print("-" * 100)

# Create example assignment for the first teacher and subject
if teachers and subjects and night_classes:
    example_teacher = teachers[0]
    example_subject = subjects[0]
    
    print(f"\n# Assign {example_teacher['full_name']} to teach {example_subject['name']} for all Sem 3 Night classes:")
    for cls in night_classes:
        print(f"INSERT INTO teacher_assignments (teacher_id, subject_id, class_id, shift)")
        print(f"VALUES ({example_teacher['id']}, {example_subject['id']}, {cls['id']}, 'night');")
    
print("\n" + "=" * 100)
print("\nRun the assignment? (This will assign the first teacher to the first subject)")
print("Enter 'yes' to proceed, or 'no' to cancel:")

# For now, just display the info - don't auto-assign
print("\n[INFO] Script completed. Use the SQL commands above to assign teachers manually,")
print("       or modify this script to do automatic assignment.")
