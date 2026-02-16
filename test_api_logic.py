"""
Test the updated API endpoint to ensure it returns correct teacher assignments
"""
from db import get_db_connection

print("="*60)
print("TESTING UPDATED API LOGIC")
print("="*60)

conn = get_db_connection()
cur = conn.cursor()

# Test query for Semester 3 (the one with teacher assignments)
semester = 3

print(f"\nTesting API query for Semester {semester}...")
cur.execute("""
    SELECT DISTINCT
        s.id, s.name, s.class_id,
        c.section, c.shift, c.year, c.semester,
        ta.id as assignment_id,
        t.id as teacher_id,
        u.full_name as teacher_name
    FROM subjects s
    JOIN classes c ON s.class_id = c.id
    LEFT JOIN teacher_assignments ta ON s.id = ta.subject_id AND ta.shift = c.shift
    LEFT JOIN teachers t ON ta.teacher_id = t.id
    LEFT JOIN users u ON t.user_id = u.id
    WHERE c.semester = %s
    ORDER BY c.section, s.name
""", (semester,))

results = cur.fetchall()

print(f"\nFound {len(results)} subject instances for Semester {semester}:")
print("-" * 60)

for row in results:
    subject_id, name, class_id, section, shift, year, sem, assign_id, teacher_id, teacher_name = row
    teacher_display = teacher_name if teacher_name else "NONE"
    print(f"Section {section} ({shift}): {name}")
    print(f"  → Teacher: {teacher_display} (Assignment ID: {assign_id})")

# Check for the duplicate issue - same subject in multiple semesters
print("\n" + "="*60)
print("CHECKING FOR CROSS-SEMESTER DUPLICATES")
print("="*60)

cur.execute("""
    SELECT s.name, c.semester, c.section, u.full_name as teacher
    FROM subjects s
    JOIN classes c ON s.class_id = c.id
    LEFT JOIN teacher_assignments ta ON s.id = ta.subject_id
    LEFT JOIN teachers t ON ta.teacher_id = t.id
    LEFT JOIN users u ON t.user_id = u.id
    WHERE s.name IN ('Advanced Database', 'Statistics')
    ORDER BY s.name, c.semester, c.section
""")

duplicates = cur.fetchall()
print("\nTracking 'Advanced Database' and 'Statistics' across semesters:")
for row in duplicates:
    name, semester, section, teacher = row
    teacher = teacher if teacher else "NONE"
    print(f"  Sem {semester} Section {section}: {name} → {teacher}")

cur.close()
conn.close()

print("\n" + "="*60)
print("✅ API LOGIC TEST COMPLETE")
print("="*60)
