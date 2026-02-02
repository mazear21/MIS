"""Check all users in the database"""
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

print('=== ALL USERS ===\n')
cur.execute('SELECT id, username, full_name, role, email FROM users ORDER BY role, id')
for row in cur.fetchall():
    user_id, username, full_name, role, email = row
    print(f'ID: {user_id}')
    print(f'  Username: {username}')
    print(f'  Full Name: {full_name}')
    print(f'  Role: {role}')
    print(f'  Email: {email if email else "N/A"}')
    print()

conn.close()
