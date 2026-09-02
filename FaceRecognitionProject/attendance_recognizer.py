"""
Attendance Recognizer - Smart Attendance System
================================================
Main attendance-taking module. Combines:
  - Camera input (webcam / CCTV)
  - Adaptive face recognition scanning
  - Attendance engine (confirmation + marking)
  - Real-time video overlay with status

Run this during a lecture to automatically mark attendance.
"""
import os
import sys
import time

sys.stdout.reconfigure(line_buffering=True)

import cv2
import numpy as np
import face_recognition

from camera_config import (
    get_camera_source,
    ACTIVE_CAMERA,
    DISPLAY_WIDTH,
    DISPLAY_HEIGHT,
    SHOW_FPS,
    CONFIDENCE_THRESHOLD,
    RECOGNITION_TOLERANCE,
    FACE_DETECTION_MODEL,
    LECTURE_DURATION_MINUTES,
    RECONNECT_DELAY_SECONDS,
    MAX_RECONNECT_ATTEMPTS,
)
from database import Database
from attendance_engine import AttendanceEngine


def _open_camera(source):
    """Open a camera source with retry logic for CCTV streams.

    Args:
        source: Camera index (int for webcam) or RTSP URL (str for CCTV).

    Returns:
        cv2.VideoCapture object, or None if failed.
    """
    if isinstance(source, int):
        # Webcam
        cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
        if not cap.isOpened():
            # Try next index
            cap = cv2.VideoCapture(source + 1, cv2.CAP_DSHOW)
        return cap if cap.isOpened() else None
    else:
        # CCTV / RTSP stream
        for attempt in range(MAX_RECONNECT_ATTEMPTS):
            cap = cv2.VideoCapture(source)
            if cap.isOpened():
                return cap
            print(f"  [RETRY] Camera connection attempt {attempt + 1}/{MAX_RECONNECT_ATTEMPTS}...")
            time.sleep(RECONNECT_DELAY_SECONDS)
        return None


def _draw_overlay(frame, face_results, engine, fps):
    """Draw the attendance overlay on the camera frame.

    Args:
        frame: The camera frame (BGR image).
        face_results: List of dicts with face info and recognition results.
        engine: AttendanceEngine instance for progress data.
        fps: Current FPS value.
    """
    h, w = frame.shape[:2]

    # Semi-transparent header bar
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 80), (30, 30, 30), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    # Header text
    elapsed = engine.get_elapsed_minutes()
    _, phase = engine.get_current_phase()
    next_scan = engine.get_time_until_next_scan()

    cv2.putText(frame, "SMART ATTENDANCE", (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    cv2.putText(frame, f"Camera: {ACTIVE_CAMERA}", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
    cv2.putText(frame, f"Phase: {phase} | Next scan: {next_scan}s",
                (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)

    if SHOW_FPS:
        cv2.putText(frame, f"FPS: {int(fps)}", (w - 100, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Progress bar at the top
    progress_text = engine.get_progress()
    cv2.putText(frame, progress_text, (w - 250, 55),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

    # Elapsed time
    mins = int(elapsed)
    secs = int((elapsed - mins) * 60)
    cv2.putText(frame, f"Elapsed: {mins:02d}:{secs:02d}", (w - 250, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

    # Draw face bounding boxes with status
    for result in face_results:
        top, right, bottom, left = result["location"]
        name = result.get("name", "UNKNOWN")
        confidence = result.get("confidence", 0)
        status = result.get("status", "unknown")

        # Color based on status
        if status == "marked" or status == "already_marked":
            color = (0, 255, 0)       # Green — attendance confirmed
            label = f"{name} {confidence:.0f}% [MARKED]"
        elif status == "confirming":
            color = (0, 255, 255)     # Yellow — being confirmed
            count = result.get("count", 0)
            required = result.get("required", 3)
            label = f"{name} {confidence:.0f}% ({count}/{required})"
        elif status == "low_confidence":
            color = (0, 165, 255)     # Orange — too low confidence
            label = f"{name}? {confidence:.0f}%"
        else:
            color = (0, 0, 255)       # Red — unknown face
            label = "UNKNOWN"

        # Draw bounding box
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

        # Draw label background
        label_h = 30
        cv2.rectangle(frame, (left, bottom), (right, bottom + label_h), color, -1)
        cv2.putText(frame, label, (left + 4, bottom + 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1)

    # Bottom status bar
    overlay2 = frame.copy()
    cv2.rectangle(overlay2, (0, h - 40), (w, h), (30, 30, 30), -1)
    cv2.addWeighted(overlay2, 0.7, frame, 0.3, 0, frame)

    marked_count = len(engine.marked_this_session)
    total = engine.total_students
    bar_text = f"Attendance: {marked_count}/{total}"
    cv2.putText(frame, bar_text, (10, h - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(frame, "q=quit | r=remaining", (w - 220, h - 15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)

    # Progress bar visual
    if total > 0:
        bar_width = w - 20
        fill_width = int(bar_width * (marked_count / total))
        cv2.rectangle(frame, (10, h - 45), (10 + bar_width, h - 42), (80, 80, 80), -1)
        cv2.rectangle(frame, (10, h - 45), (10 + fill_width, h - 42), (0, 255, 0), -1)


def start_attendance():
    """Start the attendance recognition session.

    This is the main function that:
    1. Opens the camera
    2. Loads face vectors from database
    3. Runs adaptive scanning over the lecture duration
    4. Marks attendance for recognized students
    5. Shows real-time overlay on the video feed
    """
    print()
    print("=" * 55)
    print("   START ATTENDANCE SESSION")
    print("=" * 55)
    print()

    # Initialize database and engine
    db = Database()

    total_students = db.get_student_count()
    if total_students == 0:
        print("  [ERROR] No students enrolled! Please enroll students first.")
        db.close()
        return

    face_data = db.load_all_face_vectors()
    enrolled_with_faces = len(face_data)

    if enrolled_with_faces == 0:
        print("  [ERROR] No students have face vectors! Please enroll with photos.")
        db.close()
        return

    print(f"  Students enrolled: {total_students}")
    print(f"  Students with face data: {enrolled_with_faces}")
    print(f"  Lecture duration: {LECTURE_DURATION_MINUTES} minutes")
    print(f"  Confidence threshold: {CONFIDENCE_THRESHOLD}%")
    print()

    # Prepare face data for comparison
    known_ids = list(face_data.keys())
    known_names = [face_data[sid]["name"] for sid in known_ids]
    known_vectors = [face_data[sid]["vector"] for sid in known_ids]

    # Open camera
    source = get_camera_source()
    print(f"  Opening camera ({ACTIVE_CAMERA})...", end=" ", flush=True)
    cap = _open_camera(source)

    if cap is None:
        print("\n  [ERROR] Cannot open camera!")
        db.close()
        return

    print("OK")
    print()
    print("  Attendance session started!")
    print(f"  Scanning {enrolled_with_faces} student faces...")
    print("  Press 'q' in the camera window to stop.")
    print("  Press 'r' to show remaining students.")
    print()
    print("  " + "─" * 45)

    # Initialize engine
    engine = AttendanceEngine(db)

    prev_time = time.time()
    window_name = "Smart Attendance System - Press q to quit"

    while True:
        ret, frame = cap.read()

        if not ret:
            # Try to reconnect for CCTV streams
            if isinstance(source, str):
                print("  [WARNING] Camera frame lost. Attempting reconnect...")
                cap.release()
                cap = _open_camera(source)
                if cap is None:
                    print("  [ERROR] Camera reconnection failed!")
                    break
                continue
            else:
                break

        # Resize for display
        frame = cv2.resize(frame, (DISPLAY_WIDTH, DISPLAY_HEIGHT))

        # Calculate FPS
        curr_time = time.time()
        fps = 1.0 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
        prev_time = curr_time

        face_results = []

        # Only run face recognition during scan intervals
        if engine.should_scan_now():
            engine.record_scan()

            # Shrink frame for faster face detection
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # Detect faces
            face_locations = face_recognition.face_locations(
                rgb_small, model=FACE_DETECTION_MODEL
            )

            if face_locations:
                # Generate encodings for detected faces
                face_encodings = face_recognition.face_encodings(
                    rgb_small, face_locations
                )

                detected_ids = set()

                for face_enc, face_loc in zip(face_encodings, face_locations):
                    # Scale face location back to display size
                    top, right, bottom, left = face_loc
                    top *= 2
                    right *= 2
                    bottom *= 2
                    left *= 2

                    # Compare against all known faces
                    distances = face_recognition.face_distance(known_vectors, face_enc)

                    if len(distances) > 0:
                        best_idx = np.argmin(distances)
                        best_distance = distances[best_idx]
                        confidence = round((1.0 - best_distance) * 100, 2)

                        if best_distance <= RECOGNITION_TOLERANCE:
                            # Recognized!
                            student_id = known_ids[best_idx]
                            student_name = known_names[best_idx]
                            detected_ids.add(student_id)

                            # Process through attendance engine
                            result = engine.process_recognition(
                                student_id, student_name, confidence
                            )

                            face_results.append({
                                "location": (top, right, bottom, left),
                                "name": student_name,
                                "confidence": confidence,
                                "status": result["action"],
                                "count": result.get("count", 0),
                                "required": result.get("required", 3),
                            })
                        else:
                            # Face detected but no match above threshold
                            face_results.append({
                                "location": (top, right, bottom, left),
                                "name": "UNKNOWN",
                                "confidence": confidence,
                                "status": "unknown",
                            })
                    else:
                        face_results.append({
                            "location": (top, right, bottom, left),
                            "name": "UNKNOWN",
                            "confidence": 0,
                            "status": "unknown",
                        })

                # Reset counters for students not seen in this scan
                engine.reset_undetected(detected_ids)

        # Draw overlay (always, even between scans)
        _draw_overlay(frame, face_results, engine, fps)

        # Show frame
        cv2.imshow(window_name, frame)

        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if key == ord('r'):
            # Show remaining students in terminal
            remaining = engine.get_remaining_students()
            print()
            print(f"  Remaining ({len(remaining)} students):")
            for sid, name in remaining:
                print(f"    - {name} ({sid})")
            print()

        # Check if window was closed
        try:
            if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break
        except cv2.error:
            break

        # Check if lecture is over
        if engine.is_lecture_over():
            print()
            print("  [INFO] Lecture duration reached. Ending session...")
            break

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()

    # Print session summary
    engine.finalize_session()

    db.close()


if __name__ == "__main__":
    start_attendance()
