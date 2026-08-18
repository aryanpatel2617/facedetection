import cv2
import face_recognition
import pickle
import numpy as np
import os
import pandas as pd
from datetime import datetime
import time
from utils import show_error

class RecognizeApp:
    def __init__(self, root):
        self.root = root
        # We don't need a UI for this class, just run the OpenCV window
        self.root.withdraw()
        self.start_recognition()
        
    def start_recognition(self):
        model_path = os.path.join("models", "trained_model.pkl")
        if not os.path.exists(model_path):
            show_error("Error", "Model not found. Please train the dataset first.")
            self.root.destroy()
            return
            
        try:
            with open(model_path, 'rb') as f:
                data = pickle.load(f)
        except Exception as e:
            show_error("Error", f"Failed to load model: {e}")
            self.root.destroy()
            return
            
        known_encodings = data.get("encodings", [])
        known_names = data.get("names", [])
        
        if not known_encodings:
            show_error("Error", "Model is empty. Please train the dataset first.")
            self.root.destroy()
            return
            
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            # Fallback to index 1 if 0 doesn't work
            cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

        if not cap.isOpened():
            show_error("Error", "Webcam not found!")
            self.root.destroy()
            return
            
        attendance_path = os.path.join("attendance", "attendance.csv")
        
        process_this_frame = True
        face_locations = []
        face_encodings = []
        face_names = []
        confidences = []
        
        prev_time = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Resize frame to 1/4 size for faster face recognition processing
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Only process every other frame of video to save time
            if process_this_frame:
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                
                face_names = []
                confidences = []
                
                for face_encoding in face_encodings:
                    # See if the face is a match for the known face(s)
                    matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=0.5)
                    name = "UNKNOWN"
                    confidence_percent = 0
                    
                    face_distances = face_recognition.face_distance(known_encodings, face_encoding)
                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = known_names[best_match_index]
                            
                            # Calculate a confidence percentage
                            confidence = face_distances[best_match_index]
                            # Map distance 0.0-0.5 to confidence 100%-0% roughly
                            # Note: smaller distance means higher confidence
                            confidence_percent = round((1.0 - confidence) * 100, 2)
                            
                            # Mark attendance
                            self.mark_attendance(name, attendance_path)
                            
                    face_names.append(name)
                    confidences.append(confidence_percent)
                    
            process_this_frame = not process_this_frame
            
            # FPS calculation
            curr_time = time.time()
            fps = 1 / (curr_time - prev_time) if (curr_time - prev_time) > 0 else 0
            prev_time = curr_time
            
            # Display the results
            for (top, right, bottom, left), name, conf in zip(face_locations, face_names, confidences):
                # Scale back up face locations since the frame we detected in was scaled to 1/4 size
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                
                color = (0, 255, 0) if name != "UNKNOWN" else (0, 0, 255)
                
                # Draw a box around the face
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                
                # Draw a label with a name below the face
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                
                display_text = f"{name} {conf}%" if name != "UNKNOWN" else "UNKNOWN"
                cv2.putText(frame, display_text, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)
                
            # Draw FPS
            cv2.putText(frame, f"FPS: {int(fps)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            
            cv2.imshow('Face Recognition - Press q to exit', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
            # Check if window was closed by the user clicking 'X'
            if cv2.getWindowProperty('Face Recognition - Press q to exit', cv2.WND_PROP_VISIBLE) < 1:
                break

        cap.release()
        cv2.destroyAllWindows()
        self.root.destroy()
        
    def mark_attendance(self, name, csv_path):
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')
        
        try:
            if not os.path.exists(csv_path):
                df = pd.DataFrame(columns=["Name", "Date", "Time"])
                df.to_csv(csv_path, index=False)
                
            df = pd.read_csv(csv_path)
            
            # Filter today's attendance for this user
            today_records = df[(df['Name'] == name) & (df['Date'] == date_str)]
            
            if today_records.empty:
                new_record = pd.DataFrame({"Name": [name], "Date": [date_str], "Time": [time_str]})
                new_record.to_csv(csv_path, mode='a', header=False, index=False)
                print(f"Logged attendance for {name}")
        except Exception as e:
            print(f"Error logging attendance: {e}")
