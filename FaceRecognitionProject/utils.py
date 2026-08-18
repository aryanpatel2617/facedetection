import tkinter as tk
from tkinter import messagebox
import os

# ═══════════════════════════════════════════════════════════════
#                    PREMIUM DARK THEME PALETTE
# ═══════════════════════════════════════════════════════════════

# Background colors
BG_COLOR = "#0d1117"
BG_SECONDARY = "#161b22"
CARD_COLOR = "#1c2333"
CARD_HOVER = "#242d3d"

# Accent colors
PRIMARY_COLOR = "#00d4aa"
PRIMARY_HOVER = "#00b894"
SECONDARY_COLOR = "#4f8fff"
SECONDARY_HOVER = "#3a7be0"
DANGER_COLOR = "#ff4757"
DANGER_HOVER = "#e84050"
WARNING_COLOR = "#ffa502"
SUCCESS_COLOR = "#2ed573"

# Text colors
TEXT_COLOR = "#e6edf3"
TEXT_SECONDARY = "#8b949e"
TEXT_MUTED = "#484f58"

# Border colors
BORDER_COLOR = "#30363d"
BORDER_LIGHT = "#3d444d"
ACCENT_BORDER = "#1a7f5a"

# Hover color map
HOVER_COLOR_MAP = {
    PRIMARY_COLOR: PRIMARY_HOVER,
    SECONDARY_COLOR: SECONDARY_HOVER,
    DANGER_COLOR: DANGER_HOVER,
    "#666666": "#555555",
    "#2196F3": "#1e88e5",
}

# ═══════════════════════════════════════════════════════════════
#                         FONTS
# ═══════════════════════════════════════════════════════════════

FONT_TITLE = ("Segoe UI", 26, "bold")
FONT_SUBTITLE = ("Segoe UI", 14)
FONT_BODY = ("Segoe UI", 11)
FONT_BODY_BOLD = ("Segoe UI", 11, "bold")
FONT_BTN = ("Segoe UI", 11, "bold")
FONT_SMALL = ("Segoe UI", 9)
FONT_ICON = ("Segoe UI", 16)
FONT_HEADER = ("Segoe UI", 18, "bold")

# ═══════════════════════════════════════════════════════════════
#                     WIDGET HELPERS
# ═══════════════════════════════════════════════════════════════

def create_gradient_frame(parent, color1, color2, width, height):
    """Creates a canvas with a vertical gradient effect."""
    canvas = tk.Canvas(parent, width=width, height=height, highlightthickness=0, bd=0)
    
    r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
    r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
    
    steps = height
    for i in range(steps):
        ratio = i / steps
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)
        color = f"#{r:02x}{g:02x}{b:02x}"
        canvas.create_line(0, i, width, i, fill=color)
    
    return canvas


def create_button(parent, text, command, bg_color=PRIMARY_COLOR, fg_color=TEXT_COLOR, width=20, height=2):
    """Creates a premium styled button with smooth hover effects."""
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg_color,
        fg=fg_color,
        font=FONT_BTN,
        relief="flat",
        activebackground=HOVER_COLOR_MAP.get(bg_color, bg_color),
        activeforeground=TEXT_COLOR,
        width=width,
        height=height,
        cursor="hand2",
        bd=0,
        padx=12,
        pady=4,
    )
    
    def on_enter(e):
        btn['bg'] = HOVER_COLOR_MAP.get(bg_color, bg_color)
        
    def on_leave(e):
        btn['bg'] = bg_color

    btn.bind("<Enter>", on_enter)
    btn.bind("<Leave>", on_leave)
    
    return btn


def create_icon_button(parent, icon, text, command, bg_color=PRIMARY_COLOR, fg_color=TEXT_COLOR, width=22, height=2):
    """Creates a button with an icon prefix."""
    full_text = f"{icon}  {text}"
    return create_button(parent, full_text, command, bg_color=bg_color, fg_color=fg_color, width=width, height=height)


def create_styled_entry(parent, placeholder="", show=None, width=30):
    """Creates a modern styled entry with focus effects."""
    frame = tk.Frame(parent, bg=BORDER_COLOR, bd=0)
    
    entry = tk.Entry(
        frame,
        font=FONT_BODY,
        bg=BG_SECONDARY,
        fg=TEXT_COLOR,
        insertbackground=PRIMARY_COLOR,
        relief="flat",
        width=width,
        highlightthickness=0,
        bd=0,
    )
    if show:
        entry.config(show=show)
    
    entry.pack(padx=1, pady=1, ipady=8, fill="x")
    
    def on_focus_in(e):
        frame.config(bg=PRIMARY_COLOR)
        
    def on_focus_out(e):
        frame.config(bg=BORDER_COLOR)
    
    entry.bind("<FocusIn>", on_focus_in)
    entry.bind("<FocusOut>", on_focus_out)
    
    # Store entry reference on frame for access
    frame.entry = entry
    return frame


def create_card(parent, pad_x=30, pad_y=20):
    """Creates a card-style frame with border."""
    outer = tk.Frame(parent, bg=BORDER_COLOR)
    inner = tk.Frame(outer, bg=CARD_COLOR, padx=pad_x, pady=pad_y)
    inner.pack(padx=1, pady=1, fill="both", expand=True)
    inner.outer = outer
    return inner


def create_separator(parent, color=BORDER_COLOR):
    """Creates a thin horizontal separator line."""
    sep = tk.Frame(parent, bg=color, height=1)
    return sep


def create_label(parent, text, font=FONT_BODY, fg=TEXT_COLOR, bg=None):
    """Creates a styled label."""
    if bg is None:
        bg = parent.cget("bg")
    return tk.Label(parent, text=text, font=font, fg=fg, bg=bg)


# ═══════════════════════════════════════════════════════════════
#                    DIALOG HELPERS
# ═══════════════════════════════════════════════════════════════

def show_error(title, message):
    """Displays an error messagebox."""
    messagebox.showerror(title, message)

def show_info(title, message):
    """Displays an info messagebox."""
    messagebox.showinfo(title, message)
    
def show_warning(title, message):
    """Displays a warning messagebox."""
    messagebox.showwarning(title, message)

def center_window(window, width, height):
    """Centers a Tkinter window on the screen."""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = int((screen_width / 2) - (width / 2))
    y = int((screen_height / 2) - (height / 2))
    window.geometry(f'{width}x{height}+{x}+{y}')

def init_csv_files():
    """Initializes necessary CSV files if they don't exist."""
    users_path = os.path.join("users", "users.csv")
    attendance_path = os.path.join("attendance", "attendance.csv")
    
    if not os.path.exists(users_path):
        with open(users_path, 'w') as f:
            f.write("ID,Name,Department,Age\n")
            
    if not os.path.exists(attendance_path):
        with open(attendance_path, 'w') as f:
            f.write("Name,Date,Time\n")
