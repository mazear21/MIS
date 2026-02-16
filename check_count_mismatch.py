import db

# Check for mismatches between student table columns and class_id reference
query = """
    SELECT 
        s.id, 
        s.semester, 
        s.shift, 
        s.section, 
        s.class_id,
        c.semester as c_sem, 
        c.shift as c_shift, 
        c.section as c_sec
    FROM students s
    LEFT JOIN classes c ON s.class_id = c.id
    WHERE s.semester = 1 AND s.shift = 'morning' AND s.section = 'A'
    ORDER BY s.id
"""

result = db.execute_query(query, fetch_all=True)

print(f"Students with semester=1, shift='morning', section='A': {len(result)}")
print("\nChecking for mismatches between students columns and class_id reference:\n")

mismatch_count = 0
for r in result:
    if r['class_id'] is None:
        print(f"Student {r['id']}: students(sem={r['semester']},{r['shift']},{r['section']}) but class_id is NULL")
        mismatch_count += 1
    elif r['c_sem'] != r['semester'] or r['c_shift'] != r['shift'] or r['c_sec'] != r['section']:
        print(f"Student {r['id']}: students(sem={r['semester']},{r['shift']},{r['section']}) but class_id {r['class_id']} -> ({r['c_sem']},{r['c_shift']},{r['c_sec']})")
        mismatch_count += 1

if mismatch_count == 0:
    print("✓ All students have matching semester/shift/section and class_id")
else:
    print(f"\n⚠ Found {mismatch_count} mismatches!")

# Now check the count using class_id
count_query = """
    SELECT c.id, c.semester, c.shift, c.section, COUNT(s.id) as student_count
    FROM classes c
    LEFT JOIN students s ON c.id = s.class_id
    WHERE c.semester = 1 AND c.shift = 'morning' AND c.section = 'A'
    GROUP BY c.id, c.semester, c.shift, c.section
"""
count_result = db.execute_query(count_query, fetch_one=True)
print(f"\nCount using class_id join: {count_result['student_count']}")
print(f"Count using semester/shift/section columns: {len(result)}")
