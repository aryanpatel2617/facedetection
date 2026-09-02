"""
Smart Attendance System - Terminal Version
===========================================
CCTV/Webcam-based face recognition attendance system.
Supports enrollment of 50-60 students, lecture-mode attendance,
and attendance reporting.

Also includes legacy face recognition tools for backward compatibility.

Usage:  python app_terminal.py
"""
import os
import sys

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)


def init_project():
    """Create required folders and files if they don't exist."""
    os.makedirs("users", exist_ok=True)
    os.makedirs("dataset", exist_ok=True)
    os.makedirs("models", exist_ok=True)

    users_path = os.path.join("users", "users.csv")

    if not os.path.exists(users_path):
        with open(users_path, 'w') as f:
            f.write("ID,Name,Department,Age\n")

    # Initialize the SQLite database (auto-creates tables)
    try:
        from database import Database
        db = Database()
        db.close()
    except Exception:
        pass


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def login():
    """Terminal-based login prompt."""
    clear_screen()
    print()
    print("=" * 55)
    print("   +-------------------------------------------+")
    print("   |     SMART ATTENDANCE SYSTEM               |")
    print("   |     CCTV-Based Face Recognition            |")
    print("   +-------------------------------------------+")
    print("=" * 55)
    print()
    print("   Sign In")
    print("   " + "-" * 35)
    print()

    max_attempts = 3
    for attempt in range(max_attempts):
        username = input("   Username: ").strip()
        password = input("   Password: ").strip()

        if username == "admin" and password == "admin":
            print("\n   [OK] Login successful! Welcome, Admin.")
            return True
        else:
            remaining = max_attempts - attempt - 1
            if remaining > 0:
                print(f"\n   [FAIL] Invalid credentials. {remaining} attempt(s) remaining.\n")
            else:
                print("\n   [FAIL] Too many failed attempts. Exiting.")
                return False

    return False


def _show_camera_settings():
    """Display and modify camera settings."""
    print()
    print("=" * 55)
    print("   CAMERA SETTINGS")
    print("=" * 55)
    print()

    try:
        import camera_config as cfg
        print(f"   Active Camera:     {cfg.ACTIVE_CAMERA}")
        print(f"   Camera Source:     {cfg.get_camera_source()}")
        print()
        print(f"   Lecture Duration:  {cfg.LECTURE_DURATION_MINUTES} min")
        print(f"   Aggressive Phase:  {cfg.AGGRESSIVE_PHASE_MINUTES} min (scan every {cfg.SCAN_INTERVAL_AGGRESSIVE}s)")
        print(f"   Relaxed Phase:     {cfg.RELAXED_PHASE_MINUTES} min (scan every {cfg.SCAN_INTERVAL_RELAXED}s)")
        print(f"   Idle Phase:        after {cfg.RELAXED_PHASE_MINUTES} min (scan every {cfg.SCAN_INTERVAL_IDLE}s)")
        print()
        print(f"   Confidence Threshold:  {cfg.CONFIDENCE_THRESHOLD}%")
        print(f"   Consecutive Scans:     {cfg.CONSECUTIVE_SCANS_REQUIRED}")
        print(f"   Face Detection Model:  {cfg.FACE_DETECTION_MODEL}")
        print(f"   Recognition Tolerance: {cfg.RECOGNITION_TOLERANCE}")
        print()
        print("   To change settings, edit: camera_config.py")
    except ImportError:
        print("   [ERROR] camera_config.py not found!")


def show_dashboard():
    """Display the main dashboard menu and handle choices."""
    while True:
        print()
        print("=" * 55)
        print("   DASHBOARD - Admin Panel")
        print("=" * 55)
        print()
        print("   ── Smart Attendance System ──────────────")
        print("   1.  Enroll Students (Single / Bulk CSV)")
        print("   2.  Start Attendance (Lecture Mode)")
        print("   3.  View Attendance Reports")
        print("   4.  Camera Settings")
        print()
        print("   ── Legacy Tools ────────────────────────")
        print("   5.  Register New Person")
        print("   6.  Capture Faces")
        print("   7.  Train Model")
        print("   8.  Recognize Faces (Camera)")
        print("   9.  Manage Users")
        print("   10. Evaluate Model (Metrics)")
        print()
        print("   0.  Logout & Exit")
        print()

        choice = input("   Enter choice (0-10): ").strip()

        # ── Smart Attendance Options ──

        if choice == "1":
            from enroll_students import enroll_menu
            enroll_menu()
            input("\n  Press Enter to continue...")

        elif choice == "2":
            from attendance_recognizer import start_attendance
            start_attendance()
            input("\n  Press Enter to continue...")

        elif choice == "3":
            from attendance_report import reports_menu
            reports_menu()

        elif choice == "4":
            _show_camera_settings()
            input("\n  Press Enter to continue...")

        # ── Legacy Options ──

        elif choice == "5":
            from register_terminal import register_user
            register_user()
            input("\n  Press Enter to continue...")

        elif choice == "6":
            from capture_terminal import capture_faces
            capture_faces()
            input("\n  Press Enter to continue...")

        elif choice == "7":
            from train_terminal import train_model
            train_model()
            input("\n  Press Enter to continue...")

        elif choice == "8":
            from recognize_terminal import recognize_faces
            recognize_faces()
            input("\n  Press Enter to continue...")

        elif choice == "9":
            from manage_users_terminal import manage_users_menu
            manage_users_menu()

        elif choice == "10":
            from evaluate_terminal import evaluate_model
            evaluate_model()
            input("\n  Press Enter to continue...")

        elif choice == "0":
            print("\n   Goodbye!\n")
            break

        else:
            print("\n   [FAIL] Invalid choice. Please enter 0-10.")


def main():
    """Main entry point."""
    init_project()

    if login():
        show_dashboard()


if __name__ == "__main__":
    main()
