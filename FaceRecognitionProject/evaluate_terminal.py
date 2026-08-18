"""
Model Evaluation - Terminal Version
Runs Leave-One-Out Cross-Validation and prints metrics.
"""
import os
import csv
import numpy as np
import face_recognition
from datetime import datetime
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix


def _load_encodings():
    """Load face encodings from the dataset folder."""
    dataset_path = "dataset"
    if not os.path.exists(dataset_path):
        print("  [ERROR] 'dataset' folder not found!")
        return [], []

    persons = [d for d in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, d))]
    if not persons:
        print("  [ERROR] No user data found in dataset!")
        return [], []

    encodings = []
    names = []
    total_persons = len(persons)

    for pi, person_name in enumerate(persons):
        person_folder = os.path.join(dataset_path, person_name)
        images = [f for f in os.listdir(person_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        print(f"  [{pi+1}/{total_persons}] Encoding '{person_name}' ({len(images)} images)...", end=" ", flush=True)

        count = 0
        for img_name in images:
            img_path = os.path.join(person_folder, img_name)
            try:
                image = face_recognition.load_image_file(img_path)
                encs = face_recognition.face_encodings(image)
                if len(encs) > 0:
                    encodings.append(encs[0])
                    names.append(person_name)
                    count += 1
            except Exception:
                pass

        print(f"({count} faces)")

    return encodings, names


def evaluate_model():
    """Run LOOCV evaluation and print results."""
    print()
    print("=" * 60)
    print("   MODEL EVALUATION (Leave-One-Out Cross-Validation)")
    print("=" * 60)
    print()

    # Step 1: Load encodings
    print("  STEP 1: Loading face encodings...")
    print("  " + "-" * 45)
    encodings, names = _load_encodings()

    if len(encodings) < 2:
        print("\n  [ERROR] Need at least 2 face encodings to evaluate.")
        return

    unique_persons = sorted(set(names))
    total = len(encodings)
    print(f"\n  Loaded: {total} samples, {len(unique_persons)} person(s)")

    # Step 2: LOOCV
    print()
    print("  STEP 2: Running Leave-One-Out CV...")
    print("  " + "-" * 45)

    y_true = []
    y_pred = []

    for i in range(total):
        test_encoding = encodings[i]
        test_label = names[i]

        train_encodings = encodings[:i] + encodings[i+1:]
        train_names = names[:i] + names[i+1:]

        matches = face_recognition.compare_faces(train_encodings, test_encoding, tolerance=0.5)
        face_distances = face_recognition.face_distance(train_encodings, test_encoding)

        predicted = "UNKNOWN"
        if len(face_distances) > 0:
            best_idx = np.argmin(face_distances)
            if matches[best_idx]:
                predicted = train_names[best_idx]

        y_true.append(test_label)
        y_pred.append(predicted)

        # Progress every 10% or so
        if (i + 1) % max(1, total // 10) == 0 or i == total - 1:
            pct = int((i + 1) / total * 100)
            print(f"    Evaluating... {i+1}/{total} ({pct}%)")

    # Step 3: Compute metrics
    print()
    print("  STEP 3: Computing metrics...")
    print("  " + "-" * 45)

    all_labels = sorted(set(y_true + y_pred))
    acc = accuracy_score(y_true, y_pred)
    precision, recall, f1, support = precision_recall_fscore_support(
        y_true, y_pred, labels=all_labels, zero_division=0
    )
    cm = confusion_matrix(y_true, y_pred, labels=all_labels)

    # Print results
    print()
    print("=" * 60)
    print("   EVALUATION RESULTS")
    print("=" * 60)
    print()

    acc_pct = round(acc * 100, 2)
    macro_prec = round(np.mean(precision) * 100, 2)
    macro_rec = round(np.mean(recall) * 100, 2)
    macro_f1 = round(np.mean(f1) * 100, 2)

    print(f"  ACCURACY:          {acc_pct}%")
    print(f"  MACRO PRECISION:   {macro_prec}%")
    print(f"  MACRO RECALL:      {macro_rec}%")
    print(f"  MACRO F1-SCORE:    {macro_f1}%")
    print(f"  TOTAL SAMPLES:     {total}")
    print(f"  TOTAL PERSONS:     {len(unique_persons)}")

    # Per-person report
    print()
    print("  CLASSIFICATION REPORT:")
    print("  " + "-" * 55)
    print(f"  {'Person':<20} {'Precision':>10} {'Recall':>10} {'F1':>10} {'Support':>10}")
    print("  " + "-" * 55)

    for idx, label in enumerate(all_labels):
        p = round(precision[idx] * 100, 2)
        r = round(recall[idx] * 100, 2)
        f = round(f1[idx] * 100, 2)
        s = int(support[idx])
        print(f"  {label:<20} {p:>9}% {r:>9}% {f:>9}% {s:>10}")

    print("  " + "-" * 55)
    print(f"  {'MACRO AVG':<20} {macro_prec:>9}% {macro_rec:>9}% {macro_f1:>9}% {total:>10}")

    # Confusion Matrix
    print()
    print("  CONFUSION MATRIX:")
    print("  " + "-" * 55)

    col_width = max(max(len(l) for l in all_labels), 10) + 2

    # Header row
    header = " " * (col_width + 4)
    for label in all_labels:
        header += f"{label:>{col_width}}"
    print(f"  {header}")

    # Data rows
    for i, label in enumerate(all_labels):
        row_str = f"  {label:>{col_width}}  "
        for j in range(len(all_labels)):
            row_str += f"{cm[i][j]:>{col_width}}"
        print(row_str)

    print()

    # Export option
    export = input("  Export report to CSV? (y/n): ").strip().lower()
    if export == 'y':
        _export_report(all_labels, precision, recall, f1, support, cm,
                       acc_pct, macro_prec, macro_rec, macro_f1, total, len(unique_persons))


def _export_report(labels, precision, recall, f1, support, cm,
                   accuracy, macro_prec, macro_rec, macro_f1, total_samples, total_persons):
    """Export evaluation report to CSV."""
    os.makedirs("models", exist_ok=True)
    filepath = os.path.join("models", f"evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")

    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            writer.writerow(["=== Model Evaluation Report ==="])
            writer.writerow(["Date", datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow(["Overall Accuracy", f"{accuracy}%"])
            writer.writerow(["Total Samples", total_samples])
            writer.writerow(["Total Persons", total_persons])
            writer.writerow(["Macro Precision", f"{macro_prec}%"])
            writer.writerow(["Macro Recall", f"{macro_rec}%"])
            writer.writerow(["Macro F1-Score", f"{macro_f1}%"])
            writer.writerow([])

            writer.writerow(["=== Per-Person Metrics ==="])
            writer.writerow(["Person", "Precision (%)", "Recall (%)", "F1-Score (%)", "Support"])
            for idx, label in enumerate(labels):
                writer.writerow([label, round(precision[idx]*100, 2), round(recall[idx]*100, 2),
                                round(f1[idx]*100, 2), int(support[idx])])
            writer.writerow([])

            writer.writerow(["=== Confusion Matrix ==="])
            writer.writerow(["Actual \\ Predicted"] + list(labels))
            for i, label in enumerate(labels):
                writer.writerow([label] + [str(v) for v in cm[i]])

        print(f"  [OK] Report saved to: {filepath}")
    except Exception as e:
        print(f"  [ERROR] Failed to export: {e}")


if __name__ == "__main__":
    evaluate_model()
