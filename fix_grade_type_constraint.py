"""
Fix the grade_type CHECK constraint to include new types
"""
import pg8000
from config import config

def fix_constraint():
    try:
        conn = pg8000.connect(
            host=config.DB_HOST,
            port=int(config.DB_PORT),
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        cur = conn.cursor()
        
        print("Dropping old constraint...")
        cur.execute("ALTER TABLE grades DROP CONSTRAINT IF EXISTS grades_grade_type_check;")
        
        print("Adding new constraint with expanded types...")
        cur.execute("""
            ALTER TABLE grades 
            ADD CONSTRAINT grades_grade_type_check 
            CHECK (grade_type IN ('quiz', 'exam', 'homework', 'midterm', 'final', 'project', 'activity', 'report', 'seminar', 'lab_report'));
        """)
        
        conn.commit()
        print("✓ Constraint updated successfully!")
        print("New allowed types: quiz, exam, homework, midterm, final, project, activity, report, seminar, lab_report")
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()

if __name__ == '__main__':
    fix_constraint()
