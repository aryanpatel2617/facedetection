"""
Camera Configuration for Smart Attendance System
=================================================
Configure camera sources (webcam / CCTV RTSP) and lecture timing settings.
Switch between cameras by changing ACTIVE_CAMERA.
"""

# ─────────────────────────────────────────────
#  Camera Sources
# ─────────────────────────────────────────────
# Add your CCTV RTSP URL here when ready.
# For prototype testing, keep ACTIVE_CAMERA = "webcam"

CAMERA_SOURCES = {
    "webcam": 0,
    # Example CCTV RTSP URLs (uncomment and edit when you have a camera):
    # "cctv": "rtsp://admin:password@192.168.1.100:554/stream1",
    # "cctv_hd": "rtsp://admin:password@192.168.1.100:554/stream2",
}

# Which camera to use — change this to switch between webcam and CCTV
ACTIVE_CAMERA = "webcam"


# ─────────────────────────────────────────────
#  Lecture Mode Timing (Adaptive Scanning)
# ─────────────────────────────────────────────
# The system scans less frequently over time to save CPU.

LECTURE_DURATION_MINUTES = 50          # Total lecture duration

# Phase 1 — AGGRESSIVE (first few minutes, most students arrive)
AGGRESSIVE_PHASE_MINUTES = 5           # Duration of aggressive phase
SCAN_INTERVAL_AGGRESSIVE = 2           # Scan every 2 seconds

# Phase 2 — RELAXED (catch latecomers)
RELAXED_PHASE_MINUTES = 30             # Duration of relaxed phase
SCAN_INTERVAL_RELAXED = 10             # Scan every 10 seconds

# Phase 3 — IDLE (most already marked, just monitoring)
SCAN_INTERVAL_IDLE = 30                # Scan every 30 seconds


# ─────────────────────────────────────────────
#  Recognition Settings
# ─────────────────────────────────────────────

CONFIDENCE_THRESHOLD = 60              # Minimum confidence % to consider a match
CONSECUTIVE_SCANS_REQUIRED = 3         # Must be detected in N scans before marking
FACE_DETECTION_MODEL = "hog"           # "hog" (fast, CPU) or "cnn" (accurate, GPU)
RECOGNITION_TOLERANCE = 0.5            # face_recognition distance threshold (lower = stricter)


# ─────────────────────────────────────────────
#  CCTV Auto-Reconnect Settings
# ─────────────────────────────────────────────

RECONNECT_DELAY_SECONDS = 5            # Wait before retrying a dropped CCTV stream
MAX_RECONNECT_ATTEMPTS = 10            # Give up after N failed reconnects


# ─────────────────────────────────────────────
#  Display Settings
# ─────────────────────────────────────────────

DISPLAY_WIDTH = 960                    # Camera feed display width
DISPLAY_HEIGHT = 540                   # Camera feed display height
SHOW_FPS = True                        # Show FPS counter on video feed


def get_camera_source():
    """Get the currently configured camera source."""
    source = CAMERA_SOURCES.get(ACTIVE_CAMERA)
    if source is None:
        print(f"  [WARNING] Camera '{ACTIVE_CAMERA}' not found in CAMERA_SOURCES.")
        print(f"  Falling back to webcam (index 0).")
        return 0
    return source


def get_scan_interval(elapsed_minutes):
    """Get the appropriate scan interval based on elapsed lecture time.

    Args:
        elapsed_minutes: Minutes since lecture/attendance session started.

    Returns:
        Scan interval in seconds and the current phase name.
    """
    if elapsed_minutes < AGGRESSIVE_PHASE_MINUTES:
        return SCAN_INTERVAL_AGGRESSIVE, "AGGRESSIVE"
    elif elapsed_minutes < RELAXED_PHASE_MINUTES:
        return SCAN_INTERVAL_RELAXED, "RELAXED"
    else:
        return SCAN_INTERVAL_IDLE, "IDLE"
