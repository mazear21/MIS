"""Check current database status"""
import pg8000
from config import config

conn = pg8000.connect(
    host=config.DB_HOST,
    port=int(config.DB_PORT),
    database=config.DB_NAME,
    user=config.DB_USER,
    password=config.DB_PASSWORD
)
cur = conn.cursor()

# Check student columns
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'students'")
print('Student columns:', [r[0] for r in cur.fetchall()])

# Check if semester_subjects exists
cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'semester_subjects')")
print('semester_subjects table exists:', cur.fetchone()[0])

# Check if teacher_assignments exists
cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'teacher_assignments')")
print('teacher_assignments table exists:', cur.fetchone()[0])

# Check counts
cur.execute('SELECT COUNT(*) FROM students')
print('Students:', cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM classes')
print('Classes:', cur.fetchone()[0])

conn.close()
