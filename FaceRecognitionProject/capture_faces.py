import cv2
import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog
import pandas as pd
from PIL import Image, ImageTk
from utils import (BG_COLOR, BG_SECONDARY, CARD_COLOR, CARD_HOVER, TEXT_COLOR, TEXT_SECONDARY,
                   PRIMARY_COLOR, SECONDARY_COLOR, BORDER_COLOR, BORDER_LIGHT,
                   SUCCESS_COLOR, DANGER_COLOR, WARNING_COLOR,
                   FONT_TITLE, FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_HEADER,
                   create_button, create_separator, show_error, show_info, center_window)

class CaptureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Capture Faces")
        self.root.configure(bg=BG_COLOR)
        center_window(self.root, 560, 520)
        self.root.resizable(False, False)
        self.root.grab_set()
        
        self.users_df = pd.DataFrame()
        self.uploaded_files = []  # Track uploaded image paths for preview
        self.load_users()
        self.create_widgets()
        
    def load_users(self):
        try:
            csv_path = os.path.join("users", "users.csv")
            if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
                self.users_df = pd.read_csv(csv_path)
        except Exception:
            pass
            
    def create_widgets(self):
        # Top accent bar
        tk.Frame(self.root, bg=SECONDARY_COLOR, height=3).pack(fill="x")
        
        # Header
        header = tk.Frame(self.root, bg=BG_SECONDARY, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        lbl_icon = tk.Label(header, text="📸", font=("Segoe UI", 22), bg=BG_SECONDARY)
        lbl_icon.pack(side="left", padx=(25, 10))
        
        header_text = tk.Frame(header, bg=BG_SECONDARY)
        header_text.pack(side="left", fill="y", pady=8)
        tk.Label(header_text, text="CAPTURE FACES", font=FONT_HEADER, bg=BG_SECONDARY, fg=TEXT_COLOR).pack(anchor="w")
        tk.Label(header_text, text="Upload images or use camera to capture faces", font=FONT_SMALL, bg=BG_SECONDARY, fg=TEXT_SECONDARY).pack(anchor="w")
        
        tk.Frame(self.root, bg=BORDER_COLOR, height=1).pack(fill="x")
        
        # Content
        content = tk.Frame(self.root, bg=BG_COLOR, padx=30, pady=20)
        content.pack(fill="both", expand=True)
        
        # ── User Selection ──
        lbl_select = tk.Label(content, text="SELECT USER", font=("Segoe UI", 9, "bold"), bg=BG_COLOR, fg=TEXT_SECONDARY)
        lbl_select.pack(anchor="w", pady=(0, 5))
        
        names = []
        if not self.users_df.empty:
            names = self.users_df['Name'].tolist()
        
        # Style the combobox
        style = ttk.Style()
        style.configure("Custom.TCombobox", fieldbackground=BG_SECONDARY, background=BG_SECONDARY, foreground=TEXT_COLOR)
            
        self.cb_users = ttk.Combobox(content, values=names, font=FONT_BODY, state="readonly")
        self.cb_users.pack(pady=(0, 15), ipady=5, fill="x")
        
        tk.Frame(content, bg=BORDER_COLOR, height=1).pack(fill="x", pady=(0, 15))
        
        # ── Method Selection Label ──
        tk.Label(content, text="CHOOSE METHOD", font=("Segoe UI", 9, "bold"), bg=BG_COLOR, fg=TEXT_SECONDARY).pack(anchor="w", pady=(0, 10))
        
        # ── Two Option Cards ──
        cards_row = tk.Frame(content, bg=BG_COLOR)
        cards_row.pack(fill="x", pady=(0, 15))
        cards_row.columnconfigure(0, weight=1)
        cards_row.columnconfigure(1, weight=1)
        
        # Card 1: Upload Images
        self._create_option_card(
            cards_row, col=0,
            icon="📁", title="Upload Images",
            subtitle="Select photos from your device",
            command=self.upload_images,
            accent_color=PRIMARY_COLOR
        )
        
        # Card 2: Capture from Camera
        self._create_option_card(
            cards_row, col=1,
            icon="📷", title="Capture Face",
            subtitle="Take 50 photos via webcam",
            command=self.start_capture,
            accent_color=SECONDARY_COLOR
        )
        
        # ── Upload status area (hidden by default) ──
        self.upload_status_frame = tk.Frame(content, bg=BG_COLOR)
        self.upload_status_frame.pack(fill="x", pady=(0, 5))
        
        self.lbl_upload_status = tk.Label(self.upload_status_frame, text="", font=FONT_SMALL, bg=BG_COLOR, fg=TEXT_SECONDARY)
        self.lbl_upload_status.pack(anchor="w")
        
        # ── Upload preview area ──
        self.preview_frame = tk.Frame(content, bg=BG_COLOR)
        self.preview_frame.pack(fill="x", pady=(0, 10))
        
        # ── Hint ──
        lbl_hint = tk.Label(content, text="💡 For best results, include different angles and lighting", font=FONT_SMALL, bg=BG_COLOR, fg=TEXT_SECONDARY)
        lbl_hint.pack(pady=(5, 0), side="bottom")
    
    def _create_option_card(self, parent, col, icon, title, subtitle, command, accent_color):
        """Creates a clickable option card in the grid."""
        card_outer = tk.Frame(parent, bg=BORDER_COLOR)
        card_outer.grid(row=0, column=col, padx=6, sticky="nsew")
        
        card = tk.Frame(card_outer, bg=CARD_COLOR, cursor="hand2")
        card.pack(padx=1, pady=1, fill="both", expand=True)
        
        # Accent strip
        accent = tk.Frame(card, bg=accent_color, height=3)
        accent.pack(fill="x")
        
        inner = tk.Frame(card, bg=CARD_COLOR, padx=15, pady=15)
        inner.pack(fill="both", expand=True)
        
        lbl_icon = tk.Label(inner, text=icon, font=("Segoe UI", 28), bg=CARD_COLOR)
        lbl_icon.pack(pady=(5, 8))
        
        lbl_title = tk.Label(inner, text=title, font=FONT_BODY_BOLD, bg=CARD_COLOR, fg=TEXT_COLOR)
        lbl_title.pack()
        
        lbl_sub = tk.Label(inner, text=subtitle, font=FONT_SMALL, bg=CARD_COLOR, fg=TEXT_SECONDARY)
        lbl_sub.pack(pady=(2, 5))
        
        # Hover effects
        all_widgets = [card, inner, lbl_icon, lbl_title, lbl_sub, accent]
        
        def on_enter(e):
            card.config(bg=CARD_HOVER)
            inner.config(bg=CARD_HOVER)
            for w in [lbl_icon, lbl_title, lbl_sub]:
                w.config(bg=CARD_HOVER)
            card_outer.config(bg=accent_color)
                
        def on_leave(e):
            card.config(bg=CARD_COLOR)
            inner.config(bg=CARD_COLOR)
            for w in [lbl_icon, lbl_title, lbl_sub]:
                w.config(bg=CARD_COLOR)
            card_outer.config(bg=BORDER_COLOR)
        
        for widget in all_widgets:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", lambda e, cmd=command: cmd())
        
        return card_outer

    # ──────────────────────────────────────────────────────────────
    #                   UPLOAD IMAGES
    # ──────────────────────────────────────────────────────────────

    def upload_images(self):
        """Open file dialog to select images and save them to the dataset."""
        selected_name = self.cb_users.get()
        if not selected_name:
            show_error("Error", "Please select a user first!")
            return
        
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.bmp *.webp"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("PNG files", "*.png"),
            ("All files", "*.*")
        ]
        
        file_paths = filedialog.askopenfilenames(
            title="Select Face Images",
            filetypes=filetypes,
            parent=self.root
        )
        
        if not file_paths:
            return
        
        user_folder = os.path.join("dataset", selected_name)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
        
        # Count existing images to continue numbering
        existing = [f for f in os.listdir(user_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))]
        start_count = len(existing)
        
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        saved_count = 0
        skipped_count = 0
        
        for file_path in file_paths:
            try:
                # Read and detect face
                img = cv2.imread(file_path)
                if img is None:
                    skipped_count += 1
                    continue
                
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(80, 80))
                
                if len(faces) == 0:
                    # No face detected — save the whole image anyway with a note
                    # (face_recognition library may still detect it during training)
                    start_count += 1
                    dest_path = os.path.join(user_folder, f"img_{start_count}.jpg")
                    shutil.copy2(file_path, dest_path)
                    saved_count += 1
                else:
                    # Save each detected face as a separate cropped image
                    for (x, y, w, h) in faces:
                        start_count += 1
                        face_img = img[y:y+h, x:x+w]
                        dest_path = os.path.join(user_folder, f"img_{start_count}.jpg")
                        cv2.imwrite(dest_path, face_img)
                        saved_count += 1
                        
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                skipped_count += 1
        
        # Update status
        self._show_upload_result(saved_count, skipped_count, selected_name)
        
        # Show thumbnails preview
        self._show_upload_preview(user_folder, saved_count)
    
    def _show_upload_result(self, saved, skipped, name):
        """Update the status label with upload results."""
        if saved > 0:
            status_text = f"✓ {saved} face image(s) saved for {name}"
            if skipped > 0:
                status_text += f"  ·  {skipped} skipped"
            self.lbl_upload_status.config(text=status_text, fg=SUCCESS_COLOR)
        else:
            self.lbl_upload_status.config(text="✕ No valid face images found", fg=DANGER_COLOR)
    
    def _show_upload_preview(self, user_folder, count):
        """Show thumbnail previews of the last few uploaded images."""
        # Clear previous previews
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        
        if count == 0:
            return
        
        # Get the last few images
        all_images = sorted([f for f in os.listdir(user_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))], reverse=True)
        preview_images = all_images[:6]  # Show up to 6 thumbnails
        
        tk.Label(self.preview_frame, text="RECENT UPLOADS", font=("Segoe UI", 8, "bold"),
                 bg=BG_COLOR, fg=TEXT_SECONDARY).pack(anchor="w", pady=(0, 5))
        
        thumb_row = tk.Frame(self.preview_frame, bg=BG_COLOR)
        thumb_row.pack(anchor="w")
        
        self._thumbnail_refs = []  # Keep references to prevent garbage collection
        
        for img_name in preview_images:
            img_path = os.path.join(user_folder, img_name)
            try:
                pil_img = Image.open(img_path)
                pil_img.thumbnail((50, 50))
                tk_img = ImageTk.PhotoImage(pil_img)
                self._thumbnail_refs.append(tk_img)
                
                thumb_frame = tk.Frame(thumb_row, bg=BORDER_COLOR)
                thumb_frame.pack(side="left", padx=3)
                
                lbl = tk.Label(thumb_frame, image=tk_img, bg=CARD_COLOR, padx=2, pady=2)
                lbl.pack()
            except Exception:
                pass
        
        # Show total count
        total_images = len(all_images)
        tk.Label(self.preview_frame, text=f"Total: {total_images} images in dataset",
                 font=FONT_SMALL, bg=BG_COLOR, fg=TEXT_SECONDARY).pack(anchor="w", pady=(5, 0))

    # ──────────────────────────────────────────────────────────────
    #                   CAPTURE FROM CAMERA
    # ──────────────────────────────────────────────────────────────

    def start_capture(self):
        selected_name = self.cb_users.get()
        if not selected_name:
            show_error("Error", "Please select a user first!")
            return
            
        user_folder = os.path.join("dataset", selected_name)
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
        
        # Count existing images to continue numbering
        existing = [f for f in os.listdir(user_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.webp'))]
        start_count = len(existing)
            
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            # Fallback to index 1 if 0 doesn't work
            cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

        if not cap.isOpened():
            show_error("Error", "Webcam not found!")
            return
            
        # Using Haar Cascade for fast face detection during capture
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        count = 0
        max_images = 50
        
        show_info("Info", "Camera will open. Look at the camera and turn your head slightly. Wait until 50 images are captured.")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(100, 100))
            
            for (x, y, w, h) in faces:
                count += 1
                # Save just the cropped face to dataset
                face_img = frame[y:y+h, x:x+w]
                img_path = os.path.join(user_folder, f"img_{start_count + count}.jpg")
                cv2.imwrite(img_path, face_img)
                
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, f"Captured: {count}/{max_images}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
            cv2.imshow('Capturing Faces - Press q to cancel', frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
            # Check if window was closed by the user clicking 'X'
            if cv2.getWindowProperty('Capturing Faces - Press q to cancel', cv2.WND_PROP_VISIBLE) < 1:
                break
            if count >= max_images:
                break
                
        cap.release()
        cv2.destroyAllWindows()
        
        if count > 0:
            show_info("Success", f"Successfully captured {count} images for {selected_name}.")
            self.lbl_upload_status.config(text=f"✓ {count} face(s) captured via camera for {selected_name}", fg=SUCCESS_COLOR)
        else:
            show_error("Error", "No faces were captured.")
