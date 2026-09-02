"""
Capture Faces - Terminal Version
Upload images or capture from webcam.
"""
import os

import numpy as np
import cv2
import pandas as pd


def _get_registered_users():
    """Load registered users from CSV."""
    csv_path = os.path.join("users", "users.csv")
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        try:
            df = pd.read_csv(csv_path)
            return df['Name'].tolist()
        except Exception:
            pass
    return []


def _select_user(names):
    """Display users and let the user pick one."""
    print("\n  Registered Users:")
    print("  " + "-" * 30)
    for i, name in enumerate(names, 1):
        print(f"    {i}. {name}")
    print()

    while True:
        choice = input("  Enter user number: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(names):
                return names[idx]
        except ValueError:
            pass
        print("  [ERROR] Invalid choice. Try again.")


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


def _imwrite_unicode(path, img):
    """Write an image to a path that may contain Unicode characters."""
    try:
        ext = os.path.splitext(path)[1] if os.path.splitext(path)[1] else '.jpg'
        success, buf = cv2.imencode(ext, img)
        if success:
            with open(path, 'wb') as f:
                f.write(buf.tobytes())
            return True
    except Exception:
        pass
    return False


def _get_image_files(path):
    """If path is a folder, return all image files inside it.
    If path is a file, return it as a single-item list."""
    img_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.webp')

    if os.path.isdir(path):
        files = []
        for f in os.listdir(path):
            if f.lower().endswith(img_extensions):
                files.append(os.path.join(path, f))
        return sorted(files)
    elif os.path.isfile(path) and path.lower().endswith(img_extensions):
        return [path]
    elif os.path.isfile(path):
        return [path]
    return []


def _upload_images(selected_name):
    """Upload images by entering file or folder paths."""
    user_folder = os.path.join("dataset", selected_name)
    os.makedirs(user_folder, exist_ok=True)

    existing = [f for f in os.listdir(user_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))]
    start_count = len(existing)

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    print("\n  Enter image file path OR folder path.")
    print("  If you enter a folder, all images inside will be used.")
    print("  Type 'done' when finished.\n")

    saved_count = 0
    skipped_count = 0

    while True:
        path = input("  Path: ").strip().strip('"').strip("'")
        if path.lower() == 'done':
            break
        if not path:
            continue
        if not os.path.exists(path):
            print(f"    [ERROR] Path not found: {path}")
            skipped_count += 1
            continue

        image_files = _get_image_files(path)

        if not image_files:
            print(f"    [ERROR] No image files found at: {path}")
            skipped_count += 1
            continue

        if os.path.isdir(path):
            print(f"    Found {len(image_files)} image(s) in folder.")

        for img_path in image_files:
            try:
                img = _imread_unicode(img_path)
                if img is None:
                    print(f"    [SKIP] Cannot read: {os.path.basename(img_path)}")
                    skipped_count += 1
                    continue

                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(80, 80))

                if len(faces) == 0:
                    start_count += 1
                    dest_path = os.path.join(user_folder, f"img_{start_count}.jpg")
                    _imwrite_unicode(dest_path, img)
                    saved_count += 1
                    print(f"    [OK] {os.path.basename(img_path)} -- saved (full image)")
                else:
                    for (x, y, w, h) in faces:
                        start_count += 1
                        face_img = img[y:y+h, x:x+w]
                        dest_path = os.path.join(user_folder, f"img_{start_count}.jpg")
                        _imwrite_unicode(dest_path, face_img)
                        saved_count += 1
                    print(f"    [OK] {os.path.basename(img_path)} -- {len(faces)} face(s) saved")
            except Exception as e:
                print(f"    [ERROR] {os.path.basename(img_path)}: {e}")
                skipped_count += 1

    print(f"\n  Result: {saved_count} saved, {skipped_count} skipped")


def _capture_from_camera(selected_name):
    """Capture faces from webcam using OpenCV window."""
    user_folder = os.path.join("dataset", selected_name)
    os.makedirs(user_folder, exist_ok=True)

    existing = [f for f in os.listdir(user_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))]
    start_count = len(existing)

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("\n  [ERROR] Webcam not found!")
        return

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    count = 0
    max_images = 50

    print(f"\n  Camera will open. Look at the camera and turn your head slightly.")
    print(f"  Capturing {max_images} images. Press 'q' to stop early.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(100, 100))

        for (x, y, w, h) in faces:
            count += 1
            face_img = frame[y:y+h, x:x+w]
            img_path = os.path.join(user_folder, f"img_{start_count + count}.jpg")
            cv2.imwrite(img_path, face_img)

            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, f"Captured: {count}/{max_images}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        cv2.imshow('Capturing Faces - Press q to cancel', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if cv2.getWindowProperty('Capturing Faces - Press q to cancel', cv2.WND_PROP_VISIBLE) < 1:
            break
        if count >= max_images:
            break

    cap.release()
    cv2.destroyAllWindows()

    if count > 0:
        print(f"  [OK] Successfully captured {count} images for {selected_name}.")
    else:
        print("  [ERROR] No faces were captured.")


def capture_faces():
    """Main capture function - terminal menu."""
    print()
    print("=" * 50)
    print("   CAPTURE FACES")
    print("=" * 50)

    names = _get_registered_users()
    if not names:
        print("\n  [ERROR] No registered users found. Please register a user first.")
        return

    selected_name = _select_user(names)
    print(f"\n  Selected: {selected_name}")

    print("\n  Choose method:")
    print("    1. Upload Images (enter file paths)")
    print("    2. Capture from Camera (webcam)")
    print()

    choice = input("  Enter choice (1/2): ").strip()

    if choice == "1":
        _upload_images(selected_name)
    elif choice == "2":
        _capture_from_camera(selected_name)
    else:
        print("  [ERROR] Invalid choice.")


if __name__ == "__main__":
    capture_faces()
