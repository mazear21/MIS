import db
import json

# Check database
subjs = db.get_all_subjects()
print("=== DATABASE: Introduction to Programming entries ===")
for s in subjs:
    if s['name'] == 'Introduction to Programming':
        print(f"  id={s['id']}, class_id={s.get('class_id')}, section={s.get('section')}, shift={s.get('shift')}, teacher={s.get('teacher_name')}")

print()
print("=== All Semester 1 subjects with section/shift info ===")
for s in subjs:
    if s['semester'] == 1:
        print(f"  {s['name']}: section={s.get('section')}, shift={s.get('shift')}, teacher={s.get('teacher_name')}")
