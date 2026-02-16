import db

print("Auto-assigning teachers to Sem 3 Night shift classes...")
print("=" * 100)

# Get Sem 3 subjects
subjects_sem3 = [
    {'id': 147, 'name': 'advanced C++'},
    {'id': 139, 'name': 'web development'}
]

# Get Sem 3 Night classes
night_classes = [
    {'id': 11, 'name': 'Year 2 - Sem 3 - Section A - Night'},
    {'id': 45, 'name': 'Year 2 - Sem 3 - Section B - Night'},
    {'id': 46, 'name': 'Year 2 - Sem 3 - Section C - Night'}
]

# Assign Dr. Omar Rashid (who already teaches Sem 3 morning) to night shift too
teacher_id = 11  # Dr. Omar Rashid
teacher_name = "Dr. Omar Rashid"

print(f"\nAssigning {teacher_name} (ID: {teacher_id}) to Sem 3 Night shift classes...")
print("-" * 100)

success_count = 0
for subject in subjects_sem3:
    for cls in night_classes:
        # Check if assignment already exists
        check_query = """
            SELECT id FROM teacher_assignments
            WHERE teacher_id = %s AND subject_id = %s AND class_id = %s
        """
        existing = db.execute_query(check_query, (teacher_id, subject['id'], cls['id']))
        
        if existing:
            print(f"✓ Already assigned: {subject['name']} to {cls['name']}")
        else:
            # Insert assignment
            insert_query = """
                INSERT INTO teacher_assignments (teacher_id, subject_id, class_id, shift)
                VALUES (%s, %s, %s, 'night')
                RETURNING id
            """
            result = db.execute_insert_returning(insert_query, (teacher_id, subject['id'], cls['id']))
            
            if result:
                print(f"✓ Assigned: {subject['name']} to {cls['name']}")
                success_count += 1
            else:
                print(f"✗ Failed: {subject['name']} to {cls['name']}")

print("-" * 100)
print(f"\n✓ Successfully created {success_count} new teacher assignments!")
print("\n" + "=" * 100)

# Verify the assignments
verify_query = """
    SELECT ta.id, u.full_name as teacher_name, s.name as subject_name, c.name as class_name
    FROM teacher_assignments ta
    JOIN teachers t ON ta.teacher_id = t.id
    JOIN users u ON t.user_id = u.id
    JOIN subjects s ON ta.subject_id = s.id
    JOIN classes c ON ta.class_id = c.id
    WHERE c.semester = 3 AND LOWER(c.shift) = 'night'
    ORDER BY c.name, s.name
"""

assignments = db.execute_query(verify_query, fetch_all=True)

print("\nVerifying Sem 3 Night Shift Assignments:")
print("-" * 100)
if assignments:
    print(f"{'Teacher':<20} {'Subject':<25} {'Class':<40}")
    print("-" * 100)
    for assignment in assignments:
        print(f"{assignment['teacher_name']:<20} {assignment['subject_name']:<25} {assignment['class_name']:<40}")
    print("-" * 100)
    print(f"\n✓ Total: {len(assignments)} assignments")
else:
    print("✗ No assignments found!")

print("\n✓ Done! You can now assign homework to Sem 3 Night shift classes.")
