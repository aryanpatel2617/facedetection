"""
Attendance History - Terminal Version
View, search, delete, and export attendance records.
"""
import os
import pandas as pd


def _load_attendance():
    """Load attendance CSV."""
    csv_path = os.path.join("attendance", "attendance.csv")
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        try:
            return pd.read_csv(csv_path), csv_path
        except Exception:
            pass
    return pd.DataFrame(columns=["Name", "Date", "Time"]), csv_path


def _print_table(df):
    """Print attendance records as a formatted table."""
    if df.empty:
        print("\n  (No records found)")
        return

    print()
    print(f"  {'#':<5} {'Name':<25} {'Date':<15} {'Time':<12}")
    print("  " + "-" * 57)
    for i, (_, row) in enumerate(df.iterrows(), 1):
        print(f"  {i:<5} {str(row.get('Name', '')):<25} {str(row.get('Date', '')):<15} {str(row.get('Time', '')):<12}")
    print()
    print(f"  Total: {len(df)} record(s)")


def attendance_menu():
    """Main attendance terminal menu."""
    print()
    print("=" * 50)
    print("   ATTENDANCE HISTORY")
    print("=" * 50)

    while True:
        df, csv_path = _load_attendance()
        _print_table(df)

        print()
        print("  Options:")
        print("    1. Search by name/date")
        print("    2. Delete specific record(s)")
        print("    3. Delete ALL records")
        print("    4. Export to CSV")
        print("    0. Back to menu")
        print()

        choice = input("  Enter choice: ").strip()

        if choice == "0":
            break

        elif choice == "1":
            query = input("  Search (name or date): ").strip().lower()
            if query and not df.empty:
                filtered = df[
                    df["Name"].astype(str).str.lower().str.contains(query, na=False) |
                    df["Date"].astype(str).str.lower().str.contains(query, na=False)
                ]
                print(f"\n  Search results for '{query}':")
                _print_table(filtered)
            input("\n  Press Enter to continue...")

        elif choice == "2":
            if df.empty:
                print("  [ERROR] No records to delete.")
                continue
            row_nums = input("  Enter row number(s) to delete (comma-separated): ").strip()
            try:
                indices = [int(x.strip()) - 1 for x in row_nums.split(",")]
                valid_indices = [i for i in indices if 0 <= i < len(df)]
                if not valid_indices:
                    print("  [ERROR] Invalid row number(s).")
                    continue
                confirm = input(f"  Delete {len(valid_indices)} record(s)? (y/n): ").strip().lower()
                if confirm == 'y':
                    df = df.drop(df.index[valid_indices])
                    df.to_csv(csv_path, index=False)
                    print(f"  [OK] Deleted {len(valid_indices)} record(s).")
            except ValueError:
                print("  [ERROR] Invalid input.")

        elif choice == "3":
            if df.empty:
                print("  [ERROR] No records to delete.")
                continue
            confirm = input("  Delete ALL attendance records? This cannot be undone! (y/n): ").strip().lower()
            if confirm == 'y':
                empty_df = pd.DataFrame(columns=["Name", "Date", "Time"])
                empty_df.to_csv(csv_path, index=False)
                print("  [OK] All attendance records deleted.")

        elif choice == "4":
            if df.empty:
                print("  [ERROR] No data to export.")
                continue
            export_path = os.path.join("attendance", "attendance_export.csv")
            df.to_csv(export_path, index=False)
            print(f"  [OK] Exported to: {export_path}")

        else:
            print("  [ERROR] Invalid choice.")


if __name__ == "__main__":
    attendance_menu()
