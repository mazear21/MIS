"""
Migration script to add component_id field to grades table
This links grades to the grade components created by admin
"""
import pg8000.native
from config import config

def migrate():
    """Add component_id column to grades table"""
    try:
        conn = pg8000.native.Connection(
            host=config.DB_HOST,
            port=int(config.DB_PORT),
            database=config.DB_NAME,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        
        # Check if column already exists
        check_query = """
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='grades' AND column_name='component_id'
        """
        existing = conn.run(check_query)
        
        if existing:
            print("✓ component_id column already exists in grades table")
            conn.close()
            return
        
        # Add component_id column
        alter_query = """
            ALTER TABLE grades 
            ADD COLUMN component_id INTEGER REFERENCES grade_components(id) ON DELETE SET NULL
        """
        conn.run(alter_query)
        
        print("✓ Successfully added component_id column to grades table")
        
        # Show table structure
        info_query = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'grades'
            ORDER BY ordinal_position
        """
        columns = conn.run(info_query)
        print("\nGrades table structure:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        conn.close()
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        raise

if __name__ == '__main__':
    print("Starting migration: Add component_id to grades table...")
    migrate()
    print("\n✓ Migration completed!")
