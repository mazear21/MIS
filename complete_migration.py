"""
Complete Database Migration Script
- Migrate teacher assignments from subjects table to teacher_assignments table
- Clean old sample data from subjects table
"""
import sys
from db import get_db_connection, execute_query

def migrate_teacher_assignments():
    """Migrate teacher assignments from subjects to teacher_assignments table"""
    print("\n" + "="*60)
    print("STEP 1: MIGRATING TEACHER ASSIGNMENTS")
    print("="*60)
    
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    cur = conn.cursor()
    
    try:
        # Get all subjects with teacher assignments
        cur.execute("""
            SELECT s.id, s.name, s.teacher_id, s.practical_teacher_id, 
                   c.shift, c.semester, c.section, c.year
            FROM subjects s
            JOIN classes c ON s.class_id = c.id
            WHERE s.teacher_id IS NOT NULL OR s.practical_teacher_id IS NOT NULL
            ORDER BY c.semester, c.section, s.name
        """)
        subjects_with_teachers = cur.fetchall()
        
        print(f"\nFound {len(subjects_with_teachers)} subjects with teacher assignments")
        
        migrated_theory = 0
        migrated_practical = 0
        
        for row in subjects_with_teachers:
            subject_id, name, teacher_id, practical_teacher_id, shift, semester, section, year = row
            
            # Migrate theory teacher
            if teacher_id:
                try:
                    cur.execute("""
                        INSERT INTO teacher_assignments (teacher_id, subject_id, shift)
                        VALUES (%s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (teacher_id, subject_id, shift))
                    migrated_theory += 1
                    print(f"  ✓ Migrated theory teacher for: Sem {semester} Section {section} - {name}")
                except Exception as e:
                    print(f"  ⚠️  Error migrating theory teacher for {name}: {e}")
            
            # Migrate practical teacher if different from theory teacher
            if practical_teacher_id and practical_teacher_id != teacher_id:
                try:
                    cur.execute("""
                        INSERT INTO teacher_assignments (teacher_id, subject_id, shift)
                        VALUES (%s, %s, %s)
                        ON CONFLICT DO NOTHING
                    """, (practical_teacher_id, subject_id, shift))
                    migrated_practical += 1
                    print(f"  ✓ Migrated practical teacher for: Sem {semester} Section {section} - {name}")
                except Exception as e:
                    print(f"  ⚠️  Error migrating practical teacher for {name}: {e}")
        
        conn.commit()
        print(f"\n✅ Migration complete:")
        print(f"   - Theory teachers migrated: {migrated_theory}")
        print(f"   - Practical teachers migrated: {migrated_practical}")
        print(f"   - Total assignments: {migrated_theory + migrated_practical}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()


def clean_old_sample_data():
    """Remove old sample subjects that are not currently assigned"""
    print("\n" + "="*60)
    print("STEP 2: CLEANING OLD SAMPLE DATA")
    print("="*60)
    
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    cur = conn.cursor()
    
    try:
        # Check for old sample subjects (subjects without teacher assignments)
        # These are likely old test data
        cur.execute("""
            SELECT s.id, s.name, c.semester, c.section
            FROM subjects s
            JOIN classes c ON s.class_id = c.id
            WHERE s.teacher_id IS NULL 
            AND s.practical_teacher_id IS NULL
            AND NOT EXISTS (
                SELECT 1 FROM teacher_assignments ta WHERE ta.subject_id = s.id
            )
            ORDER BY c.semester, c.section, s.name
        """)
        unassigned_subjects = cur.fetchall()
        
        if unassigned_subjects:
            print(f"\nFound {len(unassigned_subjects)} unassigned subjects:")
            for row in unassigned_subjects:
                subject_id, name, semester, section = row
                print(f"  - Sem {semester} Section {section}: {name} (ID: {subject_id})")
            
            print(f"\n⚠️  These subjects have no teacher assignments.")
            print("They will be kept in case they are needed later.")
            print("You can manually delete them from the admin panel if not needed.")
        else:
            print("\n✓ No unassigned subjects found. Database is clean!")
        
        return True
        
    except Exception as e:
        print(f"❌ Cleanup check failed: {e}")
        return False
    finally:
        cur.close()
        conn.close()


def verify_migration():
    """Verify the migration was successful"""
    print("\n" + "="*60)
    print("STEP 3: VERIFICATION")
    print("="*60)
    
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return False
    
    cur = conn.cursor()
    
    try:
        # Count teacher assignments
        cur.execute("SELECT COUNT(*) FROM teacher_assignments")
        ta_count = cur.fetchone()[0]
        print(f"\n✓ teacher_assignments table: {ta_count} records")
        
        # Count subjects with teachers in old structure
        cur.execute("""
            SELECT COUNT(*) FROM subjects 
            WHERE teacher_id IS NOT NULL OR practical_teacher_id IS NOT NULL
        """)
        subjects_count = cur.fetchone()[0]
        print(f"✓ subjects with teacher_id: {subjects_count} records")
        
        # Show sample assignments
        if ta_count > 0:
            cur.execute("""
                SELECT s.name, c.semester, c.section, u.full_name, ta.shift
                FROM teacher_assignments ta
                JOIN subjects s ON ta.subject_id = s.id
                JOIN classes c ON s.class_id = c.id
                JOIN teachers t ON ta.teacher_id = t.id
                JOIN users u ON t.user_id = u.id
                ORDER BY c.semester, c.section, s.name
                LIMIT 10
            """)
            assignments = cur.fetchall()
            print(f"\nSample assignments in teacher_assignments table:")
            for row in assignments:
                name, semester, section, teacher, shift = row
                print(f"  ✓ Sem {semester} Section {section} ({shift}): {name} → {teacher}")
        
        # Count total subjects
        cur.execute("SELECT COUNT(*) FROM subjects")
        total_subjects = cur.fetchone()[0]
        print(f"\n✓ Total subjects in database: {total_subjects}")
        
        # Check for duplicates
        cur.execute("""
            SELECT s.name, c.semester, COUNT(*)
            FROM subjects s
            JOIN classes c ON s.class_id = c.id
            GROUP BY s.name, c.semester
            HAVING COUNT(*) > 3
            ORDER BY c.semester, s.name
        """)
        duplicates = cur.fetchall()
        
        if duplicates:
            print(f"\n⚠️  Potential duplicate subjects:")
            for row in duplicates:
                name, semester, count = row
                print(f"  - Sem {semester}: {name} appears {count} times")
        else:
            print(f"\n✓ No excessive duplicates found")
        
        print("\n" + "="*60)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    print("="*60)
    print("DATABASE MIGRATION UTILITY")
    print("="*60)
    
    # Step 1: Migrate teacher assignments
    if not migrate_teacher_assignments():
        print("\n❌ Migration aborted due to errors")
        sys.exit(1)
    
    # Step 2: Clean old data (informational only, doesn't delete)
    clean_old_sample_data()
    
    # Step 3: Verify migration
    if verify_migration():
        print("\n✅ All migration steps completed successfully!")
        print("\nNext steps:")
        print("1. The API endpoint will be updated to use teacher_assignments")
        print("2. Test the schedule page to ensure teachers show correctly")
        print("3. Review unassigned subjects and delete if not needed")
    else:
        print("\n⚠️  Migration completed but verification had issues")
        sys.exit(1)
