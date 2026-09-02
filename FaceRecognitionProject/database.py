"""
Database Layer for Smart Attendance System
===========================================
SQLite-based storage for students (with face vectors) and attendance records.
Replaces the old users.csv + trained_model.pkl approach.

The database file (attendance_system.db) is auto-created on first use.
"""
import os
import io
import sqlite3
from datetime import datetime, date

import numpy as np


# ─────────────────────────────────────────────
#  NumPy ↔ SQLite Adapters
# ─────────────────────────────────────────────
# SQLite cannot store NumPy arrays natively, so we convert them to/from binary.

def _adapt_numpy_array(arr):
    """Convert a NumPy array to binary for SQLite storage."""
    buf = io.BytesIO()
    np.save(buf, arr)
    buf.seek(0)
    return sqlite3.Binary(buf.read())


def _convert_numpy_array(blob):
    """Convert binary data from SQLite back to a NumPy array."""
    buf = io.BytesIO(blob)
    buf.seek(0)
    return np.load(buf)


# Register the custom types with sqlite3
sqlite3.register_adapter(np.ndarray, _adapt_numpy_array)
sqlite3.register_converter("NPARRAY", _convert_numpy_array)


class Database:
    """SQLite database manager for the Smart Attendance System.

    Handles:
    - Student registration with 128D face vectors
    - Daily attendance records with deduplication
    - Queries for reports (daily, date range, absent students)
    """

    def __init__(self, db_path=None):
        """Initialize database connection and create tables if needed.

        Args:
            db_path: Path to the SQLite database file.
                     Defaults to 'attendance_system.db' in the project root.
        """
        if db_path is None:
            # Place database in the project root (parent of FaceRecognitionProject/)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_root, "attendance_system.db")

        self.db_path = db_path
        self.conn = sqlite3.connect(
            db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def _create_tables(self):
        """Create the students and attendance tables if they don't exist."""
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                department  TEXT,
                age         INTEGER,
                photo_path  TEXT,
                face_vector NPARRAY,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id  TEXT NOT NULL,
                date        DATE NOT NULL,
                time        TIME NOT NULL,
                confidence  REAL,
                status      TEXT DEFAULT 'PRESENT',
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                UNIQUE(student_id, date)
            )
        """)

        self.conn.commit()

    # ─────────────────────────────────────────
    #  Student Management
    # ─────────────────────────────────────────

    def add_student(self, student_id, name, department, age, photo_path, face_vector):
        """Add a new student with their face vector.

        Args:
            student_id: Unique student ID (e.g., "001")
            name: Full name
            department: Department name
            age: Age
            photo_path: Path to the student's photo file
            face_vector: 128D NumPy array from face_recognition

        Returns:
            True if successful, False if student ID already exists.
        """
        try:
            self.conn.execute(
                """INSERT INTO students (id, name, department, age, photo_path, face_vector)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (str(student_id), name, department, age, photo_path, face_vector)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def update_student_face(self, student_id, photo_path, face_vector):
        """Update a student's face vector (re-enrollment with better photo).

        Args:
            student_id: Student ID to update
            photo_path: Path to the new photo
            face_vector: New 128D face vector

        Returns:
            True if the student was found and updated, False otherwise.
        """
        cursor = self.conn.execute(
            """UPDATE students SET face_vector = ?, photo_path = ? WHERE id = ?""",
            (face_vector, photo_path, str(student_id))
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def get_student(self, student_id):
        """Get a single student's details.

        Returns:
            Dict with student info, or None if not found.
        """
        cursor = self.conn.execute(
            """SELECT id, name, department, age, photo_path, face_vector, created_at
               FROM students WHERE id = ?""",
            (str(student_id),)
        )
        row = cursor.fetchone()
        if row:
            return {
                "id": row[0], "name": row[1], "department": row[2],
                "age": row[3], "photo_path": row[4], "face_vector": row[5],
                "created_at": row[6]
            }
        return None

    def get_all_students(self):
        """Get all registered students.

        Returns:
            List of dicts with student info (without face vectors for efficiency).
        """
        cursor = self.conn.execute(
            """SELECT id, name, department, age, photo_path, created_at
               FROM students ORDER BY name"""
        )
        return [
            {"id": r[0], "name": r[1], "department": r[2],
             "age": r[3], "photo_path": r[4], "created_at": r[5]}
            for r in cursor.fetchall()
        ]

    def get_student_count(self):
        """Get the total number of registered students."""
        cursor = self.conn.execute("SELECT COUNT(*) FROM students")
        return cursor.fetchone()[0]

    def delete_student(self, student_id):
        """Delete a student and all their attendance records.

        Returns:
            True if a student was deleted, False if not found.
        """
        cursor = self.conn.execute(
            "DELETE FROM students WHERE id = ?", (str(student_id),)
        )
        self.conn.commit()
        return cursor.rowcount > 0

    def student_exists(self, student_id):
        """Check if a student ID already exists."""
        cursor = self.conn.execute(
            "SELECT 1 FROM students WHERE id = ?", (str(student_id),)
        )
        return cursor.fetchone() is not None

    # ─────────────────────────────────────────
    #  Face Vector Operations
    # ─────────────────────────────────────────

    def load_all_face_vectors(self):
        """Load all face vectors into memory for recognition.

        This is called once at the start of an attendance session.
        60 students × 128 floats × 8 bytes = ~60KB in RAM — negligible.

        Returns:
            Dict: {student_id: {"name": str, "vector": np.ndarray}}
        """
        cursor = self.conn.execute(
            """SELECT id, name, face_vector FROM students
               WHERE face_vector IS NOT NULL"""
        )
        result = {}
        for row in cursor.fetchall():
            student_id, name, vector = row
            if vector is not None:
                result[student_id] = {"name": name, "vector": vector}
        return result

    # ─────────────────────────────────────────
    #  Attendance Operations
    # ─────────────────────────────────────────

    def mark_attendance(self, student_id, confidence, status="PRESENT"):
        """Mark attendance for a student for today.

        The UNIQUE(student_id, date) constraint prevents duplicate entries.

        Args:
            student_id: Student ID
            confidence: Recognition confidence percentage
            status: Attendance status (default: "PRESENT")

        Returns:
            True if attendance was marked, False if already marked today.
        """
        today = date.today().isoformat()
        now = datetime.now().strftime("%H:%M:%S")

        try:
            self.conn.execute(
                """INSERT INTO attendance (student_id, date, time, confidence, status)
                   VALUES (?, ?, ?, ?, ?)""",
                (str(student_id), today, now, confidence, status)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Already marked today (UNIQUE constraint violated)
            return False

    def is_marked_today(self, student_id):
        """Check if a student's attendance is already marked for today."""
        today = date.today().isoformat()
        cursor = self.conn.execute(
            "SELECT 1 FROM attendance WHERE student_id = ? AND date = ?",
            (str(student_id), today)
        )
        return cursor.fetchone() is not None

    def get_attendance_by_date(self, target_date=None):
        """Get all attendance records for a specific date.

        Args:
            target_date: Date string (YYYY-MM-DD). Defaults to today.

        Returns:
            List of dicts with attendance info.
        """
        if target_date is None:
            target_date = date.today().isoformat()

        cursor = self.conn.execute(
            """SELECT a.student_id, s.name, s.department, a.time, a.confidence, a.status
               FROM attendance a
               JOIN students s ON a.student_id = s.id
               WHERE a.date = ?
               ORDER BY a.time""",
            (target_date,)
        )
        return [
            {"id": r[0], "name": r[1], "department": r[2],
             "time": r[3], "confidence": r[4], "status": r[5]}
            for r in cursor.fetchall()
        ]

    def get_marked_today(self):
        """Get set of student IDs already marked today.

        Returns:
            Set of student ID strings.
        """
        today = date.today().isoformat()
        cursor = self.conn.execute(
            "SELECT student_id FROM attendance WHERE date = ?", (today,)
        )
        return {row[0] for row in cursor.fetchall()}

    def get_absent_students(self, target_date=None):
        """Get students who were NOT marked present on a given date.

        Args:
            target_date: Date string (YYYY-MM-DD). Defaults to today.

        Returns:
            List of dicts with absent student info.
        """
        if target_date is None:
            target_date = date.today().isoformat()

        cursor = self.conn.execute(
            """SELECT id, name, department
               FROM students
               WHERE id NOT IN (
                   SELECT student_id FROM attendance WHERE date = ?
               )
               ORDER BY name""",
            (target_date,)
        )
        return [
            {"id": r[0], "name": r[1], "department": r[2]}
            for r in cursor.fetchall()
        ]

    def get_attendance_summary(self, target_date=None):
        """Get summary counts for a specific date.

        Returns:
            Dict with 'total', 'present', 'absent', 'percentage'.
        """
        if target_date is None:
            target_date = date.today().isoformat()

        total = self.get_student_count()
        present = self.conn.execute(
            "SELECT COUNT(*) FROM attendance WHERE date = ?", (target_date,)
        ).fetchone()[0]
        absent = total - present
        percentage = round((present / total * 100), 1) if total > 0 else 0

        return {
            "total": total,
            "present": present,
            "absent": absent,
            "percentage": percentage,
            "date": target_date
        }

    def get_student_attendance_range(self, student_id, start_date, end_date):
        """Get attendance records for a student over a date range.

        Args:
            student_id: Student ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            List of date strings when the student was present.
        """
        cursor = self.conn.execute(
            """SELECT date FROM attendance
               WHERE student_id = ? AND date BETWEEN ? AND ?
               ORDER BY date""",
            (str(student_id), start_date, end_date)
        )
        return [row[0] for row in cursor.fetchall()]

    def get_all_dates_with_attendance(self):
        """Get all dates that have attendance records.

        Returns:
            List of date strings (YYYY-MM-DD), most recent first.
        """
        cursor = self.conn.execute(
            "SELECT DISTINCT date FROM attendance ORDER BY date DESC"
        )
        return [row[0] for row in cursor.fetchall()]

    # ─────────────────────────────────────────
    #  Migration: Import from old CSV
    # ─────────────────────────────────────────

    def import_from_csv(self, csv_path):
        """Import existing users from the old users.csv file.

        This only imports student details (ID, Name, Department, Age).
        Face vectors must be generated separately via enrollment.

        Args:
            csv_path: Path to the users.csv file.

        Returns:
            Tuple of (imported_count, skipped_count).
        """
        import pandas as pd

        if not os.path.exists(csv_path):
            return 0, 0

        try:
            df = pd.read_csv(csv_path)
        except Exception:
            return 0, 0

        imported = 0
        skipped = 0

        for _, row in df.iterrows():
            student_id = str(row.get("ID", ""))
            name = str(row.get("Name", ""))
            dept = str(row.get("Department", ""))
            age = row.get("Age", None)

            if not student_id or not name:
                skipped += 1
                continue

            try:
                age_int = int(age) if age is not None else None
            except (ValueError, TypeError):
                age_int = None

            if self.add_student(student_id, name, dept, age_int, None, None):
                imported += 1
            else:
                skipped += 1

        return imported, skipped

    # ─────────────────────────────────────────
    #  Cleanup
    # ─────────────────────────────────────────

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
