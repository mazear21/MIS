"""
Cleanup duplicate records from the database
"""
import pg8000
from config import config

def main():
    conn = pg8000.connect(
        host=config.DB_HOST,
        port=int(config.DB_PORT),
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD
    )
    cur = conn.cursor()

    # Delete duplicate classes (keep IDs 1-11, delete 12+)
    print('Deleting duplicate classes (IDs 12+)...')
    cur.execute('DELETE FROM classes WHERE id > 11')
    conn.commit()
    print(f'  Deleted {cur.rowcount} duplicate classes')

    # Delete duplicate subjects (keep only first of each name per class)
    print('Deleting duplicate subjects...')
    cur.execute('''
        DELETE FROM subjects WHERE id NOT IN (
            SELECT MIN(id) FROM subjects GROUP BY name, class_id
        )
    ''')
    conn.commit()
    print(f'  Deleted {cur.rowcount} duplicate subjects')

    # Verify counts
    print('\n=== FINAL COUNTS ===')
    cur.execute('SELECT COUNT(*) FROM classes')
    print(f'Classes: {cur.fetchone()[0]}')
    cur.execute('SELECT COUNT(*) FROM subjects')
    print(f'Subjects: {cur.fetchone()[0]}')
    cur.execute('SELECT COUNT(*) FROM students')
    print(f'Students: {cur.fetchone()[0]}')
    cur.execute('SELECT COUNT(*) FROM teachers')
    print(f'Teachers: {cur.fetchone()[0]}')

    # Show classes
    print('\n=== ALL CLASSES ===')
    cur.execute('SELECT id, name FROM classes ORDER BY id')
    for r in cur.fetchall():
        print(f'  {r[0]}: {r[1]}')

    conn.close()
    print('\nDone!')

if __name__ == '__main__':
    main()
