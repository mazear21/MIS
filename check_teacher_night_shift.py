import db

print("Checking teacher assignments and night shift classes...")
print("=" * 100)

# Get all teacher assignments
query1 = """
    SELECT ta.id, ta.teacher_id, u.full_name as teacher_name, 
           s.name as subject_name, c.name as class_name, c.shift, c.semester
    FROM teacher_assignments ta
    JOIN teachers t ON ta.teacher_id = t.id
    JOIN users u ON t.user_id = u.id
    JOIN subjects s ON ta.subject_id = s.id
    JOIN classes c ON ta.class_id = c.id
    ORDER BY c.shift, c.name, s.name
"""

assignments = db.execute_query(query1, fetch_all=True)

print("\nAll Teacher Assignments:")
print("-" * 100)
print(f"{'Teacher':<20} {'Subject':<25} {'Class':<35} {'Shift':<10} {'Sem':<5}")
print("-" * 100)

night_count = 0
for assignment in assignments:
    teacher_name = assignment['teacher_name']
    subject = assignment['subject_name']
    class_name = assignment['class_name']
    shift = assignment['shift']
    semester = assignment['semester']
    
    print(f"{teacher_name:<20} {subject:<25} {class_name:<35} {shift:<10} {semester:<5}")
    
    if shift and shift.lower() == 'night':
        night_count += 1

print("-" * 100)
print(f"\nTotal Night Shift Assignments: {night_count}")

# Get all night shift classes
query2 = """
    SELECT c.id, c.name, c.semester, c.section, c.shift
    FROM classes c
    WHERE LOWER(c.shift) = 'night'
    ORDER BY c.semester, c.section
"""

night_classes = db.execute_query(query2, fetch_all=True)

print("\n" + "=" * 100)
print("\nAll Night Shift Classes:")
print("-" * 100)
print(f"{'ID':<10} {'Class Name':<40} {'Semester':<10} {'Section':<10}")
print("-" * 100)

for cls in night_classes:
    print(f"{cls['id']:<10} {cls['name']:<40} {cls['semester']:<10} {cls['section']:<10}")

print("-" * 100)
print(f"\nTotal Night Shift Classes: {len(night_classes)}")

# Check if any teacher is assigned to Sem 3 Night shift
query3 = """
    SELECT ta.id, u.full_name as teacher_name, s.name as subject_name, c.name as class_name
    FROM teacher_assignments ta
    JOIN teachers t ON ta.teacher_id = t.id
    JOIN users u ON t.user_id = u.id
    JOIN subjects s ON ta.subject_id = s.id
    JOIN classes c ON ta.class_id = c.id
    WHERE c.semester = 3 AND LOWER(c.shift) = 'night'
    ORDER BY c.name
"""

sem3_night = db.execute_query(query3, fetch_all=True)

print("\n" + "=" * 100)
print("\nSem 3 Night Shift Assignments:")
print("-" * 100)
if sem3_night:
    print(f"{'Teacher':<20} {'Subject':<25} {'Class':<35}")
    print("-" * 100)
    for assignment in sem3_night:
        print(f"{assignment['teacher_name']:<20} {assignment['subject_name']:<25} {assignment['class_name']:<35}")
else:
    print("NO TEACHERS ASSIGNED TO SEM 3 NIGHT SHIFT CLASSES!")
    print("\nThis is why you can't assign homework to night shift classes.")
    print("You need to assign teachers to night shift classes first.")

print("-" * 100)
