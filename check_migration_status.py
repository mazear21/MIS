from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

print("Checking teacher_assignments structure...")
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'teacher_assignments' ORDER BY ordinal_position")
cols = [row[0] for row in cur.fetchall()]
print(f"Columns: {', '.join(cols)}")

print("\nChecking if class_id already exists...")
if 'class_id' in cols:
    print("✓ class_id already added!")
    cur.execute("SELECT COUNT(*) FROM teacher_assignments WHERE class_id IS NOT NULL")
    count = cur.fetchone()[0]
    print(f"✓{count} records have class_id")
    
    # Check for duplicates that would violate new constraint
    print("\nChecking for duplicate assignments...")
    cur.execute("""
        SELECT teacher_id, subject_id, class_id, COUNT(*)
        FROM teacher_assignments
        GROUP BY teacher_id, subject_id, class_id
        HAVING COUNT(*) > 1
    """)
    dups = cur.fetchall()
    if dups:
        print(f"⚠️  Found {len(dups)} duplicate assignments!")
        for dup in dups:
            print(f"   Teacher {dup[0]}, Subject {dup[1]}, Class {dup[2]}: {dup[3]} times")
    else:
        print("✓ No duplicates found")
else:
    print("✗ class_id not yet added")

cur.close()
conn.close()
