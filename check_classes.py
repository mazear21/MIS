import db

classes = db.get_all_classes()
print("All classes:")
for c in classes:
    print(f"  {c['id']}: {c['name']} - Year {c['year']}, Sem {c['semester']}, Section {c['section']}, {c['shift']}")
