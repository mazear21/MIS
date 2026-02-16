"""Check the relationship between subjects, semester_subjects, and teacher_assignments tables"""
from db import get_db_connection

conn = get_db_connection()
cur = conn.cursor()

print("="*60)
print("TABLE RELATIONSHIPS CHECK")
print("="*60)

# Check semester_subjects structure and data
print("\n1. semester_subjects table:")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'semester_subjects'
    ORDER BY ordinal_position
""")
print("Columns:", [row[0] for row in cur.fetchall()])

cur.execute("SELECT id, name, year, semester FROM semester_subjects LIMIT 5")
print("Sample data:")
for row in cur.fetchall():
    print(f"  ID {row[0]}: {row[1]} (Year {row[2]}, Sem {row[3]})")

# Check subjects structure and data  
print("\n2. subjects table:")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'subjects'
    ORDER BY ordinal_position
""")
print("Columns:", [row[0] for row in cur.fetchall()])

cur.execute("""
    SELECT s.id, s.name, c.year, c.semester, s.teacher_id
    FROM subjects s
    JOIN classes c ON s.class_id = c.id
    WHERE s.teacher_id IS NOT NULL
    LIMIT 5
""")
print("Sample data with teachers:")
for row in cur.fetchall():
    print(f"  ID {row[0]}: {row[1]} (Year {row[2]}, Sem {row[3]}) - Teacher ID: {row[4]}")

# Check teacher_assignments constraints
print("\n3. teacher_assignments foreign keys:")
cur.execute("""
    SELECT tc.constraint_name, kcu.column_name, 
           ccu.table_name AS foreign_table,
           ccu.column_name AS foreign_column
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu 
        ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage ccu 
        ON ccu.constraint_name = tc.constraint_name
    WHERE tc.table_name = 'teacher_assignments' 
    AND tc.constraint_type = 'FOREIGN KEY'
""")
for row in cur.fetchall():
    print(f"  {row[0]}: {row[1]} -> {row[2]}.{row[3]}")

# Check what the app is actually using
print("\n4. Which table is the app using?")
cur.execute("SELECT COUNT(*) FROM subjects")
subjects_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM semester_subjects")
semester_subjects_count = cur.fetchone()[0]

print(f"  subjects table: {subjects_count} records")
print(f"  semester_subjects table: {semester_subjects_count} records")

print("\n" + "="*60)
print("ANALYSIS:")
print("="*60)
print("The app uses 'subjects' table (30 records with teacher_id)")
print("But 'teacher_assignments' references 'semester_subjects' (20 old records)")
print("This is a schema mismatch that needs to be fixed!")

cur.close()
conn.close()
