"""Test all manually added students"""
from werkzeug.security import check_password_hash, generate_password_hash
import db

# Get manually added students (not the sample data ones)
manual_students = [
    {"username": "alo", "expected_pass": "student123"},
    {"username": "ali hh", "expected_pass": "student123"},
    {"username": "niga", "expected_pass": "student123"},
    {"username": "mis202500001", "expected_pass": "student123"},
    {"username": "mis202500002", "expected_pass": "student123"},
    {"username": "mis202500003", "expected_pass": "student123"},
    {"username": "mis202600001", "expected_pass": "student123"},
]

print("="*70)
print("TESTING MANUALLY CREATED STUDENT ACCOUNTS")
print("="*70)

for student in manual_students:
    username = student["username"]
    password = student["expected_pass"]
    
    user = db.get_user_by_username(username)
    
    if user:
        is_correct = check_password_hash(user['password_hash'], password)
        status = "✓ WORKS" if is_correct else "✗ BROKEN"
        print(f"\n{status} - Username: {username}")
        print(f"       Email: {user.get('email', 'N/A')}")
        print(f"       Password Hash: {user['password_hash'][:40]}...")
        
        if not is_correct:
            print(f"       → Password '{password}' does NOT match!")
            print(f"       → This user needs password reset in admin panel")
    else:
        print(f"\n? NOT FOUND - Username: {username}")

print("\n" + "="*70)
print("SOLUTION: Use admin panel to reset passwords for broken accounts")
print("Go to Admin → Users → Edit button → Enter new password")
print("="*70)
