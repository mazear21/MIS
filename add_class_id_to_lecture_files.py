import db

print("Adding class_id column to lecture_files table...")
print("=" * 100)

# Add class_id column
alter_query = """
    ALTER TABLE lecture_files
    ADD COLUMN IF NOT EXISTS class_id INTEGER REFERENCES classes(id) ON DELETE CASCADE
"""

try:
    db.execute_query(alter_query)
    print("✓ Successfully added class_id column to lecture_files table")
except Exception as e:
    print(f"✗ Error adding column: {e}")

# Verify the change
verify_query = """
    SELECT column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name = 'lecture_files' AND column_name = 'class_id'
"""

result = db.execute_query(verify_query, fetch_all=True)

if result:
    print("\n✓ Verification successful:")
    print(f"  Column: {result[0]['column_name']}")
    print(f"  Type: {result[0]['data_type']}")
    print(f"  Nullable: {result[0]['is_nullable']}")
else:
    print("\n✗ Column not found!")

print("\n" + "=" * 100)
print("✓ Migration complete! Now lecture files can be associated with specific classes.")
