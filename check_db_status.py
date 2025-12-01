"""Check current database status for new structure"""
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

print('=== DATABASE STATUS ===')
cur.execute('SELECT COUNT(*) FROM students')
print(f'Total Students: {cur.fetchone()[0]}')

cur.execute('SELECT COUNT(*) FROM students WHERE year IS NOT NULL')
print(f'Students with Year: {cur.fetchone()[0]}')

cur.execute('SELECT COUNT(*) FROM students WHERE section IS NOT NULL')
print(f'Students with Section: {cur.fetchone()[0]}')

cur.execute('SELECT COUNT(*) FROM students WHERE section IS NULL')
print(f'Students WITHOUT Section: {cur.fetchone()[0]}')

print('\n=== STUDENT DISTRIBUTION ===')
cur.execute('''
    SELECT year, shift, section, COUNT(*) as cnt 
    FROM students 
    GROUP BY year, shift, section 
    ORDER BY year, shift, section
''')
for r in cur.fetchall():
    section = r[2] if r[2] else 'Not Assigned'
    print(f'  Year {r[0]}, {r[1]}, Section {section}: {r[3]} students')

print('\n=== TABLES STATUS ===')
cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'semester_subjects')")
print(f'semester_subjects exists: {cur.fetchone()[0]}')

cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'teacher_assignments')")
print(f'teacher_assignments exists: {cur.fetchone()[0]}')

conn.close()
print('\nDone!')
