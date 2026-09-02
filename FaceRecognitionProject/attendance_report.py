"""
Attendance Reports - Smart Attendance System
=============================================
Terminal-based attendance reporting:
  - View today's attendance (present + absent)
  - View attendance by date
  - Student attendance summary over a date range
  - Export reports to CSV
"""
import os
import sys
import csv
from datetime import datetime, date, timedelta

sys.stdout.reconfigure(line_buffering=True)

from database import Database


def _print_attendance_table(records, title=""):
    """Print attendance records as a formatted table."""
    if title:
        print(f"\n  {title}")
        print("  " + "─" * 60)

    if not records:
        print("  (No records)")
        return

    print(f"  {'#':<4} {'ID':<8} {'Name':<25} {'Time':<10} {'Confidence':<12} {'Status'}")
    print("  " + "─" * 70)
    for i, r in enumerate(records, 1):
        conf_str = f"{r['confidence']:.1f}%" if r['confidence'] else "N/A"
        print(f"  {i:<4} {r['id']:<8} {r['name']:<25} {r['time']:<10} {conf_str:<12} {r['status']}")


def _print_absent_table(absent_list):
    """Print absent students list."""
    if not absent_list:
        print("  (All students present!)")
        return

    print(f"  {'#':<4} {'ID':<8} {'Name':<25} {'Department'}")
    print("  " + "─" * 50)
    for i, r in enumerate(absent_list, 1):
        print(f"  {i:<4} {r['id']:<8} {r['name']:<25} {r['department']}")


def view_today():
    """View today's attendance with present and absent lists."""
    db = Database()
    today = date.today().isoformat()
    summary = db.get_attendance_summary(today)
    records = db.get_attendance_by_date(today)
    absent = db.get_absent_students(today)

    print()
    print("  " + "═" * 55)
    print(f"  TODAY: {today}")
    print("  " + "═" * 55)
    print(f"  Present: {summary['present']}/{summary['total']} ({summary['percentage']}%)")
    print(f"  Absent:  {summary['absent']}/{summary['total']}")
    print("  " + "═" * 55)

    _print_attendance_table(records, "PRESENT STUDENTS")

    print()
    print("  ABSENT STUDENTS")
    print("  " + "─" * 60)
    _print_absent_table(absent)

    db.close()


def view_by_date():
    """View attendance for a specific date."""
    db = Database()

    # Show available dates
    dates = db.get_all_dates_with_attendance()
    if not dates:
        print("\n  [INFO] No attendance records found yet.")
        db.close()
        return

    print("\n  Available dates with attendance records:")
    for i, d in enumerate(dates[:10], 1):
        summary = db.get_attendance_summary(d)
        print(f"    {i}. {d}  — {summary['present']}/{summary['total']} present")

    if len(dates) > 10:
        print(f"    ... and {len(dates) - 10} more dates")

    print()
    choice = input("  Enter date (YYYY-MM-DD) or row number: ").strip()

    # Allow selecting by row number
    try:
        idx = int(choice) - 1
        if 0 <= idx < len(dates):
            target_date = dates[idx]
        else:
            target_date = choice
    except ValueError:
        target_date = choice

    # Validate date format
    try:
        datetime.strptime(target_date, "%Y-%m-%d")
    except ValueError:
        print(f"  [ERROR] Invalid date format: {target_date}")
        db.close()
        return

    summary = db.get_attendance_summary(target_date)
    records = db.get_attendance_by_date(target_date)
    absent = db.get_absent_students(target_date)

    print()
    print("  " + "═" * 55)
    print(f"  DATE: {target_date}")
    print("  " + "═" * 55)
    print(f"  Present: {summary['present']}/{summary['total']} ({summary['percentage']}%)")
    print(f"  Absent:  {summary['absent']}/{summary['total']}")
    print("  " + "═" * 55)

    _print_attendance_table(records, "PRESENT STUDENTS")

    print()
    print("  ABSENT STUDENTS")
    print("  " + "─" * 60)
    _print_absent_table(absent)

    db.close()


def view_absent_today():
    """Quick view of absent students today."""
    db = Database()
    today = date.today().isoformat()
    absent = db.get_absent_students(today)
    summary = db.get_attendance_summary(today)

    print()
    print("  " + "═" * 55)
    print(f"  ABSENT STUDENTS — {today}")
    print(f"  {summary['absent']}/{summary['total']} students absent")
    print("  " + "═" * 55)
    print()
    _print_absent_table(absent)

    db.close()


def student_summary():
    """View a student's attendance over a date range."""
    db = Database()

    student_id = input("\n  Enter Student ID: ").strip()
    student = db.get_student(student_id)

    if student is None:
        print(f"  [ERROR] Student ID '{student_id}' not found!")
        db.close()
        return

    print(f"\n  Student: {student['name']} ({student['department']})")
    print()

    # Get date range
    print("  Enter date range (or press Enter for last 30 days):")
    start_input = input("  Start date (YYYY-MM-DD): ").strip()
    end_input = input("  End date (YYYY-MM-DD): ").strip()

    if not start_input:
        start_date = (date.today() - timedelta(days=30)).isoformat()
    else:
        start_date = start_input

    if not end_input:
        end_date = date.today().isoformat()
    else:
        end_date = end_input

    # Validate dates
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        print("  [ERROR] Invalid date format!")
        db.close()
        return

    present_dates = db.get_student_attendance_range(student_id, start_date, end_date)

    # Get all dates that have attendance records in this range
    all_dates = db.get_all_dates_with_attendance()
    class_dates = [d for d in all_dates if start_date <= d <= end_date]

    total_classes = len(class_dates)
    present_count = len(present_dates)
    absent_count = total_classes - present_count
    attendance_pct = round((present_count / total_classes * 100), 1) if total_classes > 0 else 0

    print()
    print("  " + "═" * 55)
    print(f"  ATTENDANCE SUMMARY: {student['name']}")
    print(f"  Period: {start_date} to {end_date}")
    print("  " + "═" * 55)
    print(f"  Total class days:  {total_classes}")
    print(f"  Present:           {present_count}")
    print(f"  Absent:            {absent_count}")
    print(f"  Attendance %:      {attendance_pct}%")
    print("  " + "─" * 55)

    if class_dates:
        print()
        print(f"  {'Date':<15} {'Status'}")
        print("  " + "─" * 25)
        for d in sorted(class_dates):
            status = "✓ PRESENT" if d in present_dates else "✗ ABSENT"
            print(f"  {d:<15} {status}")

    db.close()


def export_report():
    """Export attendance report to CSV."""
    db = Database()

    print("\n  Export Options:")
    print("    1. Export today's attendance")
    print("    2. Export attendance for a specific date")
    print("    3. Export full attendance database")
    print()

    choice = input("  Enter choice (1-3): ").strip()

    if choice == "1":
        target_date = date.today().isoformat()
        _export_date_report(db, target_date)
    elif choice == "2":
        target_date = input("  Enter date (YYYY-MM-DD): ").strip()
        try:
            datetime.strptime(target_date, "%Y-%m-%d")
        except ValueError:
            print("  [ERROR] Invalid date format!")
            db.close()
            return
        _export_date_report(db, target_date)
    elif choice == "3":
        _export_full_report(db)
    else:
        print("  [ERROR] Invalid choice.")

    db.close()


def _export_date_report(db, target_date):
    """Export attendance for a specific date to CSV."""
    records = db.get_attendance_by_date(target_date)
    absent = db.get_absent_students(target_date)
    summary = db.get_attendance_summary(target_date)

    # Create reports directory
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    filename = f"attendance_{target_date}.csv"
    filepath = os.path.join(reports_dir, filename)

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header info
            writer.writerow(["Smart Attendance Report"])
            writer.writerow(["Date", target_date])
            writer.writerow(["Present", f"{summary['present']}/{summary['total']}"])
            writer.writerow(["Absent", f"{summary['absent']}/{summary['total']}"])
            writer.writerow(["Attendance %", f"{summary['percentage']}%"])
            writer.writerow([])

            # Present students
            writer.writerow(["=== PRESENT STUDENTS ==="])
            writer.writerow(["ID", "Name", "Department", "Time", "Confidence", "Status"])
            for r in records:
                conf_str = f"{r['confidence']:.1f}%" if r['confidence'] else "N/A"
                writer.writerow([r['id'], r['name'], r['department'],
                               r['time'], conf_str, r['status']])
            writer.writerow([])

            # Absent students
            writer.writerow(["=== ABSENT STUDENTS ==="])
            writer.writerow(["ID", "Name", "Department"])
            for r in absent:
                writer.writerow([r['id'], r['name'], r['department']])

        print(f"\n  [OK] Report exported to: {filepath}")
    except Exception as e:
        print(f"\n  [ERROR] Failed to export: {e}")


def _export_full_report(db):
    """Export all attendance records to CSV."""
    reports_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"full_attendance_{timestamp}.csv"
    filepath = os.path.join(reports_dir, filename)

    dates = db.get_all_dates_with_attendance()
    students = db.get_all_students()

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow(["Smart Attendance — Full Report"])
            writer.writerow(["Generated", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            writer.writerow(["Total Students", len(students)])
            writer.writerow(["Total Days", len(dates)])
            writer.writerow([])

            # All attendance records
            writer.writerow(["Date", "ID", "Name", "Department", "Time", "Confidence", "Status"])

            for d in sorted(dates):
                records = db.get_attendance_by_date(d)
                for r in records:
                    conf_str = f"{r['confidence']:.1f}%" if r['confidence'] else "N/A"
                    writer.writerow([d, r['id'], r['name'], r['department'],
                                   r['time'], conf_str, r['status']])

        print(f"\n  [OK] Full report exported to: {filepath}")
    except Exception as e:
        print(f"\n  [ERROR] Failed to export: {e}")


def reports_menu():
    """Main attendance reports menu."""
    while True:
        print()
        print("=" * 55)
        print("   ATTENDANCE REPORTS")
        print("=" * 55)
        print()
        print("   1.  View Today's Attendance")
        print("   2.  View Attendance by Date")
        print("   3.  View Absent Students (Today)")
        print("   4.  Student Attendance Summary (Date Range)")
        print("   5.  Export Report to CSV")
        print("   0.  Back to Dashboard")
        print()

        choice = input("   Enter choice (0-5): ").strip()

        if choice == "1":
            view_today()
        elif choice == "2":
            view_by_date()
        elif choice == "3":
            view_absent_today()
        elif choice == "4":
            student_summary()
        elif choice == "5":
            export_report()
        elif choice == "0":
            break
        else:
            print("\n  [ERROR] Invalid choice.")

        input("\n  Press Enter to continue...")


if __name__ == "__main__":
    reports_menu()
