"""
Face Recognition - Simple Terminal Version
==========================================
- Loads face images from dataset/ folder
- Encodes faces using face_recognition library
- Splits data into Train (80%) and Test (20%)
- Trains a simple nearest-neighbor model
- Evaluates: Accuracy, Confusion Matrix, F1 Score, Classification Report
- Saves trained model to models/trained_model.pkl
"""

import os
import sys
import pickle
import numpy as np

# Force unbuffered output so prints show immediately in terminal
sys.stdout.reconfigure(line_buffering=True)
import face_recognition
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    classification_report,
)


# ─────────────────────────────────────────────
#  Step 1: Load images and encode faces
# ─────────────────────────────────────────────
def load_dataset(dataset_path="dataset"):
    """Load all face images from dataset folder and return encodings + labels."""
    encodings = []
    labels = []

    if not os.path.exists(dataset_path):
        print("ERROR: 'dataset' folder not found!")
        return [], []

    persons = [
        d for d in os.listdir(dataset_path)
        if os.path.isdir(os.path.join(dataset_path, d))
    ]

    if not persons:
        print("ERROR: No person folders found in dataset!")
        return [], []

    print(f"Found {len(persons)} person(s): {persons}")
    print()

    for person_name in persons:
        person_folder = os.path.join(dataset_path, person_name)
        images = [
            f for f in os.listdir(person_folder)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        print(f"  Loading {len(images)} images for '{person_name}'...", end=" ")

        count = 0
        for img_name in images:
            img_path = os.path.join(person_folder, img_name)
            try:
                image = face_recognition.load_image_file(img_path)
                encs = face_recognition.face_encodings(image)
                if len(encs) > 0:
                    encodings.append(encs[0])
                    labels.append(person_name)
                    count += 1
            except Exception as e:
                print(f"\n    Warning: Could not process {img_name}: {e}")

        print(f"({count} faces encoded)")

    return encodings, labels


# ─────────────────────────────────────────────
#  Step 2: Predict using nearest neighbor
# ─────────────────────────────────────────────
def predict(train_encodings, train_labels, test_encoding, tolerance=0.5):
    """Predict the label for a single test encoding."""
    distances = face_recognition.face_distance(train_encodings, test_encoding)

    if len(distances) == 0:
        return "UNKNOWN"

    best_idx = np.argmin(distances)
    matches = face_recognition.compare_faces(
        train_encodings, test_encoding, tolerance=tolerance
    )

    if matches[best_idx]:
        return train_labels[best_idx]
    else:
        return "UNKNOWN"


# ─────────────────────────────────────────────
#  Step 3: Main - Train, Test, Evaluate
# ─────────────────────────────────────────────
def main():
    print("=" * 55)
    print("   FACE RECOGNITION - TRAIN, TEST & EVALUATE")
    print("=" * 55)
    print()

    # --- Load dataset ---
    print("STEP 1: Loading dataset...")
    print("-" * 40)
    encodings, labels = load_dataset()

    if len(encodings) < 2:
        print("\nERROR: Need at least 2 face images to train and test.")
        return

    print(f"\nTotal faces loaded: {len(encodings)}")
    print()

    # --- Train/Test Split ---
    print("STEP 2: Splitting into Train & Test (80/20)...")
    print("-" * 40)

    X_train, X_test, y_train, y_test = train_test_split(
        encodings, labels, test_size=0.2, random_state=42, stratify=labels
    )

    print(f"  Training samples: {len(X_train)}")
    print(f"  Testing samples:  {len(X_test)}")
    print()

    # --- Save trained model ---
    print("STEP 3: Saving trained model...")
    print("-" * 40)

    model_dir = "models"
    os.makedirs(model_dir, exist_ok=True)

    model_data = {"encodings": X_train, "names": y_train}
    model_path = os.path.join(model_dir, "trained_model.pkl")

    with open(model_path, "wb") as f:
        pickle.dump(model_data, f)

    print(f"  Model saved to: {model_path}")
    print()

    # --- Predict on test set ---
    print("STEP 4: Predicting on test set...")
    print("-" * 40)

    y_pred = []
    for i, test_enc in enumerate(X_test):
        pred = predict(X_train, y_train, test_enc)
        y_pred.append(pred)
        print(f"  Sample {i+1}/{len(X_test)}: True = {y_test[i]}, Predicted = {pred}")

    print()

    # --- Evaluation ---
    print("=" * 55)
    print("   EVALUATION RESULTS")
    print("=" * 55)
    print()

    # Accuracy
    acc = accuracy_score(y_test, y_pred)
    print(f"ACCURACY: {acc * 100:.2f}%")
    print()

    # F1 Score
    f1 = f1_score(y_test, y_pred, average="weighted", zero_division=0)
    print(f"F1 SCORE (weighted): {f1 * 100:.2f}%")
    print()

    # Classification Report
    print("CLASSIFICATION REPORT:")
    print("-" * 55)
    report = classification_report(y_test, y_pred, zero_division=0)
    print(report)

    # Confusion Matrix
    print("CONFUSION MATRIX:")
    print("-" * 55)
    unique_labels = sorted(set(y_test + y_pred))
    cm = confusion_matrix(y_test, y_pred, labels=unique_labels)

    # Print header row
    col_width = max(len(str(l)) for l in unique_labels) + 2
    header = " " * (col_width + 2) + "".join(
        str(l).center(col_width) for l in unique_labels
    )
    print(f"{'':>{col_width}}  " + "  ".join(f"{l:>{col_width}}" for l in unique_labels))

    # Print each row
    for i, label in enumerate(unique_labels):
        row_values = "  ".join(f"{v:>{col_width}}" for v in cm[i])
        print(f"{label:>{col_width}}  {row_values}")

    print()
    print("=" * 55)
    print("   DONE!")
    print("=" * 55)


if __name__ == "__main__":
    main()

# so this is the commit from aryan that we are checking that our repo is working properly