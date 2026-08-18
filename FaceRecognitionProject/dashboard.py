import tkinter as tk
import time
from utils import (BG_COLOR, BG_SECONDARY, CARD_COLOR, CARD_HOVER, TEXT_COLOR, TEXT_SECONDARY,
                   PRIMARY_COLOR, SECONDARY_COLOR, DANGER_COLOR, WARNING_COLOR,
                   BORDER_COLOR, FONT_TITLE, FONT_SUBTITLE, FONT_BODY, FONT_BODY_BOLD,
                   FONT_SMALL, FONT_HEADER,
                   create_button, create_separator, center_window)
from register import RegisterApp
from capture_faces import CaptureApp
from train_model import TrainApp
from recognize import RecognizeApp
from attendance import AttendanceApp
from manage_users import ManageUsersApp
from evaluate_model import EvaluateModelApp

class DashboardApp:
    def __init__(self, root, on_logout):
        self.root = root
        self.on_logout = on_logout
        
        self.root.title("Face Recognition System - Dashboard")
        self.root.configure(bg=BG_COLOR)
        self.root.state('zoomed')  # Full screen (maximized)
        
        self.create_widgets()
        self.update_clock()
        
    def create_widgets(self):
        # Top accent bar
        accent_bar = tk.Frame(self.root, bg=PRIMARY_COLOR, height=3)
        accent_bar.pack(fill="x")
        
        # ── Header ──
        header = tk.Frame(self.root, bg=BG_SECONDARY, height=70)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Left side - title
        left_header = tk.Frame(header, bg=BG_SECONDARY)
        left_header.pack(side="left", padx=25, fill="y")
        
        lbl_icon = tk.Label(left_header, text="◉", font=("Segoe UI", 20), bg=BG_SECONDARY, fg=PRIMARY_COLOR)
        lbl_icon.pack(side="left", padx=(0, 10))
        
        title_container = tk.Frame(left_header, bg=BG_SECONDARY)
        title_container.pack(side="left", fill="y", pady=10)
        
        lbl_title = tk.Label(title_container, text="FACE RECOGNITION", font=FONT_HEADER, bg=BG_SECONDARY, fg=TEXT_COLOR)
        lbl_title.pack(anchor="w")
        
        lbl_sub = tk.Label(title_container, text="Dashboard  ·  Admin Panel", font=FONT_SMALL, bg=BG_SECONDARY, fg=TEXT_SECONDARY)
        lbl_sub.pack(anchor="w")
        
        # Right side - clock & logout
        right_header = tk.Frame(header, bg=BG_SECONDARY)
        right_header.pack(side="right", padx=25, fill="y")
        
        btn_logout = create_button(right_header, "⏻  Logout", self.on_logout, bg_color=DANGER_COLOR, width=10, height=1)
        btn_logout.pack(side="right", pady=18)
        
        self.lbl_clock = tk.Label(right_header, font=FONT_BODY_BOLD, bg=BG_SECONDARY, fg=SECONDARY_COLOR)
        self.lbl_clock.pack(side="right", padx=20, pady=18)
        
        # Separator
        sep = tk.Frame(self.root, bg=BORDER_COLOR, height=1)
        sep.pack(fill="x")
        
        # ── Welcome section ──
        welcome_frame = tk.Frame(self.root, bg=BG_COLOR)
        welcome_frame.pack(fill="x", padx=30, pady=(25, 10))
        
        lbl_welcome = tk.Label(welcome_frame, text="Welcome back, Admin 👋", font=("Segoe UI", 16, "bold"), bg=BG_COLOR, fg=TEXT_COLOR)
        lbl_welcome.pack(side="left")
        
        lbl_hint = tk.Label(welcome_frame, text="Select a module to get started", font=FONT_SMALL, bg=BG_COLOR, fg=TEXT_SECONDARY)
        lbl_hint.pack(side="right")
        
        # ── Cards Grid ──
        content = tk.Frame(self.root, bg=BG_COLOR)
        content.pack(expand=True, fill="both", padx=25, pady=(10, 25))
        
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_columnconfigure(2, weight=1)
        
        # Card data: (icon, title, subtitle, command, color)
        cards = [
            ("👤", "Register", "Add new person", self.open_register, PRIMARY_COLOR),
            ("📸", "Capture", "Take face photos", self.open_capture, SECONDARY_COLOR),
            ("🧠", "Train", "Train AI model", self.open_train, WARNING_COLOR),
            ("🔍", "Recognize", "Start detection", self.open_recognize, "#9b59b6"),
            ("📋", "Attendance", "View history", self.open_attendance, SECONDARY_COLOR),
            ("⚙", "Manage Users", "Edit & delete", self.open_manage_users, DANGER_COLOR),
            ("📊", "Metrics", "Model evaluation", self.open_metrics, "#e17055"),
        ]
        
        for i, (icon, title, subtitle, command, color) in enumerate(cards):
            row, col = divmod(i, 3)
            card = self._create_dashboard_card(content, icon, title, subtitle, command, color)
            card.grid(row=row, column=col, padx=12, pady=12, sticky="nsew")
        
        content.grid_rowconfigure(0, weight=1)
        content.grid_rowconfigure(1, weight=1)
        content.grid_rowconfigure(2, weight=1)
        
        # ── Status Bar ──
        status_bar = tk.Frame(self.root, bg=BG_SECONDARY, height=30)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        
        lbl_status = tk.Label(status_bar, text="●  System Online", font=FONT_SMALL, bg=BG_SECONDARY, fg=PRIMARY_COLOR)
        lbl_status.pack(side="left", padx=15)
        
        lbl_version = tk.Label(status_bar, text="v2.0  |  OpenCV + face_recognition", font=FONT_SMALL, bg=BG_SECONDARY, fg=TEXT_SECONDARY)
        lbl_version.pack(side="right", padx=15)
    
    def _create_dashboard_card(self, parent, icon, title, subtitle, command, accent_color):
        """Creates a premium dashboard card with hover animation."""
        card_outer = tk.Frame(parent, bg=BORDER_COLOR)
        card = tk.Frame(card_outer, bg=CARD_COLOR, cursor="hand2")
        card.pack(padx=1, pady=1, fill="both", expand=True)
        
        # Accent strip at top
        accent = tk.Frame(card, bg=accent_color, height=3)
        accent.pack(fill="x")
        
        # Content
        inner = tk.Frame(card, bg=CARD_COLOR, padx=20, pady=20)
        inner.pack(fill="both", expand=True)
        
        # Icon
        lbl_icon = tk.Label(inner, text=icon, font=("Segoe UI", 32), bg=CARD_COLOR)
        lbl_icon.pack(pady=(5, 10))
        
        # Title
        lbl_title = tk.Label(inner, text=title, font=FONT_BODY_BOLD, bg=CARD_COLOR, fg=TEXT_COLOR)
        lbl_title.pack()
        
        # Subtitle
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
        
    def update_clock(self):
        current_time = time.strftime("%H:%M:%S")
        current_date = time.strftime("%d %b %Y")
        self.lbl_clock.config(text=f"📅 {current_date}   🕐 {current_time}")
        self.root.after(1000, self.update_clock)
        
    def open_register(self):
        top = tk.Toplevel(self.root)
        RegisterApp(top)
        
    def open_capture(self):
        top = tk.Toplevel(self.root)
        CaptureApp(top)
        
    def open_train(self):
        top = tk.Toplevel(self.root)
        TrainApp(top)
        
    def open_recognize(self):
        top = tk.Toplevel(self.root)
        RecognizeApp(top)
        
    def open_attendance(self):
        top = tk.Toplevel(self.root)
        AttendanceApp(top)
        
    def open_manage_users(self):
        top = tk.Toplevel(self.root)
        ManageUsersApp(top)

    def open_metrics(self):
        top = tk.Toplevel(self.root)
        EvaluateModelApp(top)
