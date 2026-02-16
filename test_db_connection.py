"""Test database connection and show admin credentials"""
import pg8000
from config import config
import sys

print("=" * 50)
print("DATABASE CONNECTION TEST")
print("=" * 50)

print(f"\nConnection Details:")
print(f"  Host: {config.DB_HOST}")
print(f"  Port: {config.DB_PORT}")
print(f"  Database: {config.DB_NAME}")
print(f"  User: {config.DB_USER}")

try:
    # Try to connect
    conn = pg8000.connect(
        host=config.DB_HOST,
        port=int(config.DB_PORT),
        database=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD
    )
    
    print("\n✓ DATABASE CONNECTION SUCCESSFUL!")
    
    # Check for admin user
    cur = conn.cursor()
    cur.execute("SELECT username, full_name, role, email FROM users WHERE role = 'admin'")
    admins = cur.fetchall()
    
    print(f"\n{'=' * 50}")
    print("ADMIN USERS IN DATABASE")
    print("=" * 50)
    
    if admins:
        for admin in admins:
            print(f"\n  Username: {admin[0]}")
            print(f"  Full Name: {admin[1]}")
            print(f"  Role: {admin[2]}")
            print(f"  Email: {admin[3]}")
    else:
        print("\n  No admin users found in database!")
        print("  You may need to run init_db.py to create default admin")
    
    # Get database statistics
    print(f"\n{'=' * 50}")
    print("DATABASE STATISTICS")
    print("=" * 50)
    
    cur.execute('SELECT COUNT(*) FROM users')
    print(f"\n  Total Users: {cur.fetchone()[0]}")
    
    cur.execute('SELECT COUNT(*) FROM students')
    print(f"  Total Students: {cur.fetchone()[0]}")
    
    cur.execute('SELECT COUNT(*) FROM teachers')
    print(f"  Total Teachers: {cur.fetchone()[0]}")
    
    cur.execute('SELECT COUNT(*) FROM subjects')
    print(f"  Total Subjects: {cur.fetchone()[0]}")
    
    conn.close()
    
    print(f"\n{'=' * 50}")
    print("DEFAULT ADMIN CREDENTIALS")
    print("=" * 50)
    print("\n  Username: admin")
    print("  Password: admin123")
    print("\n  (Change this password after first login!)")
    print("=" * 50)
    
except pg8000.exceptions.DatabaseError as e:
    print(f"\n✗ DATABASE CONNECTION FAILED!")
    print(f"\nError: {e}")
    print("\nPossible issues:")
    print("  1. PostgreSQL server is not running")
    print("  2. Database 'mis_system' does not exist")
    print("  3. Incorrect username or password")
    print("  4. PostgreSQL is not listening on specified host/port")
    print("\nTo fix:")
    print("  1. Make sure PostgreSQL is running")
    print("  2. Create database: CREATE DATABASE mis_system;")
    print("  3. Run: python init_db.py")
    sys.exit(1)
    
except Exception as e:
    print(f"\n✗ UNEXPECTED ERROR!")
    print(f"\nError: {e}")
    sys.exit(1)
