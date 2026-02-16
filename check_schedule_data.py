import db
import json

print("Checking schedule data for Sem 3 Night Class A...")
print("=" * 100)

schedule_data = db.get_class_schedule_data(3, 'night', 'A')

if schedule_data:
    print(f"\n✓ Schedule data found!")
    print(f"Type: {type(schedule_data)}")
    print(f"Length: {len(schedule_data) if isinstance(schedule_data, list) else 'N/A'}")
    
    if isinstance(schedule_data, list) and len(schedule_data) > 0:
        print(f"\n✓ Schedule has {len(schedule_data)} entries")
        print("\nFirst 3 entries:")
        for i, entry in enumerate(schedule_data[:3], 1):
            print(f"\n  Entry {i}:")
            print(f"    Subject: {entry.get('subject', 'N/A')}")
            print(f"    Teacher: {entry.get('teacher', 'N/A')}")
            print(f"    Row: {entry.get('row')}, Col: {entry.get('col')}")
            print(f"    Is Break: {entry.get('isBreak', False)}")
    else:
        print("\n✗ Schedule data is empty list!")
        print("This means the schedule was saved but has no classes scheduled.")
else:
    print("\n✗ No schedule data found!")
    print("The get_class_schedule_data() returned None")

print("\n" + "=" * 100)
print("\nRaw schedule from database:")
raw_schedule = db.get_schedule(3, 'night', 'A')
if raw_schedule:
    print(f"Semester: {raw_schedule.get('semester')}")
    print(f"Shift: {raw_schedule.get('shift')}")
    print(f"Section: {raw_schedule.get('section')}")
    data = raw_schedule.get('schedule_data')
    if data:
        if isinstance(data, str):
            data = json.loads(data)
        print(f"Schedule data type: {type(data)}")
        print(f"Schedule data length: {len(data) if isinstance(data, list) else 'N/A'}")
    else:
        print("schedule_data is None or empty")
else:
    print("No schedule found in database")
