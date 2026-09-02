"""
Student Enrollment - Smart Attendance System
=============================================
Enroll students by providing their details + one photo each.
Supports:
  - Bulk import from CSV file + photos folder
  - Single student enrollment (interactive)
  - Re-enrollment with a better photo
  - Verification test (check if a student's face is recognizable)
"""
import os
import sys

sys.stdout.reconfigure(line_buffering=True)

import cv2
import numpy as np
import pandas as pd
import face_recognition

from database import Database


def _imread_unicode(path):
    """Read an image from a path that may contain Unicode characters.
    cv2.imread fails on non-ASCII paths on Windows, so we use numpy instead."""
    try:
        with open(path, 'rb') as f:
            data = f.read()
        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img
    except Exception:
        return None


def _generate_face_vector(image_path):
    """Generate a 128D face vector from a photo.

    Args:
        image_path: Path to the student's photo file.

    Returns:
        Tuple of (face_vector, error_message).
        face_vector is a 128D NumPy array, or None if face detection failed.
    """
    try:
        image = face_recognition.load_image_file(image_path)
    except Exception as e:
        return None, f"Cannot read image: {e}"

    # Detect face locations
    face_locations = face_recognition.face_locations(image, model="hog")

    if len(face_locations) == 0:
        return None, "No face detected in photo"

    if len(face_locations) > 1:
        # Use the largest face (closest to camera)
        areas = [(b - t) * (r - l) for (t, r, b, l) in face_locations]
        largest_idx = np.argmax(areas)
        face_locations = [face_locations[largest_idx]]

    # Generate 128D encoding
    encodings = face_recognition.face_encodings(image, face_locations)

    if len(encodings) == 0:
        return None, "Could not generate face encoding"

    return encodings[0], None


def bulk_enroll(csv_path=None, photos_folder=None):
    """Enroll multiple students from a CSV file and photos folder.

    Expected structure:
        student_data/
        ├── students.csv       ← CSV with columns: ID, Name, Department, Age
        └── photos/            ← One photo per student, named by ID (e.g., 001.jpg)
    """
    print()
    print("=" * 55)
    print("   BULK STUDENT ENROLLMENT")
    print("=" * 55)
    print()

    # Get CSV path
    if csv_path is None:
        print("  Enter the path to your students CSV file.")
        print("  (CSV must have columns: ID, Name, Department, Age)")
        print()
        csv_path = input("  CSV path: ").strip().strip('"').strip("'")

    if not os.path.exists(csv_path):
        print(f"\n  [ERROR] CSV file not found: {csv_path}")
        return

    # Get photos folder path
    if photos_folder is None:
        print()
        print("  Enter the path to the photos folder.")
        print("  (Photos should be named by student ID, e.g., 001.jpg, 002.png)")
        print()
        photos_folder = input("  Photos folder: ").strip().strip('"').strip("'")

    if not os.path.exists(photos_folder):
        print(f"\n  [ERROR] Photos folder not found: {photos_folder}")
        return

    # Read CSV
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"\n  [ERROR] Cannot read CSV: {e}")
        return

    # Validate columns
    required_cols = {"ID", "Name"}
    if not required_cols.issubset(set(df.columns)):
        print(f"\n  [ERROR] CSV must have columns: {required_cols}")
        print(f"  Found columns: {list(df.columns)}")
        return

    total = len(df)
    print(f"\n  Found {total} students in CSV.")
    print(f"  Photos folder: {photos_folder}")
    print()

    db = Database()
    enrolled = 0
    failed = 0
    skipped = 0
    img_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')

    for idx, row in df.iterrows():
        student_id = str(row['ID']).strip()
        name = str(row['Name']).strip()
        dept = str(row.get('Department', '')).strip()
        age = row.get('Age', None)

        try:
            age_int = int(age) if pd.notna(age) else None
        except (ValueError, TypeError):
            age_int = None

        progress = f"[{idx + 1:02d}/{total}]"

        # Check if already enrolled
        if db.student_exists(student_id):
            print(f"  {progress} {name} ({student_id}) → ⏭ SKIPPED (already enrolled)")
            skipped += 1
            continue

        # Find photo file (try different extensions)
        photo_path = None
        for ext in img_extensions:
            candidate = os.path.join(photos_folder, f"{student_id}{ext}")
            if os.path.exists(candidate):
                photo_path = candidate
                break

        # Also try name-based matching
        if photo_path is None:
            for ext in img_extensions:
                candidate = os.path.join(photos_folder, f"{name}{ext}")
                if os.path.exists(candidate):
                    photo_path = candidate
                    break

        if photo_path is None:
            print(f"  {progress} {name} ({student_id}) → ✗ FAILED: Photo not found")
            # Still register the student, but without face vector
            db.add_student(student_id, name, dept, age_int, None, None)
            failed += 1
            continue

        # Generate face vector
        face_vector, error = _generate_face_vector(photo_path)

        if face_vector is None:
            print(f"  {progress} {name} ({student_id}) → ✗ FAILED: {error}")
            # Register student but flag as needing re-enrollment
            db.add_student(student_id, name, dept, age_int, photo_path, None)
            failed += 1
            continue

        # Save to database
        success = db.add_student(student_id, name, dept, age_int, photo_path, face_vector)
        if success:
            print(f"  {progress} {name} ({student_id}) → ✓ Enrolled")
            enrolled += 1
        else:
            print(f"  {progress} {name} ({student_id}) → ✗ FAILED: Database error")
            failed += 1

    # Summary
    print()
    print("  " + "─" * 45)
    print(f"  RESULT: {enrolled} enrolled, {failed} failed, {skipped} skipped")
    print(f"  Total students in database: {db.get_student_count()}")

    if failed > 0:
        print()
        print("  [TIP] For failed students, fix their photos and use")
        print("        'Re-enroll Student' option to update their face vector.")

    db.close()


def single_enroll():
    """Enroll a single student interactively."""
    print()
    print("=" * 55)
    print("   ENROLL SINGLE STUDENT")
    print("=" * 55)
    print()

    # Collect details
    student_id = input("  Enter Student ID (e.g., 001): ").strip()
    name = input("  Enter Full Name: ").strip()
    dept = input("  Enter Department: ").strip()
    age = input("  Enter Age: ").strip()

    if not student_id or not name:
        print("\n  [ERROR] Student ID and Name are required!")
        return

    try:
        age_int = int(age) if age else None
    except ValueError:
        age_int = None

    db = Database()

    # Check for duplicates
    if db.student_exists(student_id):
        print(f"\n  [ERROR] Student ID '{student_id}' already exists!")
        db.close()
        return

    # Get photo
    print()
    print("  Enter the path to the student's photo.")
    print("  (Clear, front-facing, well-lit photo works best)")
    print()
    photo_path = input("  Photo path: ").strip().strip('"').strip("'")

    if not photo_path or not os.path.exists(photo_path):
        print(f"\n  [ERROR] Photo not found: {photo_path}")
        print("  Student registered WITHOUT face vector.")
        print("  Use 'Re-enroll' option later to add their photo.")
        db.add_student(student_id, name, dept, age_int, None, None)
        db.close()
        return

    # Generate face vector
    print("\n  Generating face vector...", end=" ", flush=True)
    face_vector, error = _generate_face_vector(photo_path)

    if face_vector is None:
        print(f"\n  [ERROR] {error}")
        print("  Student registered WITHOUT face vector.")
        db.add_student(student_id, name, dept, age_int, photo_path, None)
        db.close()
        return

    # Save
    success = db.add_student(student_id, name, dept, age_int, photo_path, face_vector)
    if success:
        print("Done!")
        print(f"\n  [OK] Student '{name}' enrolled successfully!")
        print(f"  Face vector: 128D encoding generated from photo.")
    else:
        print(f"\n  [ERROR] Failed to save student.")

    db.close()


def re_enroll():
    """Re-enroll a student with a better photo (updates their face vector)."""
    print()
    print("=" * 55)
    print("   RE-ENROLL STUDENT (Update Photo)")
    print("=" * 55)
    print()

    student_id = input("  Enter Student ID to re-enroll: ").strip()

    db = Database()
    student = db.get_student(student_id)

    if student is None:
        print(f"\n  [ERROR] Student ID '{student_id}' not found!")
        db.close()
        return

    print(f"\n  Found: {student['name']} (Dept: {student['department']})")
    has_vector = student['face_vector'] is not None
    print(f"  Current face vector: {'Yes' if has_vector else 'No (not enrolled)'}")

    print()
    photo_path = input("  Enter path to new photo: ").strip().strip('"').strip("'")

    if not photo_path or not os.path.exists(photo_path):
        print(f"\n  [ERROR] Photo not found: {photo_path}")
        db.close()
        return

    print("\n  Generating face vector...", end=" ", flush=True)
    face_vector, error = _generate_face_vector(photo_path)

    if face_vector is None:
        print(f"\n  [ERROR] {error}")
        db.close()
        return

    success = db.update_student_face(student_id, photo_path, face_vector)
    if success:
        print("Done!")
        print(f"\n  [OK] Face vector updated for '{student['name']}'!")
    else:
        print(f"\n  [ERROR] Failed to update.")

    db.close()


def verify_enrollment():
    """Test if a student's face can be recognized from the database."""
    print()
    print("=" * 55)
    print("   VERIFY ENROLLMENT")
    print("=" * 55)
    print()

    print("  Enter path to a test photo to check recognition.")
    photo_path = input("  Photo path: ").strip().strip('"').strip("'")

    if not photo_path or not os.path.exists(photo_path):
        print(f"\n  [ERROR] Photo not found: {photo_path}")
        return

    print("\n  Generating face vector from test photo...", end=" ", flush=True)
    test_vector, error = _generate_face_vector(photo_path)

    if test_vector is None:
        print(f"\n  [ERROR] {error}")
        return

    print("Done!")

    db = Database()
    face_data = db.load_all_face_vectors()

    if not face_data:
        print("\n  [ERROR] No enrolled students with face vectors found!")
        db.close()
        return

    print(f"\n  Comparing against {len(face_data)} enrolled students...\n")

    # Compare against all stored vectors
    results = []
    for sid, data in face_data.items():
        distance = face_recognition.face_distance([data["vector"]], test_vector)[0]
        confidence = round((1.0 - distance) * 100, 2)
        match = distance <= 0.5
        results.append((sid, data["name"], confidence, match))

    # Sort by confidence (highest first)
    results.sort(key=lambda x: x[2], reverse=True)

    # Show top 5 results
    print(f"  {'#':<4} {'ID':<8} {'Name':<25} {'Confidence':<12} {'Match'}")
    print("  " + "─" * 55)
    for i, (sid, name, conf, match) in enumerate(results[:5], 1):
        match_str = "✓ YES" if match else "✗ NO"
        print(f"  {i:<4} {sid:<8} {name:<25} {conf:>7}%     {match_str}")

    if results[0][3]:
        print(f"\n  [OK] Best match: {results[0][1]} ({results[0][2]}%)")
    else:
        print(f"\n  [WARNING] No confident match found. Best: {results[0][1]} ({results[0][2]}%)")
        print("  Consider re-enrolling with a clearer photo.")

    db.close()


def enroll_menu():
    """Main enrollment menu."""
    print()
    print("=" * 55)
    print("   STUDENT ENROLLMENT")
    print("=" * 55)
    print()
    print("   1.  Bulk Enroll (CSV + Photos folder)")
    print("   2.  Enroll Single Student")
    print("   3.  Re-enroll Student (Update Photo)")
    print("   4.  Verify Enrollment (Test Recognition)")
    print("   0.  Back to Dashboard")
    print()

    choice = input("   Enter choice (0-4): ").strip()

    if choice == "1":
        bulk_enroll()
    elif choice == "2":
        single_enroll()
    elif choice == "3":
        re_enroll()
    elif choice == "4":
        verify_enrollment()
    elif choice == "0":
        return
    else:
        print("\n  [ERROR] Invalid choice.")


if __name__ == "__main__":
    enroll_menu()
