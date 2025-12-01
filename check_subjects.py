import db

subjects = db.get_all_subjects()
print(f'Total subjects: {len(subjects)}')
print()

# Group by semester
by_sem = {}
for s in subjects:
    sem = s['semester']
    if sem not in by_sem:
        by_sem[sem] = []
    by_sem[sem].append(s)

# Find and report duplicates
for sem in sorted(by_sem.keys()):
    print(f"=== Semester {sem} ({len(by_sem[sem])} subjects) ===")
    seen_names = {}
    for s in by_sem[sem]:
        name = s['name']
        if name in seen_names:
            print(f"  DUPLICATE: {s['id']}: {name} ({s['class_name']})")
            print(f"    Original: {seen_names[name]['id']}: {name} ({seen_names[name]['class_name']})")
        else:
            seen_names[name] = s
            print(f"  {s['id']}: {name}")
    print()

# Delete duplicates (keep the first one)
dupes = []
for sem in by_sem:
    seen = {}
    for s in by_sem[sem]:
        if s['name'] in seen:
            dupes.append(s['id'])
        else:
            seen[s['name']] = True

if dupes:
    print(f"Duplicate IDs to delete: {dupes}")
    confirm = input("Delete duplicates? (y/n): ")
    if confirm.lower() == 'y':
        for sid in dupes:
            db.delete_subject(sid)
            print(f"Deleted {sid}")
        print("Done!")
else:
    print("No duplicates found!")
