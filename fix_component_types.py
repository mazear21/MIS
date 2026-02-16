import pg8000.native as pg8
from config import Config

config = Config()

conn = pg8.Connection(
    user=config.DB_USER,
    password=config.DB_PASSWORD,
    host=config.DB_HOST,
    port=int(config.DB_PORT),
    database=config.DB_NAME
)

# Drop old constraint
conn.run("ALTER TABLE grade_components DROP CONSTRAINT IF EXISTS grade_components_component_type_check;")

# Add new constraint with seminar and lab_report
conn.run("""
    ALTER TABLE grade_components ADD CONSTRAINT grade_components_component_type_check 
    CHECK (component_type IN ('homework', 'quiz', 'report', 'project', 'exam', 'midterm', 'final', 'lab_report', 'activity', 'seminar'));
""")

print('✓ Database constraint updated! Seminar and Lab Report now supported.')
