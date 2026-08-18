"""
Register New Person - Terminal Version
"""
import os
import pandas as pd


def register_user():
    """Register a new person via terminal input."""
    print()
    print("=" * 50)
    print("   REGISTER NEW PERSON")
    print("=" * 50)
    print()

    csv_path = os.path.join("users", "users.csv")

    # Collect details
    user_id = input("  Enter Person ID (e.g., 001): ").strip()
    name = input("  Enter Full Name: ").strip()
    dept = input("  Enter Department: ").strip()
    age = input("  Enter Age: ").strip()

    if not all([user_id, name, dept, age]):
        print("\n  [ERROR] All fields are required!")
        return

    # Check for duplicates
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        try:
            df = pd.read_csv(csv_path)
            if str(user_id) in df['ID'].astype(str).values:
                print(f"\n  [ERROR] User ID {user_id} already exists!")
                return
            if name in df['Name'].values:
                print(f"\n  [ERROR] User Name '{name}' already exists!")
                return
        except Exception:
            pass

    # Save to CSV
    try:
        os.makedirs("users", exist_ok=True)
        new_data = pd.DataFrame({"ID": [user_id], "Name": [name], "Department": [dept], "Age": [age]})
        file_exists = os.path.exists(csv_path)
        new_data.to_csv(csv_path, mode='a', header=not file_exists or os.path.getsize(csv_path) == 0, index=False)
        print(f"\n  [OK] User '{name}' registered successfully!")
        print("    You can now capture their faces.")
    except Exception as e:
        print(f"\n  [ERROR] Failed to save data: {e}")


if __name__ == "__main__":
    register_user()
