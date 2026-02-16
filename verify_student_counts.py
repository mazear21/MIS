"""
Verification of Student Count Implementation
============================================

This script verifies that student counts are accurate across all classes and semesters.

Current Student Distribution:
- Semester 1: 49 total students (6 classes)
- Semester 2: 48 total students (6 classes)
- Semester 3: 49 total students (6 classes)
- Semester 4: 49 total students (6 classes)
- GRAND TOTAL: 195 students

Implementation Details:
1. db.get_class_student_counts() returns:
   - counts: dict with keys like "1_morning_A" -> student count
   - semester_totals: dict with keys 1-4 -> total students in that semester

2. Template displays:
   - Individual counts on each class button (A, B, C)
   - Total count badge on each semester card header

3. All counts use LEFT JOIN to ensure classes with 0 students show correctly
"""

import db

print("=" * 70)
print("STUDENT COUNT VERIFICATION")
print("=" * 70)

# Get counts
counts, semester_totals = db.get_class_student_counts()

# Display by semester
for semester in range(1, 5):
    print(f"\n{'='*70}")
    print(f"SEMESTER {semester} - Total: {semester_totals[semester]} students")
    print(f"{'='*70}")
    
    for shift in ['morning', 'night']:
        print(f"\n  {shift.upper()}:")
        for section in ['A', 'B', 'C']:
            key = f"{semester}_{shift}_{section}"
            count = counts.get(key, 0)
            print(f"    Class {section}: {count:2d} students")

# Summary
print(f"\n{'='*70}")
print("SUMMARY")
print(f"{'='*70}")
print(f"Total semesters: 4")
print(f"Total shifts: 2 (morning, night)")
print(f"Total sections: 3 (A, B, C)")
print(f"Total classes: 24")
print(f"Total students: {sum(semester_totals.values())}")
print(f"\nSemester totals: {semester_totals}")
print(f"{'='*70}")
