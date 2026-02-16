"""
Fix teacher_assignments table to include class_id and section
"""
import db

conn = db.get_db_connection()
if not conn:
    print("❌ Failed to connect to database")
    exit(1)

cur = conn.cursor()

print("=" * 70)
print("FIXING TEACHER_ASSIGNMENTS TABLE")
print("=" * 70)

try:
    # Check if table exists
    print("\n1. Checking if teacher_assignments table exists...")
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'teacher_assignments'
        )
    """)
    table_exists = cur.fetchone()[0]
    
    if not table_exists:
        print("   ❌ teacher_assignments table doesn't exist!")
        print("   Creating table with correct structure...")
        cur.execute("""
            CREATE TABLE teacher_assignments (
                id SERIAL PRIMARY KEY,
                teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
                subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
                class_id INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
                shift VARCHAR(10) NOT NULL CHECK (shift IN ('morning', 'night')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(teacher_id, subject_id, class_id)
            )
        """)
        conn.commit()
        print("   ✓ Created teacher_assignments table")
    else:
        print("   ✓ Table exists")
        
        # Check columns
        print("\n2. Checking table structure...")
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'teacher_assignments'
            ORDER BY ordinal_position
        """)
        columns = cur.fetchall()
        column_names = [c[0] for c in columns]
        print(f"   Current columns: {', '.join(column_names)}")
        
        # Add missing columns if needed
        modified = False
        if 'class_id' not in column_names:
            print("\n3. Adding class_id column...")
            cur.execute("""
                ALTER TABLE teacher_assignments 
                ADD COLUMN class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE
            """)
            conn.commit()
            print("   ✓ Added class_id column")
            modified = True
        else:
            print("\n3. class_id column exists")
        
        # Remove old section column if it exists (it's derived from class)
        if 'section' in column_names:
            print("\n4. Removing redundant section column...")
            cur.execute("""
                ALTER TABLE teacher_assignments 
                DROP COLUMN IF EXISTS section
            """)
            conn.commit()
            print("   ✓ Removed section column (will be derived from class_id)")
    
    # Show current data
    print("\n5. Current teacher assignments...")
    cur.execute("""
        SELECT COUNT(*) FROM teacher_assignments
    """)
    count = cur.fetchone()[0]
    print(f"   Total assignments: {count}")
    
    if count > 0:
        print("\n6. Sample data:")
        cur.execute("""
            SELECT 
                ta.id,
                u.full_name as teacher,
                s.name as subject,
                c.section as class_section,
                c.shift,
                c.semester
            FROM teacher_assignments ta
            JOIN teachers t ON ta.teacher_id = t.id
            JOIN users u ON t.user_id = u.id
            JOIN subjects s ON ta.subject_id = s.id
            JOIN classes c ON ta.class_id = c.id
            ORDER BY s.name, c.section
            LIMIT 15
        """)
        rows = cur.fetchall()
        for row in rows:
            print(f"   {row[0]:3d}. {row[2]:<30} | {row[1]:<25} | Sem{row[5]} {row[4]:^6} Section {row[3]}")
    
    print("\n" + "=" * 70)
    print("✅ COMPLETED!")
    print("=" * 70)
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    cur.close()
    conn.close()
