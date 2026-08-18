import os
import shutil
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from utils import (BG_COLOR, BG_SECONDARY, CARD_COLOR, TEXT_COLOR, TEXT_SECONDARY,
                   PRIMARY_COLOR, DANGER_COLOR, BORDER_COLOR,
                   FONT_TITLE, FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_HEADER,
                   create_button, create_separator, show_error, show_info, center_window)

class ManageUsersApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Manage Registered Users")
        self.root.configure(bg=BG_COLOR)
        center_window(self.root, 800, 550)
        self.root.grab_set()
        
        self.csv_path = os.path.join("users", "users.csv")
        self.df = pd.DataFrame()
        self.load_data()
        self.create_widgets()
        
    def load_data(self):
        if os.path.exists(self.csv_path) and os.path.getsize(self.csv_path) > 0:
            try:
                self.df = pd.read_csv(self.csv_path)
            except Exception:
                pass
                
    def create_widgets(self):
        # Top accent bar
        tk.Frame(self.root, bg=DANGER_COLOR, height=3).pack(fill="x")
        
        # Header
        header = tk.Frame(self.root, bg=BG_SECONDARY, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        lbl_icon = tk.Label(header, text="⚙", font=("Segoe UI", 22), bg=BG_SECONDARY)
        lbl_icon.pack(side="left", padx=(25, 10))
        
        header_text = tk.Frame(header, bg=BG_SECONDARY)
        header_text.pack(side="left", fill="y", pady=8)
        tk.Label(header_text, text="MANAGE USERS", font=FONT_HEADER, bg=BG_SECONDARY, fg=TEXT_COLOR).pack(anchor="w")
        
        self.lbl_count = tk.Label(header_text, text="Loading...", font=FONT_SMALL, bg=BG_SECONDARY, fg=TEXT_SECONDARY)
        self.lbl_count.pack(anchor="w")
        
        tk.Frame(self.root, bg=BORDER_COLOR, height=1).pack(fill="x")
        
        # Toolbar
        toolbar = tk.Frame(self.root, bg=BG_COLOR)
        toolbar.pack(fill="x", padx=25, pady=(15, 10))
        
        btn_refresh = create_button(toolbar, "🔄 Refresh", self.refresh_data, bg_color=PRIMARY_COLOR, width=10, height=1)
        btn_refresh.pack(side="left", padx=3)
        
        # Table
        table_outer = tk.Frame(self.root, bg=BORDER_COLOR)
        table_outer.pack(fill="both", expand=True, padx=25, pady=(5, 10))
        
        table_frame = tk.Frame(table_outer, bg=CARD_COLOR)
        table_frame.pack(padx=1, pady=1, fill="both", expand=True)
        
        # Treeview styling
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Users.Treeview",
                        background=CARD_COLOR,
                        foreground=TEXT_COLOR,
                        rowheight=35,
                        fieldbackground=CARD_COLOR,
                        borderwidth=0,
                        font=FONT_BODY)
        style.map("Users.Treeview", background=[("selected", DANGER_COLOR)])
        style.configure("Users.Treeview.Heading",
                        font=("Segoe UI", 11, "bold"),
                        background=BG_SECONDARY,
                        foreground=TEXT_COLOR,
                        relief="flat",
                        borderwidth=0)
        style.map("Users.Treeview.Heading", background=[("active", "#2d333b")])
        
        self.tree = ttk.Treeview(table_frame, columns=("ID", "Name", "Department", "Age"), show="headings", style="Users.Treeview")
        self.tree.heading("ID", text="  #  ID")
        self.tree.heading("Name", text="  👤  Name")
        self.tree.heading("Department", text="  🏢  Department")
        self.tree.heading("Age", text="  📅  Age")
        
        self.tree.column("ID", anchor="center", width=80)
        self.tree.column("Name", anchor="center", width=220)
        self.tree.column("Department", anchor="center", width=220)
        self.tree.column("Age", anchor="center", width=80)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Bottom Action Bar
        bottom_bar = tk.Frame(self.root, bg=BG_SECONDARY, height=55)
        bottom_bar.pack(fill="x", side="bottom")
        bottom_bar.pack_propagate(False)
        
        btn_delete = create_button(bottom_bar, "🗑  Delete Selected", self.delete_selected, bg_color=DANGER_COLOR, width=16, height=1)
        btn_delete.pack(side="left", padx=25, pady=12)
        
        self.lbl_selected = tk.Label(bottom_bar, text="Select users to delete", font=FONT_SMALL, bg=BG_SECONDARY, fg=TEXT_SECONDARY)
        self.lbl_selected.pack(side="right", padx=25)
        
        self.populate_table()
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        
    def on_select(self, event):
        count = len(self.tree.selection())
        if count > 0:
            self.lbl_selected.config(text=f"{count} user(s) selected", fg=DANGER_COLOR)
        else:
            self.lbl_selected.config(text="Select users to delete", fg=TEXT_SECONDARY)
        
    def populate_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if not self.df.empty:
            for _, row in self.df.iterrows():
                self.tree.insert("", tk.END, values=(
                    row.get("ID", ""),
                    row.get("Name", ""),
                    row.get("Department", ""),
                    row.get("Age", "")
                ))
                
        count = len(self.df) if not self.df.empty else 0
        self.lbl_count.config(text=f"{count} registered users")
        
    def delete_selected(self):
        selected_items = self.tree.selection()
        if not selected_items:
            show_error("Error", "Please select one or more users to delete!")
            return
            
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete {len(selected_items)} user(s)?\n\nThis will also remove their captured face images."
        )
        if not confirm:
            return
            
        deleted_names = []
        for item in selected_items:
            values = self.tree.item(item, 'values')
            user_id, name = str(values[0]), str(values[1])
            
            mask = self.df['ID'].astype(str) == user_id
            self.df = self.df[~mask]
            
            user_folder = os.path.join("dataset", name)
            if os.path.exists(user_folder):
                try:
                    shutil.rmtree(user_folder)
                except Exception:
                    pass
                    
            deleted_names.append(name)
            self.tree.delete(item)
            
        try:
            self.df.to_csv(self.csv_path, index=False)
            show_info("Success", f"Deleted user(s): {', '.join(deleted_names)}")
        except Exception as e:
            show_error("Error", f"Failed to update file: {e}")
            
        self.populate_table()
        
    def refresh_data(self):
        self.load_data()
        self.populate_table()
