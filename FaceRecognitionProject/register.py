import tkinter as tk
from tkinter import messagebox
import pandas as pd
import os
from utils import (BG_COLOR, BG_SECONDARY, CARD_COLOR, TEXT_COLOR, TEXT_SECONDARY,
                   PRIMARY_COLOR, BORDER_COLOR, FONT_TITLE, FONT_BODY, FONT_BODY_BOLD,
                   FONT_SMALL, FONT_HEADER,
                   create_button, create_styled_entry, create_card, create_separator,
                   show_info, show_error, center_window)

class RegisterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Register New Person")
        self.root.configure(bg=BG_COLOR)
        center_window(self.root, 500, 620)
        self.root.resizable(False, False)
        self.root.grab_set()
        
        self.create_widgets()
        
    def create_widgets(self):
        # Top accent bar
        tk.Frame(self.root, bg=PRIMARY_COLOR, height=3).pack(fill="x")
        
        # Header
        header = tk.Frame(self.root, bg=BG_SECONDARY, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        lbl_icon = tk.Label(header, text="👤", font=("Segoe UI", 22), bg=BG_SECONDARY)
        lbl_icon.pack(side="left", padx=(25, 10))
        
        header_text = tk.Frame(header, bg=BG_SECONDARY)
        header_text.pack(side="left", fill="y", pady=8)
        tk.Label(header_text, text="REGISTER NEW PERSON", font=FONT_HEADER, bg=BG_SECONDARY, fg=TEXT_COLOR).pack(anchor="w")
        tk.Label(header_text, text="Fill in the details below", font=FONT_SMALL, bg=BG_SECONDARY, fg=TEXT_SECONDARY).pack(anchor="w")
        
        tk.Frame(self.root, bg=BORDER_COLOR, height=1).pack(fill="x")
        
        # Form Card
        card = create_card(self.root, pad_x=30, pad_y=25)
        card.outer.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Form fields
        fields = [
            ("PERSON ID", "Enter unique ID (e.g., 001)"),
            ("FULL NAME", "Enter full name"),
            ("DEPARTMENT", "Enter department"),
            ("AGE", "Enter age"),
        ]
        
        self.entries = []
        
        for label_text, placeholder in fields:
            lbl = tk.Label(card, text=label_text, font=("Segoe UI", 9, "bold"), bg=CARD_COLOR, fg=TEXT_SECONDARY)
            lbl.pack(anchor="w", pady=(10, 3))
            
            entry_frame = create_styled_entry(card)
            entry_frame.pack(fill="x", pady=(0, 5))
            self.entries.append(entry_frame.entry)
        
        self.entry_id, self.entry_name, self.entry_dept, self.entry_age = self.entries
        
        # Separator
        create_separator(card, BORDER_COLOR).pack(fill="x", pady=(15, 15))
        
        # Buttons
        btn_frame = tk.Frame(card, bg=CARD_COLOR)
        btn_frame.pack(fill="x")
        
        btn_save = create_button(btn_frame, "✓  Save Record", self.save_data, bg_color=PRIMARY_COLOR, width=18, height=2)
        btn_save.pack(side="left")
        
        btn_cancel = create_button(btn_frame, "✕  Cancel", self.root.destroy, bg_color="#666666", width=12, height=2)
        btn_cancel.pack(side="right")
        
        # Focus first field
        self.entry_id.focus_set()
        
    def save_data(self):
        user_id = self.entry_id.get().strip()
        name = self.entry_name.get().strip()
        dept = self.entry_dept.get().strip()
        age = self.entry_age.get().strip()
        
        if not all([user_id, name, dept, age]):
            show_error("Error", "All fields are required!")
            return
            
        csv_path = os.path.join("users", "users.csv")
        
        # Check if user already exists
        if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
            try:
                df = pd.read_csv(csv_path)
                if str(user_id) in df['ID'].astype(str).values:
                    show_error("Error", f"User ID {user_id} already exists!")
                    return
                if name in df['Name'].values:
                    show_error("Error", f"User Name '{name}' already exists!")
                    return
            except Exception as e:
                pass 
                
        # Append to CSV
        try:
            new_data = pd.DataFrame({"ID": [user_id], "Name": [name], "Department": [dept], "Age": [age]})
            file_exists = os.path.exists(csv_path)
            new_data.to_csv(csv_path, mode='a', header=not file_exists or os.path.getsize(csv_path) == 0, index=False)
            show_info("Success", f"User {name} registered successfully!\nYou can now capture their faces.")
            self.root.destroy()
        except Exception as e:
            show_error("Error", f"Failed to save data: {e}")
