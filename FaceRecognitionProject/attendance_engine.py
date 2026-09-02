"""
Attendance Engine - Smart Attendance System
============================================
Core attendance logic for lecture-mode attendance:
  - Adaptive scan intervals (aggressive → relaxed → idle)
  - 3-scan consecutive confirmation before marking
  - Daily deduplication (marks each student only once per day)
  - Real-time progress tracking
"""
import time
from datetime import datetime

from database import Database
from camera_config import (
    CONFIDENCE_THRESHOLD,
    CONSECUTIVE_SCANS_REQUIRED,
    LECTURE_DURATION_MINUTES,
    AGGRESSIVE_PHASE_MINUTES,
    RELAXED_PHASE_MINUTES,
    SCAN_INTERVAL_AGGRESSIVE,
    SCAN_INTERVAL_RELAXED,
    SCAN_INTERVAL_IDLE,
)


class AttendanceEngine:
    """Manages attendance over a lecture session.

    Tracks which students have been recognized, confirms identities
    over multiple scans, and marks attendance in the database.
    """

    def __init__(self, db=None):
        """Initialize the attendance engine.

        Args:
            db: Database instance. Creates a new one if not provided.
        """
        self.db = db or Database()
        self.start_time = datetime.now()
        self.last_scan_time = 0  # Unix timestamp of last scan

        # Confirmation tracking: {student_id: consecutive_scan_count}
        self.pending = {}

        # Already marked this session: {student_id: (name, time_str, confidence)}
        self.marked_this_session = {}

        # Pre-load data
        self.face_data = self.db.load_all_face_vectors()
        self.total_students = self.db.get_student_count()
        self.already_marked_today = self.db.get_marked_today()

        # Copy already-marked-today into session tracking
        for sid in self.already_marked_today:
            if sid in self.face_data:
                self.marked_this_session[sid] = (
                    self.face_data[sid]["name"], "before session", 0
                )

        # Session log: list of (timestamp, message) for terminal display
        self.log = []

    def get_elapsed_minutes(self):
        """Get minutes elapsed since session start."""
        return (datetime.now() - self.start_time).total_seconds() / 60

    def get_current_phase(self):
        """Get the current scanning phase.

        Returns:
            Tuple of (scan_interval_seconds, phase_name)
        """
        elapsed = self.get_elapsed_minutes()

        # If all students are marked, switch to idle
        if len(self.marked_this_session) >= self.total_students:
            return SCAN_INTERVAL_IDLE, "COMPLETE"

        if elapsed < AGGRESSIVE_PHASE_MINUTES:
            return SCAN_INTERVAL_AGGRESSIVE, "AGGRESSIVE"
        elif elapsed < RELAXED_PHASE_MINUTES:
            return SCAN_INTERVAL_RELAXED, "RELAXED"
        else:
            return SCAN_INTERVAL_IDLE, "IDLE"

    def should_scan_now(self):
        """Check if it's time for the next scan.

        Returns:
            True if enough time has passed since the last scan.
        """
        interval, _ = self.get_current_phase()
        return (time.time() - self.last_scan_time) >= interval

    def record_scan(self):
        """Mark that a scan just happened."""
        self.last_scan_time = time.time()

    def get_time_until_next_scan(self):
        """Get seconds remaining until next scan."""
        interval, _ = self.get_current_phase()
        elapsed = time.time() - self.last_scan_time
        remaining = max(0, interval - elapsed)
        return int(remaining)

    def is_lecture_over(self):
        """Check if the lecture duration has been exceeded."""
        return self.get_elapsed_minutes() >= LECTURE_DURATION_MINUTES

    def process_recognition(self, student_id, name, confidence):
        """Process a face recognition result from a scan.

        This handles the 3-scan confirmation logic:
        - If confidence < threshold → ignored
        - If already marked today → ignored
        - If first/second consecutive detection → increment counter
        - If third consecutive detection → mark attendance

        Args:
            student_id: The recognized student's ID
            name: The student's name
            confidence: Recognition confidence percentage

        Returns:
            Dict with status info:
                {"action": "marked" | "confirming" | "already_marked" | "low_confidence",
                 "count": current_consecutive_count,
                 "required": CONSECUTIVE_SCANS_REQUIRED}
        """
        # Check confidence threshold
        if confidence < CONFIDENCE_THRESHOLD:
            # Reset consecutive counter on low confidence
            self.pending.pop(student_id, None)
            return {
                "action": "low_confidence",
                "confidence": confidence,
                "threshold": CONFIDENCE_THRESHOLD
            }

        # Already marked this session/today
        if student_id in self.marked_this_session:
            return {
                "action": "already_marked",
                "name": name,
                "count": CONSECUTIVE_SCANS_REQUIRED,
                "required": CONSECUTIVE_SCANS_REQUIRED
            }

        # Increment consecutive counter
        current_count = self.pending.get(student_id, 0) + 1
        self.pending[student_id] = current_count

        # Check if confirmed (reached required consecutive scans)
        if current_count >= CONSECUTIVE_SCANS_REQUIRED:
            # Mark attendance in database
            time_str = datetime.now().strftime("%H:%M:%S")
            was_new = self.db.mark_attendance(student_id, confidence)

            self.marked_this_session[student_id] = (name, time_str, confidence)
            self.pending.pop(student_id, None)

            # Log the event
            marked_count = len(self.marked_this_session)
            log_msg = f"✓ MARKED: {name} ({confidence}%) — {marked_count}/{self.total_students}"
            self.log.append((datetime.now().strftime("%H:%M:%S"), log_msg))
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] {log_msg}")

            return {
                "action": "marked",
                "name": name,
                "confidence": confidence,
                "count": current_count,
                "required": CONSECUTIVE_SCANS_REQUIRED,
                "total_marked": marked_count
            }
        else:
            # Still confirming
            log_msg = f"⏳ Confirming: {name} ({confidence}%) — {current_count}/{CONSECUTIVE_SCANS_REQUIRED}"
            self.log.append((datetime.now().strftime("%H:%M:%S"), log_msg))
            print(f"  [{datetime.now().strftime('%H:%M:%S')}] {log_msg}")

            return {
                "action": "confirming",
                "name": name,
                "confidence": confidence,
                "count": current_count,
                "required": CONSECUTIVE_SCANS_REQUIRED
            }

    def reset_undetected(self, detected_ids):
        """Reset consecutive counters for students not seen in this scan.

        This ensures a student must be seen in CONSECUTIVE scans,
        not just N scans total.

        Args:
            detected_ids: Set of student IDs detected in the current scan.
        """
        missing = set(self.pending.keys()) - detected_ids
        for sid in missing:
            self.pending.pop(sid, None)

    def get_progress(self):
        """Get a progress summary string.

        Returns:
            String like "12/60 marked (20.0%)"
        """
        marked = len(self.marked_this_session)
        total = self.total_students
        pct = round((marked / total * 100), 1) if total > 0 else 0
        return f"{marked}/{total} marked ({pct}%)"

    def get_remaining_students(self):
        """Get list of students not yet marked this session.

        Returns:
            List of (student_id, name) tuples.
        """
        remaining = []
        for sid, data in self.face_data.items():
            if sid not in self.marked_this_session:
                remaining.append((sid, data["name"]))
        return sorted(remaining, key=lambda x: x[1])

    def get_session_summary(self):
        """Get a full session summary dict.

        Returns:
            Dict with session statistics.
        """
        elapsed = self.get_elapsed_minutes()
        _, phase = self.get_current_phase()

        return {
            "elapsed_minutes": round(elapsed, 1),
            "phase": phase,
            "marked_count": len(self.marked_this_session),
            "total_students": self.total_students,
            "remaining_count": self.total_students - len(self.marked_this_session),
            "pending_confirmations": len(self.pending),
            "total_scans": len(self.log),
        }

    def finalize_session(self):
        """Finalize the attendance session.

        Returns:
            Session summary dict.
        """
        summary = self.get_session_summary()

        print()
        print("  " + "═" * 50)
        print("  SESSION COMPLETE")
        print("  " + "═" * 50)
        print(f"  Duration:   {summary['elapsed_minutes']} minutes")
        print(f"  Marked:     {summary['marked_count']}/{summary['total_students']}")
        print(f"  Remaining:  {summary['remaining_count']} students not marked")
        print(f"  Scans:      {summary['total_scans']} recognition events")
        print("  " + "═" * 50)

        return summary
