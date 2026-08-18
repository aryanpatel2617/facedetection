"""1
Face Recognition System - Terminal Version
===========================================
Run this file to start the entire application in the terminal.
No GUI / Tkinter required.

Usage:  python app_terminal.py
"""
import os
import sys

# Force unbuffered output
sys.stdout.reconfigure(line_buffering=True)


def init_csv_files():
    """Create required folders and CSV files if they don't exist."""
    os.makedirs("users", exist_ok=True)
    os.makedirs("dataset", exist_ok=True)
    os.makedirs("models", exist_ok=True)

    users_path = os.path.join("users", "users.csv")

    if not os.path.exists(users_path):
        with open(users_path, 'w') as f:
            f.write("ID,Name,Department,Age\n")


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def login():
    """Terminal-based login prompt."""
    clear_screen()
    print()
    print("=" * 55)
    print("   +-------------------------------------------+")
    print("   |       FACE RECOGNITION SYSTEM             |")
    print("   |       Face Recognition System              |")
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


def show_dashboard():
    """Display the main dashboard menu and handle choices."""
    while True:
        print()
        print("=" * 55)
        print("   DASHBOARD - Admin Panel")
        print("=" * 55)
        print()
        print("   1.  Register New Person")
        print("   2.  Capture Faces")
        print("   3.  Train Model")
        print("   4.  Recognize Faces (Camera)")
        print("   5.  Manage Users")
        print("   6.  Evaluate Model (Metrics)")
        print("   0.  Logout & Exit")
        print()

        choice = input("   Enter choice (0-6): ").strip()

        if choice == "1":
            from register_terminal import register_user
            register_user()
            input("\n  Press Enter to continue...")

        elif choice == "2":
            from capture_terminal import capture_faces
            capture_faces()
            input("\n  Press Enter to continue...")

        elif choice == "3":
            from train_terminal import train_model
            train_model()
            input("\n  Press Enter to continue...")

        elif choice == "4":
            from recognize_terminal import recognize_faces
            recognize_faces()
            input("\n  Press Enter to continue...")

        elif choice == "5":
            from manage_users_terminal import manage_users_menu
            manage_users_menu()

        elif choice == "6":
            from evaluate_terminal import evaluate_model
            evaluate_model()
            input("\n  Press Enter to continue...")

        elif choice == "0":
            print("\n   Goodbye!\n")
            break

        else:
            print("\n   [FAIL] Invalid choice. Please enter 0-6.")


def main():
    """Main entry point."""
    init_csv_files()

    if login():
        show_dashboard()


if __name__ == "__main__":
    main()
