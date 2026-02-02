"""Test user login functionality"""
from werkzeug.security import check_password_hash
import db

# Test with a sample student
username = "std101"
password = "student123"

print(f"Testing login for: {username}")
print(f"Password: {password}\n")

user = db.get_user_by_username(username)

if user:
    print(f"User found!")
    print(f"  ID: {user['id']}")
    print(f"  Username: {user['username']}")
    print(f"  Full Name: {user['full_name']}")
    print(f"  Role: {user['role']}")
    print(f"  Password Hash: {user['password_hash'][:50]}...")
    print()
    
    # Check password
    if check_password_hash(user['password_hash'], password):
        print("✓ Password is CORRECT!")
    else:
        print("✗ Password is INCORRECT!")
else:
    print("User not found!")

print("\n" + "="*50)
print("Testing with another student...")
print("="*50 + "\n")

username = "alo"
password = "student123"

print(f"Testing login for: {username}")
print(f"Password: {password}\n")

user = db.get_user_by_username(username)

if user:
    print(f"User found!")
    print(f"  ID: {user['id']}")
    print(f"  Username: {user['username']}")
    print(f"  Full Name: {user['full_name']}")
    print(f"  Role: {user['role']}")
    print(f"  Password Hash: {user['password_hash'][:50]}...")
    print()
    
    # Check password
    if check_password_hash(user['password_hash'], password):
        print("✓ Password is CORRECT!")
    else:
        print("✗ Password is INCORRECT!")
        
        # Try different passwords
        test_passwords = ["123456", "password", "123", "ali", "alo123"]
        print("\nTrying common passwords:")
        for pwd in test_passwords:
            if check_password_hash(user['password_hash'], pwd):
                print(f"  ✓ Password is: {pwd}")
                break
        else:
            print("  None of the common passwords worked")
else:
    print("User not found!")
