import db

conn = db.get_db_connection()
cur = conn.cursor()

print("=== All Tables in Database ===")
cur.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")
tables = cur.fetchall()
for t in tables:
    print(f"  - {t[0]}")

print("\n=== Checking for teacher_assignments table ===")
cur.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'teacher_assignments'
    )
""")
exists = cur.fetchone()[0]
print(f"teacher_assignments exists: {exists}")

if exists:
    print("\n=== teacher_assignments columns ===")
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'teacher_assignments'
        ORDER BY ordinal_position
    """)
    for col in cur.fetchall():
        print(f"  - {col[0]}: {col[1]}")
    
    print("\n=== Sample data from teacher_assignments ===")
    cur.execute("SELECT COUNT(*) FROM teacher_assignments")
    count = cur.fetchone()[0]
    print(f"Total rows: {count}")
    
    if count > 0:
        cur.execute("""
            SELECT ta.id, ta.subject_id, s.name as subject_name, 
                   ta.class_id, c.section, c.shift,
                   t.id as teacher_id, u.full_name as teacher_name
            FROM teacher_assignments ta
            JOIN subjects s ON ta.subject_id = s.id
            JOIN classes c ON ta.class_id = c.id
            JOIN teachers t ON ta.teacher_id = t.id
            JOIN users u ON t.user_id = u.id
            LIMIT 10
        """)
        print("\nFirst 10 assignments:")
        for row in cur.fetchall():
            print(f"  Assignment {row[0]}: {row[2]} (subj_id={row[1]}) to {row[7]} (teacher_id={row[6]}) - Class: {row[4]} {row[5]}")

cur.close()
conn.close()
