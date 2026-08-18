"""
Face Recognition - Terminal Version
Opens webcam and recognizes faces in real-time.
"""
import os
import pickle
import cv2
import face_recognition
import numpy as np
import time


def recognize_faces():
    """Start live face recognition via webcam."""
    print()
    print("=" * 50)
    print("   FACE RECOGNITION")
    print("=" * 50)
    print()

    model_path = os.path.join("models", "trained_model.pkl")
    if not os.path.exists(model_path):
        print("  [ERROR] Model not found. Please train the dataset first.")
        return

    try:
        with open(model_path, 'rb') as f:
            data = pickle.load(f)
    except Exception as e:
        print(f"  [ERROR] Failed to load model: {e}")
        return

    known_encodings = data.get("encodings", [])
    known_names = data.get("names", [])

    if not known_encodings:
        print("  [ERROR] Model is empty. Please train the dataset first.")
        return

    print(f"  Model loaded: {len(known_encodings)} encodings, {len(set(known_names))} person(s)")
    print("  Opening camera... Press 'q' in the camera window to exit.\n")

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("  [ERROR] Webcam not found!")
        return

    process_this_frame = True
    face_locations = []
    face_encodings_list = []
    face_names = []
    confidences = []
    prev_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        if process_this_frame:
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings_list = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            confidences = []

            for face_encoding in face_encodings_list:
                matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
                name = "UNKNOWN"
                confidence_percent = 0

                face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    if matches[best_match_index]:
                        name = known_names[best_match_index]
                        confidence = face_distances[best_match_index]
                        confidence_percent = round((1.0 - confidence) * 100, 2)

                face_names.append(name)
                confidences.append(confidence_percent)

        process_this_frame = not process_this_frame

        # FPS
        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time = curr_time

        # Draw results on frame
        for (top, right, bottom, left), name, conf in zip(face_locations, face_names, confidences):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            color = (0, 255, 0) if name != "UNKNOWN" else (0, 0, 255)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
            display_text = f"{name} {conf}%" if name != "UNKNOWN" else "UNKNOWN"
            cv2.putText(frame, display_text, (left + 6, bottom - 6),
                        cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

        cv2.putText(frame, f"FPS: {int(fps)}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)

        cv2.imshow('Face Recognition - Press q to exit', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if cv2.getWindowProperty('Face Recognition - Press q to exit', cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()
    print("\n  Recognition stopped.")


if __name__ == "__main__":
    recognize_faces()
