import os
import pickle
import tkinter as tk
from tkinter import ttk
import face_recognition
import threading
from utils import (BG_COLOR, BG_SECONDARY, CARD_COLOR, TEXT_COLOR, TEXT_SECONDARY,
                   PRIMARY_COLOR, WARNING_COLOR, BORDER_COLOR, SUCCESS_COLOR,
                   SECONDARY_COLOR,
                   FONT_TITLE, FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_HEADER,
                   create_button, create_separator, show_error, show_info, center_window)
from evaluate_model import EvaluateModelApp

class TrainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Train Face Model")
        self.root.configure(bg=BG_COLOR)
        center_window(self.root, 520, 440)
        self.root.resizable(False, False)
        
        # Store encodings for passing to the evaluator
        self.trained_encodings = []
        self.trained_names = []
        self.root.grab_set()
        
        self.create_widgets()
        
    def create_widgets(self):
        # Top accent bar
        tk.Frame(self.root, bg=WARNING_COLOR, height=3).pack(fill="x")
        
        # Header
        header = tk.Frame(self.root, bg=BG_SECONDARY, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        lbl_icon = tk.Label(header, text="🧠", font=("Segoe UI", 22), bg=BG_SECONDARY)
        lbl_icon.pack(side="left", padx=(25, 10))
        
        header_text = tk.Frame(header, bg=BG_SECONDARY)
        header_text.pack(side="left", fill="y", pady=8)
        tk.Label(header_text, text="TRAIN DATASET", font=FONT_HEADER, bg=BG_SECONDARY, fg=TEXT_COLOR).pack(anchor="w")
        tk.Label(header_text, text="Generate face encodings for recognition", font=FONT_SMALL, bg=BG_SECONDARY, fg=TEXT_SECONDARY).pack(anchor="w")
        
        tk.Frame(self.root, bg=BORDER_COLOR, height=1).pack(fill="x")
        
        # Content
        content = tk.Frame(self.root, bg=BG_COLOR, padx=40, pady=30)
        content.pack(fill="both", expand=True)
        
        # Status area
        status_card = tk.Frame(content, bg=CARD_COLOR, padx=20, pady=20)
        status_card.pack(fill="x")
        
        self.lbl_status = tk.Label(status_card, text="Ready to train", font=FONT_BODY_BOLD, bg=CARD_COLOR, fg=TEXT_COLOR)
        self.lbl_status.pack(pady=(0, 5))
        
        self.lbl_detail = tk.Label(status_card, text="Click the button below to start encoding faces", font=FONT_SMALL, bg=CARD_COLOR, fg=TEXT_SECONDARY)
        self.lbl_detail.pack(pady=(0, 15))
        
        # Progress bar styling
        style = ttk.Style()
        style.configure("Custom.Horizontal.TProgressbar",
                        troughcolor=BG_SECONDARY,
                        background=WARNING_COLOR,
                        borderwidth=0,
                        thickness=8)
        
        self.progress = ttk.Progressbar(status_card, orient="horizontal", length=350, mode="determinate", style="Custom.Horizontal.TProgressbar")
        self.progress.pack(pady=(0, 5))
        
        self.lbl_percent = tk.Label(status_card, text="0%", font=FONT_SMALL, bg=CARD_COLOR, fg=WARNING_COLOR)
        self.lbl_percent.pack()
        
        tk.Frame(content, bg=BG_COLOR, height=20).pack()
        
        self.btn_train = create_button(content, "⚡  Start Training", self.start_training_thread, bg_color=WARNING_COLOR, width=20, height=2)
        self.btn_train.pack()
        
    def start_training_thread(self):
        self.btn_train.config(state="disabled")
        self.lbl_status.config(text="Training in progress...", fg=WARNING_COLOR)
        self.lbl_detail.config(text="Loading images from dataset...")
        self.progress.config(value=0)
        self.lbl_percent.config(text="0%")
        threading.Thread(target=self.train_model, daemon=True).start()
        
    def train_model(self):
        dataset_path = "dataset"
        if not os.path.exists(dataset_path):
            self.root.after(0, lambda: show_error("Error", "Dataset folder not found!"))
            self.root.after(0, self.reset_ui)
            return
            
        known_face_encodings = []
        known_face_names = []
        
        persons = [d for d in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, d))]
        
        if not persons:
            self.root.after(0, lambda: show_error("Error", "No user data found in dataset!"))
            self.root.after(0, self.reset_ui)
            return
            
        total_persons = len(persons)
        
        for i, person_name in enumerate(persons):
            self.root.after(0, lambda name=person_name: self.lbl_status.config(text=f"Encoding: {name}"))
            self.root.after(0, lambda name=person_name, idx=i+1, total=total_persons: 
                          self.lbl_detail.config(text=f"Processing person {idx}/{total}: {name}"))
            
            person_folder = os.path.join(dataset_path, person_name)
            images = os.listdir(person_folder)
            
            for img_name in images:
                if not img_name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue
                
                img_path = os.path.join(person_folder, img_name)
                
                try:
                    # Load image
                    image = face_recognition.load_image_file(img_path)
                    # Get face encodings
                    encodings = face_recognition.face_encodings(image)
                    if len(encodings) > 0:
                        known_face_encodings.append(encodings[0])
                        known_face_names.append(person_name)
                except Exception as e:
                    print(f"Error encoding {img_path}: {e}")
                    
            # update progress
            progress_val = int(((i + 1) / total_persons) * 100)
            self.root.after(0, lambda p=progress_val: self.progress.config(value=p))
            self.root.after(0, lambda p=progress_val: self.lbl_percent.config(text=f"{p}%"))
            
        if not known_face_encodings:
            self.root.after(0, lambda: show_error("Error", "Could not find valid faces in dataset."))
            self.root.after(0, self.reset_ui)
            return

        # Save model
        model_dir = "models"
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)
            
        try:
            with open(os.path.join(model_dir, "trained_model.pkl"), 'wb') as f:
                pickle.dump({"encodings": known_face_encodings, "names": known_face_names}, f)
            
            # Store encodings for the evaluator
            self.trained_encodings = known_face_encodings
            self.trained_names = known_face_names
                
            self.root.after(0, lambda: self.lbl_status.config(text="✓ Training Complete!", fg=SUCCESS_COLOR))
            self.root.after(0, lambda: self.lbl_detail.config(text=f"Encoded {len(known_face_encodings)} faces for {total_persons} person(s)"))
            self.root.after(0, lambda: self.lbl_percent.config(text="100%", fg=SUCCESS_COLOR))
            self.root.after(0, lambda: show_info("Success", "Model trained and saved successfully."))
            self.root.after(0, self._show_post_training_buttons)
        except Exception as e:
            self.root.after(0, lambda err=e: show_error("Error", f"Failed to save model: {err}"))
            self.root.after(0, self.reset_ui)
        
    def _show_post_training_buttons(self):
        """Replace the train button with View Metrics and Close buttons."""
        self.btn_train.pack_forget()
        
        btn_frame = tk.Frame(self.btn_train.master, bg=BG_COLOR)
        btn_frame.pack(pady=(0, 5))
        
        btn_metrics = create_button(btn_frame, "📊  View Metrics", self._open_metrics, bg_color=SECONDARY_COLOR, width=18, height=2)
        btn_metrics.pack(side="left", padx=(0, 8))
        
        btn_close = create_button(btn_frame, "✕  Close", self.root.destroy, bg_color="#666666", width=10, height=2)
        btn_close.pack(side="left")
    
    def _open_metrics(self):
        """Open the evaluation window with preloaded encodings from training."""
        top = tk.Toplevel(self.root)
        EvaluateModelApp(top, preloaded_data={
            "encodings": self.trained_encodings,
            "names": self.trained_names
        })

    def reset_ui(self):
        self.btn_train.config(state="normal")
        self.progress.config(value=0)
        self.lbl_percent.config(text="0%", fg=WARNING_COLOR)
        self.lbl_status.config(text="Ready to train", fg=TEXT_COLOR)
        self.lbl_detail.config(text="Click the button below to start encoding faces")
