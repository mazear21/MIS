"""Test if password creation works correctly"""
from werkzeug.security import generate_password_hash, check_password_hash
import db

# Simulate what happens when admin creates a student
test_password = "mypassword123"
test_username = "test_student_temp"

print("="*70)
print("SIMULATING STUDENT CREATION IN ADMIN PANEL")
print("="*70)

# Step 1: Hash the password (what admin panel does)
password_hash = generate_password_hash(test_password)
print(f"\n1. Admin enters password: {test_password}")
print(f"2. System hashes it: {password_hash[:50]}...")

# Step 2: Store in database (simulated)
print(f"3. Stored in database")

# Step 3: Try to login (what login page does)
print(f"\n4. Student tries to login with: {test_password}")
if check_password_hash(password_hash, test_password):
    print("   ✓ LOGIN SUCCESSFUL!")
else:
    print("   ✗ LOGIN FAILED!")

print("\n" + "="*70)
print("Now testing with actual user 'alo'")
print("="*70)

user = db.get_user_by_username("alo")
if user:
    print(f"\nUsername: {user['username']}")
    print(f"Email: {user['email']}")
    print(f"Password Hash: {user['password_hash'][:50]}...")
    
    # Try to figure out what password was used
    test_passwords = [
        "student123",
        "123456",
        "password",
        "123",
        "ali",
        "alo",
        "alo123",
        "admin123",
        "osa106ss",
        "osa106ss@gmail.com",
    ]
    
    print("\nTrying to find the password...")
    found = False
    for pwd in test_passwords:
        if check_password_hash(user['password_hash'], pwd):
            print(f"✓ Found it! Password is: {pwd}")
            found = True
            break
    
    if not found:
        print("✗ Password not in common list")
        print("\nYou need to:")
        print("1. Login as admin")
        print("2. Go to Users → Students tab")
        print("3. Click Edit on 'alo'")
        print("4. Enter a NEW password (e.g., '123456')")
        print("5. Click Save")
        print("6. Then login with username 'alo' and password '123456'")
