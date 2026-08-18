import tkinter as tk
from utils import (BG_COLOR, BG_SECONDARY, CARD_COLOR, TEXT_COLOR, TEXT_SECONDARY, 
                   PRIMARY_COLOR, BORDER_COLOR, FONT_TITLE, FONT_BODY, FONT_SUBTITLE, FONT_SMALL,
                   create_button, create_styled_entry, create_card, create_separator,
                   create_label, show_error, center_window)

class LoginApp:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        
        self.root.title("Face Recognition System")
        self.root.configure(bg=BG_COLOR)
        center_window(self.root, 500, 650)
        self.root.resizable(False, False)
        
        self.create_widgets()
        
    def create_widgets(self):
        # Top accent bar
        accent_bar = tk.Frame(self.root, bg=PRIMARY_COLOR, height=4)
        accent_bar.pack(fill="x")
        
        # Spacer
        tk.Frame(self.root, bg=BG_COLOR, height=40).pack()
        
        # Logo / Icon area
        icon_frame = tk.Frame(self.root, bg=BG_COLOR)
        icon_frame.pack()
        
        # Circle icon
        icon_canvas = tk.Canvas(icon_frame, width=80, height=80, bg=BG_COLOR, highlightthickness=0)
        icon_canvas.pack()
        icon_canvas.create_oval(5, 5, 75, 75, fill=CARD_COLOR, outline=PRIMARY_COLOR, width=2)
        icon_canvas.create_text(40, 40, text="👤", font=("Segoe UI", 28))
        
        tk.Frame(self.root, bg=BG_COLOR, height=15).pack()
        
        # Title
        lbl_title = tk.Label(self.root, text="FACE RECOGNITION", font=FONT_TITLE, bg=BG_COLOR, fg=PRIMARY_COLOR)
        lbl_title.pack()
        
        lbl_subtitle = tk.Label(self.root, text="Attendance Management System", font=FONT_SUBTITLE, bg=BG_COLOR, fg=TEXT_SECONDARY)
        lbl_subtitle.pack(pady=(5, 0))
        
        tk.Frame(self.root, bg=BG_COLOR, height=30).pack()
        
        # Login Card
        card = create_card(self.root, pad_x=40, pad_y=30)
        card.outer.pack(fill="x", padx=50)
        
        # "Sign In" header
        lbl_signin = tk.Label(card, text="Sign In", font=("Segoe UI", 16, "bold"), bg=CARD_COLOR, fg=TEXT_COLOR)
        lbl_signin.pack(anchor="w", pady=(0, 5))
        
        lbl_signin_sub = tk.Label(card, text="Enter your credentials to continue", font=FONT_SMALL, bg=CARD_COLOR, fg=TEXT_SECONDARY)
        lbl_signin_sub.pack(anchor="w", pady=(0, 20))
        
        # Separator
        sep = create_separator(card, PRIMARY_COLOR)
        sep.pack(fill="x", pady=(0, 20))
        
        # Username
        lbl_user = tk.Label(card, text="USERNAME", font=("Segoe UI", 9, "bold"), bg=CARD_COLOR, fg=TEXT_SECONDARY)
        lbl_user.pack(anchor="w")
        
        self.entry_user_frame = create_styled_entry(card)
        self.entry_user_frame.pack(fill="x", pady=(5, 15))
        self.entry_user = self.entry_user_frame.entry
        
        # Password
        lbl_pass = tk.Label(card, text="PASSWORD", font=("Segoe UI", 9, "bold"), bg=CARD_COLOR, fg=TEXT_SECONDARY)
        lbl_pass.pack(anchor="w")
        
        self.entry_pass_frame = create_styled_entry(card, show="●")
        self.entry_pass_frame.pack(fill="x", pady=(5, 25))
        self.entry_pass = self.entry_pass_frame.entry
        
        # Login Button
        btn_login = create_button(card, "→  SIGN IN", self.check_login, bg_color=PRIMARY_COLOR, width=35, height=2)
        btn_login.pack(pady=(0, 5))
        
        tk.Frame(self.root, bg=BG_COLOR, height=15).pack()
        
        # Footer
        lbl_footer = tk.Label(self.root, text="Powered by OpenCV & Face Recognition", font=FONT_SMALL, bg=BG_COLOR, fg=TEXT_SECONDARY)
        lbl_footer.pack(side="bottom", pady=15)
        
        # Bind Enter key
        self.root.bind('<Return>', lambda e: self.check_login())
        self.entry_user.focus_set()
        
    def check_login(self):
        username = self.entry_user.get()
        password = self.entry_pass.get()
        
        # Simple hardcoded authentication for the mini project
        if username == "admin" and password == "admin":
            self.root.unbind('<Return>')
            self.on_login_success()
        else:
            show_error("Login Failed", "Invalid Username or Password!")
