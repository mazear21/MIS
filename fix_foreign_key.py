"""
Fix teacher_assignments foreign key to point to subjects table instead of semester_subjects
"""
from db import get_db_connection

print("="*60)
print("FIXING TEACHER_ASSIGNMENTS FOREIGN KEY")
print("="*60)

conn = get_db_connection()
cur = conn.cursor()

try:
    # Step 1: Drop the old foreign key constraint
    print("\n1. Dropping old foreign key constraint...")
    cur.execute("""
        ALTER TABLE teacher_assignments 
        DROP CONSTRAINT IF EXISTS teacher_assignments_subject_id_fkey
    """)
    print("   ✓ Old constraint dropped")
    
    # Step 2: Add new foreign key constraint pointing to subjects table
    print("\n2. Adding new foreign key constraint to subjects table...")
    cur.execute("""
        ALTER TABLE teacher_assignments 
        ADD CONSTRAINT teacher_assignments_subject_id_fkey 
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
    """)
    print("   ✓ New constraint added")
    
    conn.commit()
    
    # Verify the change
    print("\n3. Verifying new constraint...")
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
    
    print("   Current foreign keys:")
    for row in cur.fetchall():
        print(f"     {row[0]}: {row[1]} -> {row[2]}.{row[3]}")
    
    print("\n" + "="*60)
    print("✅ FOREIGN KEY FIXED SUCCESSFULLY!")
    print("="*60)
    print("\nNow teacher_assignments.subject_id -> subjects.id")
    print("Ready to run migration!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    conn.rollback()
finally:
    cur.close()
    conn.close()
