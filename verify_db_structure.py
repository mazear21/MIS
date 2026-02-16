import db

print("=" * 60)
print("DATABASE STRUCTURE CHECK")
print("=" * 60)

# Get all tables
tables_query = """
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name
"""
tables = db.execute_query(tables_query, fetch_all=True)

print("\n📋 TABLES IN DATABASE:")
for t in tables:
    print(f"  ✓ {t['table_name']}")

# Check subjects table structure
print("\n" + "=" * 60)
print("SUBJECTS TABLE STRUCTURE")
print("=" * 60)
columns_query = """
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'subjects'
ORDER BY ordinal_position
"""
columns = db.execute_query(columns_query, fetch_all=True)
print("\nColumns in 'subjects' table:")
for c in columns:
    nullable = "NULL" if c['is_nullable'] == 'YES' else "NOT NULL"
    print(f"  - {c['column_name']:30} {c['data_type']:20} {nullable}")

# Check subjects data
print("\n" + "=" * 60)
print("SUBJECTS WITH TEACHER ASSIGNMENTS")
print("=" * 60)
subjects_query = """
SELECT s.id, s.name, c.year, c.semester, c.section, c.shift,
       s.teacher_id, s.practical_teacher_id,
       u1.full_name as teacher_name,
       u2.full_name as practical_teacher_name
FROM subjects s
JOIN classes c ON s.class_id = c.id
LEFT JOIN teachers t1 ON s.teacher_id = t1.id
LEFT JOIN users u1 ON t1.user_id = u1.id
LEFT JOIN teachers t2 ON s.practical_teacher_id = t2.id
LEFT JOIN users u2 ON t2.user_id = u2.id
ORDER BY c.year, c.semester, c.section, s.name
"""
subjects = db.execute_query(subjects_query, fetch_all=True)

print(f"\nTotal subjects: {len(subjects)}")
print("\nSubject assignments:")

assigned = 0
unassigned = 0

for s in subjects:
    teacher = s['teacher_name'] or 'NONE'
    practical = s['practical_teacher_name'] or 'NONE'
    
    if s['teacher_id'] or s['practical_teacher_id']:
        assigned += 1
        status = "✓"
    else:
        unassigned += 1
        status = "✗"
    
    print(f"{status} Sem {s['semester']} - Section {s['section']} - {s['name']:30} | Teacher: {teacher:20} | Practical: {practical}")

print(f"\n📊 Summary:")
print(f"  ✓ Assigned: {assigned}")
print(f"  ✗ Unassigned: {unassigned}")

# Check teachers table
print("\n" + "=" * 60)
print("TEACHERS TABLE")
print("=" * 60)
teachers_query = """
SELECT t.id, u.full_name, u.email
FROM teachers t
JOIN users u ON t.user_id = u.id
ORDER BY t.id
"""
teachers = db.execute_query(teachers_query, fetch_all=True)
print(f"\nTotal teachers: {len(teachers)}")
for t in teachers:
    print(f"  {t['id']:3} - {t['full_name']:30} ({t['email']})")
