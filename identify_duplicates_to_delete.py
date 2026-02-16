"""
Identify duplicate subjects across semesters for cleanup
"""
from db import get_db_connection

print("="*60)
print("CROSS-SEMESTER DUPLICATE FINDER")
print("="*60)

conn = get_db_connection()
cur = conn.cursor()

# Find subjects that appear in multiple semesters
print("\n📋 Subjects appearing in multiple semesters:")
print("-"*60)

cur.execute("""
    SELECT s.id, s.name, c.year, c.semester, c.section, c.shift,
           u.full_name as teacher
    FROM subjects s
    JOIN classes c ON s.class_id = c.id
    LEFT JOIN teacher_assignments ta ON s.id = ta.subject_id AND ta.shift = c.shift
    LEFT JOIN teachers t ON ta.teacher_id = t.id
    LEFT JOIN users u ON t.user_id = u.id
    WHERE s.name IN (
        SELECT s2.name 
        FROM subjects s2
        JOIN classes c2 ON s2.class_id = c2.id
        GROUP BY s2.name
        HAVING COUNT(DISTINCT c2.semester) > 1
    )
    ORDER BY s.name, c.semester, c.section
""")

duplicates = cur.fetchall()

if duplicates:
    current_subject = None
    for row in duplicates:
        subject_id, name, year, semester, section, shift, teacher = row
        teacher = teacher if teacher else "No teacher"
        
        if name != current_subject:
            if current_subject:
                print()
            print(f"\n🔴 '{name}':")
            current_subject = name
        
        print(f"   ID {subject_id:3d} | Sem {semester} Section {section} ({shift}) | Teacher: {teacher}")
    
    print("\n" + "="*60)
    print("CLEANUP INSTRUCTIONS")
    print("="*60)
    print("\nFor each subject group above:")
    print("1. Decide which semester the subject SHOULD belong to")
    print("2. Go to Admin > Subjects")
    print("3. Find and DELETE the subject from the WRONG semesters")
    print("\nExample:")
    print("  If 'Advanced Database' should ONLY be in Semester 4:")
    print("  → DELETE: ID 118 and ID 119 (the Sem 3 versions)")
    print("  → KEEP: ID 120 (the Sem 4 version)")
    
else:
    print("\n✅ No cross-semester duplicates found!")
    print("   All subjects are unique to their semesters.")

# Show subject count per semester
print("\n" + "="*60)
print("SUBJECT COUNT PER SEMESTER")
print("="*60)

cur.execute("""
    SELECT c.year, c.semester, 
           COUNT(DISTINCT s.id) as total_subjects,
           COUNT(DISTINCT s.name) as unique_names
    FROM classes c
    LEFT JOIN subjects s ON c.id = s.class_id
    GROUP BY c.year, c.semester
    ORDER BY c.year, c.semester
""")

for row in cur.fetchall():
    year, semester, total, unique = row
    status = "✓" if total == unique and total <= 5 else "⚠️"
    print(f"{status} Year {year} Sem {semester}: {total} total subjects, {unique} unique names")

print("\n💡 Goal: Each semester should have exactly 5 unique subjects")
print("   (Same subject can appear in multiple sections of same semester)")

cur.close()
conn.close()

print("\n" + "="*60)
print("✅ VALIDATION ALREADY ADDED TO PREVENT FUTURE DUPLICATES")
print("="*60)
print("\nThe system now prevents assigning subjects to classes")
print("from different semesters. Just clean up the existing duplicates!")
