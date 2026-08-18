"""
Manage Users - Terminal Version
View and delete registered users.
"""
import os
import shutil
import pandas as pd


def _load_users():
    """Load users CSV."""
    csv_path = os.path.join("users", "users.csv")
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        try:
            return pd.read_csv(csv_path), csv_path
        except Exception:
            pass
    return pd.DataFrame(columns=["ID", "Name", "Department", "Age"]), csv_path


def _print_users(df):
    """Print users as a formatted table."""
    if df.empty:
        print("\n  (No registered users)")
        return

    print()
    print(f"  {'#':<5} {'ID':<8} {'Name':<25} {'Department':<20} {'Age':<6}")
    print("  " + "-" * 64)
    for i, (_, row) in enumerate(df.iterrows(), 1):
        print(f"  {i:<5} {str(row.get('ID', '')):<8} {str(row.get('Name', '')):<25} {str(row.get('Department', '')):<20} {str(row.get('Age', '')):<6}")
    print()
    print(f"  Total: {len(df)} registered user(s)")


def manage_users_menu():
    """Main user management terminal menu."""
    print()
    print("=" * 50)
    print("   MANAGE USERS")
    print("=" * 50)

    while True:
        df, csv_path = _load_users()
        _print_users(df)

        print()
        print("  Options:")
        print("    1. Delete user(s)")
        print("    2. Refresh")
        print("    0. Back to menu")
        print()

        choice = input("  Enter choice: ").strip()

        if choice == "0":
            break

        elif choice == "1":
            if df.empty:
                print("  [ERROR] No users to delete.")
                continue

            row_nums = input("  Enter row number(s) to delete (comma-separated): ").strip()
            try:
                indices = [int(x.strip()) - 1 for x in row_nums.split(",")]
                valid_indices = [i for i in indices if 0 <= i < len(df)]
                if not valid_indices:
                    print("  [ERROR] Invalid row number(s).")
                    continue

                names_to_delete = [str(df.iloc[i]['Name']) for i in valid_indices]
                confirm = input(f"  Delete {', '.join(names_to_delete)}? This also removes their face images. (y/n): ").strip().lower()

                if confirm == 'y':
                    for i in valid_indices:
                        name = str(df.iloc[i]['Name'])
                        user_folder = os.path.join("dataset", name)
                        if os.path.exists(user_folder):
                            try:
                                shutil.rmtree(user_folder)
                            except Exception:
                                pass

                    df = df.drop(df.index[valid_indices])
                    df.to_csv(csv_path, index=False)
                    print(f"  [OK] Deleted user(s): {', '.join(names_to_delete)}")
            except ValueError:
                print("  [ERROR] Invalid input.")

        elif choice == "2":
            print("  Refreshing...")

        else:
            print("  [ERROR] Invalid choice.")


if __name__ == "__main__":
    manage_users_menu()
