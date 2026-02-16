import db

print("=" * 60)
print("CHECKING teacher_assignments TABLE")
print("=" * 60)

# Check if teacher_assignments table exists and its structure
columns_query = """
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'teacher_assignments'
ORDER BY ordinal_position
"""
columns = db.execute_query(columns_query, fetch_all=True)

if columns:
    print("\n✓ teacher_assignments table EXISTS")
    print("\nColumns:")
    for c in columns:
        nullable = "NULL" if c['is_nullable'] == 'YES' else "NOT NULL"
        print(f"  - {c['column_name']:30} {c['data_type']:20} {nullable}")
    
    # Get data from this table
    data_query = "SELECT * FROM teacher_assignments"
    data = db.execute_query(data_query, fetch_all=True)
    
    print(f"\nRows in teacher_assignments: {len(data)}")
    
    if len(data) > 0:
        print("\nData:")
        for row in data:
            print(f"  {row}")
    else:
        print("\n⚠️  Table is EMPTY!")
else:
    print("\n✗ teacher_assignments table does NOT exist or has no columns")

print("\n" + "=" * 60)
print("CHECKING semester_subjects TABLE")
print("=" * 60)

# Check semester_subjects table
columns_query2 = """
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'semester_subjects'
ORDER BY ordinal_position
"""
columns2 = db.execute_query(columns_query2, fetch_all=True)

if columns2:
    print("\n✓ semester_subjects table EXISTS")
    print("\nColumns:")
    for c in columns2:
        nullable = "NULL" if c['is_nullable'] == 'YES' else "NOT NULL"
        print(f"  - {c['column_name']:30} {c['data_type']:20} {nullable}")
    
    # Get data
    data_query2 = "SELECT * FROM semester_subjects LIMIT 10"
    data2 = db.execute_query(data_query2, fetch_all=True)
    
    print(f"\nSample rows (first 10):")
    for row in data2:
        print(f"  {row}")
else:
    print("\n✗ semester_subjects table does NOT exist")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("\nThe MAIN table for subject-teacher assignments is:")
print("  → 'subjects' table")
print("    - teacher_id column: stores theory teacher")
print("    - practical_teacher_id column: stores practical teacher")
print("\nThese tables might be from an old schema version:")
print("  → teacher_assignments (empty)")
print("  → semester_subjects (might be old design)")
