import db

print("Checking lecture_files table structure...")
print("=" * 100)

query = """
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'lecture_files'
    ORDER BY ordinal_position
"""

columns = db.execute_query(query, fetch_all=True)

if columns:
    print("\nlecture_files table columns:")
    print("-" * 100)
    print(f"{'Column Name':<30} {'Data Type':<20} {'Nullable':<10}")
    print("-" * 100)
    for col in columns:
        print(f"{col['column_name']:<30} {col['data_type']:<20} {col['is_nullable']:<10}")
    print("-" * 100)
else:
    print("ERROR: lecture_files table does not exist!")

# Check if there are any files in the table
count_query = "SELECT COUNT(*) as count FROM lecture_files"
count = db.execute_query(count_query)
print(f"\nTotal files in database: {count['count'] if count else 0}")

# Show some sample files if they exist
if count and count['count'] > 0:
    sample_query = """
        SELECT id, subject_id, teacher_id, title, file_name, uploaded_at
        FROM lecture_files
        ORDER BY uploaded_at DESC
        LIMIT 5
    """
    files = db.execute_query(sample_query, fetch_all=True)
    print("\nRecent files:")
    print("-" * 100)
    for f in files:
        print(f"ID: {f['id']}, Subject: {f['subject_id']}, Title: {f['title']}, File: {f['file_name']}")
