import pg8000.native as pg8
from config import config

conn = pg8.Connection(
    user=config.DB_USER,
    password=config.DB_PASSWORD,
    host=config.DB_HOST,
    port=int(config.DB_PORT),
    database=config.DB_NAME
)

with open('database/update_grade_component_types.sql', 'r') as f:
    sql = f.read()
    conn.run(sql)

print('Migration successful! Grade component types updated.')
