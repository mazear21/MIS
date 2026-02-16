import sys
sys.path.insert(0, r'c:\Users\DATA FORCE\OneDrive\Pictures\Screenshots\Desktop\MIS')
import db

# Check students table schema
print("=== STUDENTS TABLE SCHEMA ===")
result = db.execute_query(
    "SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_name = %s ORDER BY ordinal_position",
    ('students',), fetch_all=True
)
for r in result:
    print(r)

# Check constraints
print("\n=== CONSTRAINTS ===")
result = db.execute_query("""
    SELECT tc.constraint_name, tc.constraint_type, kcu.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
    WHERE tc.table_name = 'students'
""", fetch_all=True)
for r in result:
    print(r)

# Check if student_number has unique constraint
print("\n=== INDEXES ===")
result = db.execute_query("""
    SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'students'
""", fetch_all=True)
for r in result:
    print(r)

# Try simulating an insert
print("\n=== TEST INSERT ===")
try:
    from werkzeug.security import generate_password_hash
    import datetime
    current_year = datetime.datetime.now().year
    
    # Check latest student_number
    latest = db.execute_query(
        "SELECT student_number FROM students WHERE student_number LIKE %s ORDER BY student_number DESC LIMIT 1",
        (f'MIS{current_year}%',),
        fetch_one=True
    )
    print(f"Latest student_number: {latest}")
    
    if latest and latest['student_number']:
        try:
            seq = int(latest['student_number'][-5:]) + 1
        except:
            seq = 1
    else:
        seq = 1
    
    student_number = f"MIS{current_year}{seq:05d}"
    username = student_number.lower()
    print(f"Generated: student_number={student_number}, username={username}")
    
    existing = db.get_user_by_username(username)
    print(f"Username exists: {existing is not None}")
    
    # Test create_user
    password_hash = generate_password_hash('test123')
    user_id = db.create_user(username, password_hash, 'Test Student', 'student', None, 'test123')
    print(f"Created user_id: {user_id}")
    
    if user_id:
        # Test create_student_with_semester
        student_id = db.create_student_with_semester(user_id, 1, 1, 'morning', 'A', student_number, None)
        print(f"Created student_id: {student_id}")
        
        # Cleanup
        db.execute_query("DELETE FROM students WHERE id = %s", (student_id,))
        db.execute_query("DELETE FROM users WHERE id = %s", (user_id,))
        print("Cleanup done")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
