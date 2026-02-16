import db

subjects = db.execute_query('SELECT id, name, semester FROM subjects ORDER BY name, semester', fetch_all=True)
print('\nCurrent subjects in database:')
print('='*60)
for s in subjects:
    print(f"ID {s['id']:3d}: {s['name']:30s} - Semester {s['semester']}")

print('\n' + '='*60)
print(f"Total subjects: {len(subjects)}")

# Check for cross-semester duplicates
from collections import defaultdict
names = defaultdict(list)
for s in subjects:
    names[s['name']].append(s['semester'])

duplicates = {name: sems for name, sems in names.items() if len(set(sems)) > 1}
if duplicates:
    print(f"\n⚠️  WARNING: Found {len(duplicates)} subjects in multiple semesters:")
    for name, sems in duplicates.items():
        print(f"  - {name}: Semesters {sorted(set(sems))}")
else:
    print("\n✅ No cross-semester duplicates found!")
