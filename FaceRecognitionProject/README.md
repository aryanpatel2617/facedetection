# Face Recognition System with Name Identification

This is a complete Machine Learning mini-project built using Python, OpenCV, and `face_recognition`. It allows you to register users, capture their face data, train a recognition model, and perform real-time face recognition to log attendance.

## Features

- **User Authentication**: Simple login screen.
- **Dashboard**: Modern dark-themed dashboard to navigate through the modules.
- **Register User**: Save user details (ID, Name, Department, Age) to a CSV dataset.
- **Capture Dataset**: Automatically capture 50 face images using a webcam and Haar cascades for fast face detection.
- **Train Model**: Generate 128-d face encodings using the state-of-the-art `face_recognition` library and serialize the model.
- **Real-Time Recognition**: Detects and recognizes faces in real-time, displaying confidence percentage, FPS counter, and drawing color-coded bounding boxes.
- **Attendance Logging**: Automatically logs the date and time when a registered user is recognized, preventing duplicate same-day entries.
- **Attendance History**: View and search past attendance records in a GUI table, with CSV export functionality.

## Technology Stack

- **Programming Language**: Python 3.11+
- **Machine Learning**: `face_recognition`, `opencv-python`, `numpy`
- **Data Management**: `pandas`
- **GUI Framework**: `tkinter`

## Project Structure

```
FaceRecognitionProject/
├── app.py                 # Main entry point and routing
├── login.py               # Authentication module
├── dashboard.py           # Home dashboard interface
├── register.py            # User registration form
├── capture_faces.py       # Webcam face capture script
├── train_model.py         # Face encoding and model serialization
├── recognize.py           # Real-time face recognition engine
├── attendance.py          # Attendance history and export module
├── utils.py               # Shared utility functions and UI styling
├── requirements.txt       # Project dependencies
├── dataset/               # Folder storing captured face images
├── models/                # Folder storing the trained model (trained_model.pkl)
├── attendance/            # Folder storing attendance.csv
└── users/                 # Folder storing users.csv
```

## Installation

1. Clone or download this repository.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   > **Note on Windows**: Installing `face_recognition` requires `dlib`, which needs CMake and Visual Studio C++ Build Tools installed on your system.

## How to Run

1. Open a terminal in the project directory.
2. Run the main application:
   ```bash
   python app.py
   ```
3. Login using the default credentials:
   - **Username**: `admin`
   - **Password**: `admin`
4. Register a new person and capture their images.
5. Click **Train Dataset** to generate the face model.
6. Click **Start Face Recognition** to test the system and log attendance.

## Future Scope
- Integration with external databases (e.g., MySQL, Firebase).
- Advanced liveness detection to prevent photo spoofing.
- Adding a notification module (Email/SMS) on attendance logging.
