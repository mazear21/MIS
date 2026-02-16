import db
import json

print("=== CHECKING ADVANCED DATABASE SUBJECT ===\n")

# Get all subjects
subjects = db.get_all_subjects()

# Filter for Advanced Database
advanced_db_subjects = [s for s in subjects if 'advanced' in s['name'].lower() and 'database' in s['name'].lower()]

print(f"Found {len(advanced_db_subjects)} Advanced Database subject(s):\n")
for s in advanced_db_subjects:
    print(f"Subject: {s['name']}")
    print(f"  Class: Year {s['year']}, Semester {s['semester']}, Section {s['section']}, Shift: {s['shift']}")
    print(f"  Theory Teacher: {s.get('teacher_name', 'NOT ASSIGNED')}")
    print(f"  Practical Teacher: {s.get('practical_teacher_name', 'NOT ASSIGNED')}")
    print(f"  teacher_id: {s.get('teacher_id')}")
    print(f"  practical_teacher_id: {s.get('practical_teacher_id')}")
    print()

print("\n=== ALL SEMESTER 4 SUBJECTS ===\n")
sem4_subjects = [s for s in subjects if s['semester'] == 4]
print(f"Total Semester 4 subjects: {len(sem4_subjects)}\n")

for s in sorted(sem4_subjects, key=lambda x: (x['section'], x['name'])):
    teacher_status = "✓" if s.get('teacher_name') else "✗"
    print(f"{teacher_status} {s['name']} (Section {s['section']}, {s['shift']}) - Teacher: {s.get('teacher_name', 'NONE')}")

print("\n=== AVAILABLE TEACHERS ===\n")
teachers = db.get_all_teachers()
print(f"Total teachers: {len(teachers)}\n")
for t in teachers:
    print(f"  - {t['full_name']} (ID: {t['id']})")
