import db

# Check student counts by class_id
result = db.execute_query("""
    SELECT c.id, c.semester, c.shift, c.section, COUNT(s.id) as student_count
    FROM classes c
    LEFT JOIN students s ON c.id = s.class_id
    GROUP BY c.id, c.semester, c.shift, c.section
    ORDER BY student_count DESC
""", fetch_all=True)

print("Students per class:")
print("-" * 60)
for r in result:
    print(f"Class ID {r['id']:2d} | Sem {r['semester']} {r['shift']:7s} {r['section']} | {r['student_count']:2d} students")

print("\n" + "=" * 60)
print("Class counts dictionary:")
counts = db.get_class_student_counts()
for key, value in sorted(counts.items()):
    print(f"{key}: {value}")
