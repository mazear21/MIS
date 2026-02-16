"""
Redistribute students across all 24 classes naturally.

Steps:
1. Students WITH class_id but WITHOUT semester → derive semester/shift/section from their class
2. Students WITH semester/shift/section but WITHOUT class_id → look up and set class_id
3. Students with NEITHER → distribute randomly across all classes
4. Rebalance: move students from overpopulated classes to underpopulated ones
"""
import sys
import random
sys.path.insert(0, '.')
import db

def main():
    # Get all classes
    classes = db.execute_query(
        "SELECT id, year, semester, section, shift FROM classes WHERE is_active = true ORDER BY semester, shift, section",
        fetch_all=True
    )
    print(f"Found {len(classes)} active classes")
    
    # Build lookup: (semester, shift, section) -> class_id
    class_lookup = {}
    for c in classes:
        key = (c['semester'], c['shift'], c['section'])
        class_lookup[key] = c['id']
    
    # ── Step 1: Students WITH class_id but WITHOUT semester ──
    step1 = db.execute_query(
        "SELECT s.id, s.class_id FROM students s WHERE s.class_id IS NOT NULL AND s.semester IS NULL",
        fetch_all=True
    ) or []
    print(f"\nStep 1: {len(step1)} students have class_id but no semester")
    
    for s in step1:
        cls = db.execute_query(
            "SELECT year, semester, section, shift FROM classes WHERE id = %s", (s['class_id'],), fetch_one=True
        )
        if cls:
            db.execute_query(
                "UPDATE students SET year = %s, semester = %s, shift = %s, section = %s WHERE id = %s",
                (cls['year'], cls['semester'], cls['shift'], cls['section'], s['id'])
            )
    print(f"  ✓ Updated {len(step1)} students with semester/shift/section from their class")
    
    # ── Step 2: Students WITH semester/shift/section but WITHOUT class_id ──
    step2 = db.execute_query(
        "SELECT id, semester, shift, section FROM students WHERE class_id IS NULL AND semester IS NOT NULL AND shift IS NOT NULL AND section IS NOT NULL",
        fetch_all=True
    ) or []
    print(f"\nStep 2: {len(step2)} students have semester but no class_id")
    
    linked = 0
    for s in step2:
        key = (s['semester'], s['shift'], s['section'])
        cid = class_lookup.get(key)
        if cid:
            db.execute_query("UPDATE students SET class_id = %s WHERE id = %s", (cid, s['id']))
            linked += 1
    print(f"  ✓ Linked {linked} students to their class")
    
    # ── Step 3: Students with NEITHER semester NOR class_id ──
    step3 = db.execute_query(
        "SELECT id FROM students WHERE class_id IS NULL AND semester IS NULL",
        fetch_all=True
    ) or []
    print(f"\nStep 3: {len(step3)} students have neither → distributing randomly")
    
    if step3:
        random.shuffle(step3)
        class_ids = [c['id'] for c in classes]
        for i, s in enumerate(step3):
            target_class = classes[i % len(classes)]
            cid = target_class['id']
            db.execute_query(
                "UPDATE students SET class_id = %s, year = %s, semester = %s, shift = %s, section = %s WHERE id = %s",
                (cid, target_class['year'], target_class['semester'], target_class['shift'], target_class['section'], s['id'])
            )
        print(f"  ✓ Distributed {len(step3)} students across classes")
    
    # ── Step 4: Rebalance distribution naturally ──
    print("\n── Rebalancing for natural distribution ──")
    
    # Get current counts per class
    counts = db.execute_query("""
        SELECT c.id, c.name, c.year, c.semester, c.shift, c.section, COUNT(s.id) as cnt
        FROM classes c LEFT JOIN students s ON s.class_id = c.id
        WHERE c.is_active = true
        GROUP BY c.id, c.name, c.year, c.semester, c.shift, c.section
        ORDER BY cnt DESC
    """, fetch_all=True)
    
    total_students = sum(r['cnt'] for r in counts)
    avg = total_students / len(counts)
    print(f"Total students: {total_students}, Classes: {len(counts)}, Average: {avg:.1f}")
    
    # Build a class_count dict
    class_count = {r['id']: r['cnt'] for r in counts}
    class_info = {r['id']: r for r in counts}
    
    # Collect all students to move: from overpopulated classes
    target = int(avg)
    moves = []
    
    for r in counts:
        excess = r['cnt'] - (target + random.randint(0, 2))
        if excess > 0:
            # Get random students from this overpopulated class
            moveable = db.execute_query(
                "SELECT id FROM students WHERE class_id = %s ORDER BY RANDOM() LIMIT %s",
                (r['id'], excess), fetch_all=True
            ) or []
            for s in moveable:
                moves.append(s['id'])
            class_count[r['id']] -= len(moveable)
    
    print(f"  Found {len(moves)} students to move from overpopulated classes")
    
    # Sort classes by count ascending to fill underpopulated first
    random.shuffle(moves)
    
    for student_id in moves:
        # Find the class with lowest count
        min_class_id = min(class_count, key=class_count.get)
        c = class_info[min_class_id]
        
        db.execute_query(
            "UPDATE students SET class_id = %s, year = %s, semester = %s, shift = %s, section = %s WHERE id = %s",
            (min_class_id, c['year'], c['semester'], c['shift'], c['section'], student_id)
        )
        class_count[min_class_id] += 1
    
    print(f"  ✓ Moved {len(moves)} students for better balance")
    
    # ── Final report ──
    print("\n" + "="*60)
    print("FINAL DISTRIBUTION")
    print("="*60)
    
    final = db.execute_query("""
        SELECT c.name, c.semester, c.shift, c.section, COUNT(s.id) as cnt
        FROM classes c LEFT JOIN students s ON s.class_id = c.id
        WHERE c.is_active = true
        GROUP BY c.id, c.name, c.semester, c.shift, c.section
        ORDER BY c.semester, c.shift, c.section
    """, fetch_all=True)
    
    for sem in [1, 2, 3, 4]:
        sem_classes = [r for r in final if r['semester'] == sem]
        sem_total = sum(r['cnt'] for r in sem_classes)
        print(f"\n  Semester {sem} ({sem_total} students):")
        for r in sem_classes:
            bar = "█" * r['cnt']
            print(f"    {r['shift']:7s} {r['section']}: {r['cnt']:3d} {bar}")
    
    # Check for any remaining orphans
    orphans = db.execute_query("SELECT COUNT(*) as cnt FROM students WHERE class_id IS NULL", fetch_one=True)
    no_sem = db.execute_query("SELECT COUNT(*) as cnt FROM students WHERE semester IS NULL", fetch_one=True)
    print(f"\n  Remaining: {orphans['cnt']} without class, {no_sem['cnt']} without semester")


if __name__ == '__main__':
    main()
