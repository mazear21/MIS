import db

subjects = db.get_all_subjects()

sem3 = [s for s in subjects if s['semester'] == 3]
sem4 = [s for s in subjects if s['semester'] == 4]

print("=== SEMESTER 3 SUBJECTS ===")
for s in sem3:
    print(f"  {s['name']} (ID: {s['id']}, Section: {s['section']}, Shift: {s['shift']})")

print("\n=== SEMESTER 4 SUBJECTS ===")
for s in sem4:
    teacher = s.get('teacher_name', 'None')
    print(f"  {s['name']} (ID: {s['id']}, Section: {s['section']}, Shift: {s['shift']}, Teacher: {teacher})")

print("\n=== DUPLICATE CHECK ===")
sem3_names = set([s['name'] for s in sem3])
sem4_names = set([s['name'] for s in sem4])
duplicates = sem3_names.intersection(sem4_names)
print(f"Subjects appearing in BOTH Sem 3 and Sem 4: {duplicates}")

if duplicates:
    print("\n⚠️ WARNING: These subjects should NOT be in both semesters!")
    print("Checking details:")
    for name in duplicates:
        sem3_items = [s for s in sem3 if s['name'] == name]
        sem4_items = [s for s in sem4 if s['name'] == name]
        print(f"\n{name}:")
        print(f"  In Semester 3: {len(sem3_items)} instances")
        print(f"  In Semester 4: {len(sem4_items)} instances")
