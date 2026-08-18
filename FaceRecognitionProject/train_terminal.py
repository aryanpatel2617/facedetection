"""
Train Face Model - Terminal Version
Encodes faces from dataset/ and saves to models/trained_model.pkl.
"""
import os
import pickle
import face_recognition


def train_model():
    """Train the face recognition model in the terminal."""
    print()
    print("=" * 50)
    print("   TRAIN FACE MODEL")
    print("=" * 50)
    print()

    dataset_path = "dataset"
    if not os.path.exists(dataset_path):
        print("  [ERROR] 'dataset' folder not found!")
        return

    persons = [d for d in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, d))]

    if not persons:
        print("  [ERROR] No user data found in dataset!")
        return

    total_persons = len(persons)
    print(f"  Found {total_persons} person(s): {persons}")
    print()

    known_face_encodings = []
    known_face_names = []

    for i, person_name in enumerate(persons):
        person_folder = os.path.join(dataset_path, person_name)
        images = [f for f in os.listdir(person_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        print(f"  [{i+1}/{total_persons}] Encoding '{person_name}' ({len(images)} images)...", end=" ", flush=True)

        count = 0
        for img_name in images:
            img_path = os.path.join(person_folder, img_name)
            try:
                image = face_recognition.load_image_file(img_path)
                encodings = face_recognition.face_encodings(image)
                if len(encodings) > 0:
                    known_face_encodings.append(encodings[0])
                    known_face_names.append(person_name)
                    count += 1
            except Exception as e:
                print(f"\n    Warning: {img_name}: {e}")

        print(f"({count} faces encoded)")

    if not known_face_encodings:
        print("\n  [ERROR] Could not find valid faces in dataset.")
        return

    # Save model
    model_dir = "models"
    os.makedirs(model_dir, exist_ok=True)

    model_path = os.path.join(model_dir, "trained_model.pkl")
    try:
        with open(model_path, 'wb') as f:
            pickle.dump({"encodings": known_face_encodings, "names": known_face_names}, f)

        print()
        print(f"  [OK] Training Complete!")
        print(f"    Encoded {len(known_face_encodings)} faces for {total_persons} person(s)")
        print(f"    Model saved to: {model_path}")
    except Exception as e:
        print(f"\n  [ERROR] Failed to save model: {e}")


if __name__ == "__main__":
    train_model()
