import os
import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from utils import (BG_COLOR, BG_SECONDARY, CARD_COLOR, TEXT_COLOR, TEXT_SECONDARY,
                   PRIMARY_COLOR, SECONDARY_COLOR, DANGER_COLOR, BORDER_COLOR,
                   FONT_TITLE, FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_HEADER,
                   create_button, create_styled_entry, create_separator,
                   show_error, show_info, center_window)

class AttendanceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Attendance History")
        self.root.configure(bg=BG_COLOR)
        center_window(self.root, 850, 650)
        
        self.attendance_file = os.path.join("attendance", "attendance.csv")
        self.df = pd.DataFrame()
        self.load_data()
        
        self.create_widgets()
        
    def load_data(self):
        if os.path.exists(self.attendance_file) and os.path.getsize(self.attendance_file) > 0:
            try:
                self.df = pd.read_csv(self.attendance_file)
            except Exception:
                pass
                
    def create_widgets(self):
        # Top accent bar
        tk.Frame(self.root, bg=SECONDARY_COLOR, height=3).pack(fill="x")
        
        # Header
        header = tk.Frame(self.root, bg=BG_SECONDARY, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        lbl_icon = tk.Label(header, text="📋", font=("Segoe UI", 22), bg=BG_SECONDARY)
        lbl_icon.pack(side="left", padx=(25, 10))
        
        header_text = tk.Frame(header, bg=BG_SECONDARY)
        header_text.pack(side="left", fill="y", pady=8)
        tk.Label(header_text, text="ATTENDANCE HISTORY", font=FONT_HEADER, bg=BG_SECONDARY, fg=TEXT_COLOR).pack(anchor="w")
        
        self.lbl_count = tk.Label(header_text, text="Loading...", font=FONT_SMALL, bg=BG_SECONDARY, fg=TEXT_SECONDARY)
        self.lbl_count.pack(anchor="w")
        
        tk.Frame(self.root, bg=BORDER_COLOR, height=1).pack(fill="x")
        
        # ── Toolbar ──
        toolbar = tk.Frame(self.root, bg=BG_COLOR)
        toolbar.pack(fill="x", padx=25, pady=(15, 10))
        
        # Search
        lbl_search = tk.Label(toolbar, text="🔍", font=("Segoe UI", 14), bg=BG_COLOR)
        lbl_search.pack(side="left")
        
        self.search_frame = create_styled_entry(toolbar, width=25)
        self.search_frame.pack(side="left", padx=(5, 10))
        self.entry_search = self.search_frame.entry
        
        btn_search = create_button(toolbar, "Search", self.search_data, bg_color=SECONDARY_COLOR, width=8, height=1)
        btn_search.pack(side="left", padx=3)
        
        btn_reset = create_button(toolbar, "Reset", self.reset_search, bg_color="#666666", width=8, height=1)
        btn_reset.pack(side="left", padx=3)
        
        # Right side buttons
        btn_export = create_button(toolbar, "📥 Export", self.export_excel, bg_color=SECONDARY_COLOR, width=10, height=1)
        btn_export.pack(side="right", padx=3)
        
        # ── Table ──
        table_outer = tk.Frame(self.root, bg=BORDER_COLOR)
        table_outer.pack(fill="both", expand=True, padx=25, pady=(5, 10))
        
        table_frame = tk.Frame(table_outer, bg=CARD_COLOR)
        table_frame.pack(padx=1, pady=1, fill="both", expand=True)
        
        # Treeview styling
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Custom.Treeview",
                        background=CARD_COLOR,
                        foreground=TEXT_COLOR,
                        rowheight=35,
                        fieldbackground=CARD_COLOR,
                        borderwidth=0,
                        font=FONT_BODY)
        style.map("Custom.Treeview", background=[("selected", SECONDARY_COLOR)])
        style.configure("Custom.Treeview.Heading",
                        font=("Segoe UI", 11, "bold"),
                        background=BG_SECONDARY,
                        foreground=TEXT_COLOR,
                        relief="flat",
                        borderwidth=0)
        style.map("Custom.Treeview.Heading", background=[("active", "#2d333b")])
        
        self.tree = ttk.Treeview(table_frame, columns=("Name", "Date", "Time"), show="headings", style="Custom.Treeview")
        self.tree.heading("Name", text="  👤  Name")
        self.tree.heading("Date", text="  📅  Date")
        self.tree.heading("Time", text="  🕐  Time")
        
        self.tree.column("Name", anchor="center", width=280)
        self.tree.column("Date", anchor="center", width=180)
        self.tree.column("Time", anchor="center", width=180)
        
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # ── Bottom Action Bar ──
        bottom_bar = tk.Frame(self.root, bg=BG_SECONDARY, height=55)
        bottom_bar.pack(fill="x", side="bottom")
        bottom_bar.pack_propagate(False)
        
        btn_delete = create_button(bottom_bar, "🗑  Delete Selected", self.delete_selected, bg_color=DANGER_COLOR, width=16, height=1)
        btn_delete.pack(side="left", padx=25, pady=12)
        
        btn_delete_all = create_button(bottom_bar, "🗑  Delete All", self.delete_all, bg_color="#8b0000", width=12, height=1)
        btn_delete_all.pack(side="left", padx=5, pady=12)
        
        self.lbl_selected = tk.Label(bottom_bar, text="Select rows to delete", font=FONT_SMALL, bg=BG_SECONDARY, fg=TEXT_SECONDARY)
        self.lbl_selected.pack(side="right", padx=25)
        
        self.populate_table()
        
        # Bind selection event
        self.tree.bind("<<TreeviewSelect>>", self.on_select)
        
        # Bind Enter key for search
        self.entry_search.bind("<Return>", lambda e: self.search_data())
        
    def on_select(self, event):
        count = len(self.tree.selection())
        if count > 0:
            self.lbl_selected.config(text=f"{count} row(s) selected", fg=DANGER_COLOR)
        else:
            self.lbl_selected.config(text="Select rows to delete", fg=TEXT_SECONDARY)
        
    def populate_table(self, data_frame=None):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        df_to_show = self.df if data_frame is None else data_frame
        
        if not df_to_show.empty:
            for _, row in df_to_show.iterrows():
                self.tree.insert("", tk.END, values=(row.get("Name", ""), row.get("Date", ""), row.get("Time", "")))
                
        count = len(df_to_show) if not df_to_show.empty else 0
        self.lbl_count.config(text=f"{count} records found")
                
    def search_data(self):
        query = self.entry_search.get().strip().lower()
        if not query:
            self.populate_table()
            return
            
        if not self.df.empty:
            filtered_df = self.df[
                self.df["Name"].astype(str).str.lower().str.contains(query, na=False) |
                self.df["Date"].astype(str).str.lower().str.contains(query, na=False)
            ]
            self.populate_table(filtered_df)
            
    def reset_search(self):
        self.entry_search.delete(0, tk.END)
        self.populate_table()
            
    def delete_selected(self):
        selected_items = self.tree.selection()
        if not selected_items:
            show_error("Error", "Please select one or more rows to delete!")
            return
            
        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {len(selected_items)} record(s)?")
        if not confirm:
            return
            
        rows_to_delete = []
        for item in selected_items:
            values = self.tree.item(item, 'values')
            rows_to_delete.append(values)
            self.tree.delete(item)
            
        for values in rows_to_delete:
            name, date, time_val = values
            mask = (self.df['Name'].astype(str) == str(name)) & \
                   (self.df['Date'].astype(str) == str(date)) & \
                   (self.df['Time'].astype(str) == str(time_val))
            self.df = self.df[~mask]
            
        try:
            self.df.to_csv(self.attendance_file, index=False)
            show_info("Success", f"Deleted {len(rows_to_delete)} record(s) successfully!")
            self.populate_table()
        except Exception as e:
            show_error("Error", f"Failed to update file: {e}")
            
    def delete_all(self):
        if self.df.empty:
            show_error("Error", "No records to delete!")
            return
            
        confirm = messagebox.askyesno("Confirm Delete All", "Are you sure you want to delete ALL attendance records?\n\nThis action cannot be undone!")
        if not confirm:
            return
            
        self.df = pd.DataFrame(columns=["Name", "Date", "Time"])
        
        try:
            self.df.to_csv(self.attendance_file, index=False)
            self.populate_table()
            show_info("Success", "All attendance records have been deleted!")
        except Exception as e:
            show_error("Error", f"Failed to update file: {e}")
            
    def export_excel(self):
        if self.df.empty:
            show_error("Error", "No data to export!")
            return
            
        try:
            export_path = os.path.join("attendance", f"attendance_export.csv")
            self.df.to_csv(export_path, index=False)
            show_info("Success", f"Data exported successfully to\n{export_path}")
        except Exception as e:
            show_error("Error", f"Failed to export data: {e}")
