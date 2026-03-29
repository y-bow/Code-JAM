"""
Master Database Synchronization Script
Orchestrates all seeding scripts for Schools, Sections, and Students (Sections 1, 2, 3).
Run this after merging branches to ensure your local database is up to date.
"""
import seed
import insert_section1_students
import insert_section2_students
import seed_section3_students
import seed_section3_timetable

def sync_all():
    print("="*60)
    print("STARTING DATABASE SYNCHRONIZATION")
    print("="*60)

    # 1. Run core infrastructure seed (Non-destructive)
    print("\n--- PHASE 1: Core Infrastructure (Schools, Sections, Admin Accounts) ---")
    seed.run_seed(reset=False) 

    # 2. Run Section 1 Students
    print("\n--- PHASE 2: Section 1 Students ---")
    insert_section1_students.run()

    # 3. Run Section 2 Students
    print("\n--- PHASE 3: Section 2 Students ---")
    insert_section2_students.run()

    # 4. Run Section 3 Students (includes lab_section migration)
    print("\n--- PHASE 4: Section 3 Students ---")
    seed_section3_students.run()

    # 5. Run Section 3 Timetable
    print("\n--- PHASE 5: Section 3 Timetable ---")
    seed_section3_timetable.run()

    print("\n" + "="*60)
    print("DATABASE SYNCHRONIZATION COMPLETE")
    print("="*60)
    print("All sections (1, 2, 3) and timetables are now up to date.")

if __name__ == "__main__":
    sync_all()
