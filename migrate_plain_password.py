"""
Add plain_password column to users table
Run this script to migrate the database
"""
import db

def add_plain_password_column():
    """Add plain_password column to users table"""
    try:
        # Add column
        db.execute_query("ALTER TABLE users ADD COLUMN IF NOT EXISTS plain_password VARCHAR(255)")
        print("✓ Added plain_password column to users table")
        
        # Update admin password
        db.execute_query(
            "UPDATE users SET plain_password = 'admin123' WHERE username = 'admin' AND plain_password IS NULL"
        )
        print("✓ Set default password for admin user")
        
        # Update teacher passwords
        db.execute_query(
            "UPDATE users SET plain_password = 'password123' WHERE role = 'teacher' AND plain_password IS NULL"
        )
        print("✓ Set default password for teacher users")
        
        # Update student passwords  
        db.execute_query(
            "UPDATE users SET plain_password = 'password123' WHERE role = 'student' AND plain_password IS NULL"
        )
        print("✓ Set default password for student users")
        
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")

if __name__ == '__main__':
    print("Running database migration: add plain_password column\n")
    add_plain_password_column()
