import db

print("=== ASSIGNING TEACHERS TO SEMESTER 4 SUBJECTS ===\n")

# Get Semester 4 subjects
subjects = db.get_all_subjects()
sem4_subjects = [s for s in subjects if s['semester'] == 4]

# Assign teachers:
# Advanced Database -> ahmad xalil (ID: 1)
# Statistics -> ahmad xalil (ID: 1)

for s in sem4_subjects:
    if s['name'] == 'Advanced Database':
        print(f"Assigning ahmad xalil to Advanced Database (ID: {s['id']})")
        db.update_subject_teacher(s['id'], 1)
    elif s['name'] == 'Statistics':
        print(f"Assigning ahmad xalil to Statistics (ID: {s['id']})")
        db.update_subject_teacher(s['id'], 1)

print("\n=== VERIFICATION ===\n")
subjects = db.get_all_subjects()
sem4_subjects = [s for s in subjects if s['semester'] == 4]

for s in sorted(sem4_subjects, key=lambda x: x['name']):
    teacher = s.get('teacher_name', 'None')
    status = "✓" if teacher and teacher != 'None' else "✗"
    print(f"{status} {s['name']} - Teacher: {teacher}")

print("\nDone!")
