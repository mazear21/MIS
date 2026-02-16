"""
Major Schema Migration V3: Restructure Subjects System
- Make subjects general definitions (remove class_id)
- Move class associations to teacher_assignments
- Consolidate duplicate subjects
"""
from db import get_db_connection
import sys

def migrate_schema():
    print("="*60)
    print("SCHEMA MIGRATION V3: SUBJECTS RESTRUCTURING")
    print("="*60)
    
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    cur = conn.cursor()
    
    try:
        # STEP 1: Add class_id to teacher_assignments
        print("\n📋 Step 1: Adding class_id to teacher_assignments...")
        cur.execute("""
            ALTER TABLE teacher_assignments 
            ADD COLUMN IF NOT EXISTS class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE
        """)
        print("   ✓ Column added")
        
        # STEP 2: Drop old unique constraint FIRST before migrating data
        print("\n📋 Step 2: Dropping old unique constraint...")
        try:
            cur.execute("""
                ALTER TABLE teacher_assignments 
                DROP CONSTRAINT IF EXISTS teacher_assignments_teacher_id_subject_id_shift_key
            """)
            print("   ✓ Dropped old unique constraint")
        except Exception as e:
            print(f"   Note: {e}")
        
        # STEP 3: Migrate class_id from subjects to teacher_assignments
        print("\n📋 Step 3: Migrating class associations to teacher_assignments...")
        cur.execute("""
            UPDATE teacher_assignments ta
            SET class_id = s.class_id
            FROM subjects s
            WHERE ta.subject_id = s.id
            AND ta.class_id IS NULL
        """)
        updated = cur.rowcount
        print(f"   ✓ Updated {updated} teacher assignment records")
        
        # STEP 4: Consolidate duplicate subjects
        print("\n📋 Step 4: Consolidating duplicate subjects...")
        
        # Get all unique subject names
        cur.execute("SELECT DISTINCT name FROM subjects ORDER BY name")
        subject_names = [row[0] for row in cur.fetchall()]
        
        consolidated = 0
        for name in subject_names:
            # Find all subjects with this name
            cur.execute("""
                SELECT id, class_id, description, created_at
                FROM subjects 
                WHERE name = %s
                ORDER BY created_at
            """, (name,))
            duplicates = cur.fetchall()
            
            if len(duplicates) > 1:
                # Keep the first one (oldest)
                master_id = duplicates[0][0]
                master_desc = duplicates[0][2] or ''
                
                # Update all teacher_assignments pointing to duplicates to point to master
                for dup in duplicates[1:]:
                    dup_id = dup[0]
                    
                    try:
                        # Update teacher_assignments references
                        cur.execute("""
                            UPDATE teacher_assignments 
                            SET subject_id = %s 
                            WHERE subject_id = %s
                        """, (master_id, dup_id))
                        print(f"      Updated TA: {dup_id} → {master_id}")
                    except Exception as e:
                        print(f"      ⚠️  Error updating TA for subject {dup_id}: {e}")
                        raise  # Re-raise to see full error
                    
                    # Delete the duplicate (other tables have CASCADE delete)
                    try:
                        cur.execute("DELETE FROM subjects WHERE id = %s", (dup_id,))
                        print(f"      Deleted duplicate subject {dup_id}")
                    except Exception as e:
                        print(f"      ⚠️  Error deleting subject {dup_id}: {e}")
                        raise
                    consolidated += 1
                
                # Update master subject to have best description
                if master_desc:
                    cur.execute("""
                        UPDATE subjects 
                        SET description = %s 
                        WHERE id = %s
                    """, (master_desc, master_id))
                
                print(f"   ✓ Consolidated '{name}': {len(duplicates)} → 1 (kept ID {master_id})")
        
        print(f"\n   ✓ Total duplicates consolidated: {consolidated}")
        
        # STEP 5: Remove class_id from subjects
        print("\n📋 Step 5: Removing class_id from subjects table...")
        cur.execute("ALTER TABLE subjects DROP COLUMN IF EXISTS class_id")
        print("   ✓ class_id column removed from subjects")
        
        # STEP 6: Make class_id required in teacher_assignments and add new unique constraint
        print("\n📋 Step 6: Updating teacher_assignments constraints...")
        cur.execute("ALTER TABLE teacher_assignments ALTER COLUMN class_id SET NOT NULL")
        cur.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS teacher_assignments_unique_idx 
            ON teacher_assignments(teacher_id, subject_id, class_id)
        """)
        print("   ✓ class_id is now required")
        print("   ✓ New unique constraint: (teacher_id, subject_id, class_id)")
        
        conn.commit()
        
        # STEP 7: Verify the migration
        print("\n📋 Step 7: Verifying migration...")
        
        cur.execute("SELECT COUNT(*) FROM subjects")
        subject_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM teacher_assignments")
        ta_count = cur.fetchone()[0]
        
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'subjects'
            ORDER BY ordinal_position
        """)
        subject_columns = [row[0] for row in cur.fetchall()]
        
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'teacher_assignments'
            ORDER BY ordinal_position
        """)
        ta_columns = [row[0] for row in cur.fetchall()]
        
        print(f"\n   ✓ Subjects table: {subject_count} unique records")
        print(f"     Columns: {', '.join(subject_columns)}")
        print(f"\n   ✓ Teacher assignments: {ta_count} records")
        print(f"     Columns: {', '.join(ta_columns)}")
        
        # Show sample data
        print("\n📋 Sample subjects (general definitions):")
        cur.execute("SELECT id, name, description FROM subjects ORDER BY name LIMIT 5")
        for row in cur.fetchall():
            desc = row[2][:50] + '...' if row[2] and len(row[2]) > 50 else (row[2] or 'No description')
            print(f"   ID {row[0]}: {row[1]} - {desc}")
        
        print("\n📋 Sample teacher assignments (with class):")
        cur.execute("""
            SELECT ta.id, s.name, c.year, c.semester, c.section, u.full_name
            FROM teacher_assignments ta
            JOIN subjects s ON ta.subject_id = s.id
            JOIN classes c ON ta.class_id = c.id
            JOIN teachers t ON ta.teacher_id = t.id
            JOIN users u ON t.user_id = u.id
            ORDER BY s.name, c.semester, c.section
            LIMIT 5
        """)
        for row in cur.fetchall():
            ta_id, subj, year, sem, sec, teacher = row
            print(f"   {subj} → Year {year} Sem {sem} Sec {sec} → {teacher}")
        
        print("\n" + "="*60)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nNew structure:")
        print("  • Subjects = General definitions (no duplicates)")
        print("  • Teacher_assignments = Links teacher + subject + class")
        print("  • Same subject can be taught by different teachers in different classes")
        print("\nNext: Update application code to use new structure")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    print("\n⚠️  WARNING: This will restructure the subjects system!")
    print("Make sure you have a database backup before proceeding.\n")
    
    response = input("Continue with migration? (yes/no): ")
    if response.lower() == 'yes':
        if migrate_schema():
            print("\n✅ Migration successful! Now update the application code.")
            sys.exit(0)
        else:
            print("\n❌ Migration failed!")
            sys.exit(1)
    else:
        print("\n❌ Migration cancelled.")
        sys.exit(1)
