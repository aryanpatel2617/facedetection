import tkinter as tk
from login import LoginApp
from dashboard import DashboardApp
from utils import init_csv_files

class MainApplication:
    def __init__(self):
        self.root = tk.Tk()
        init_csv_files()
        self.show_login()
        
    def show_login(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        LoginApp(self.root, self.show_dashboard)
        
    def show_dashboard(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        DashboardApp(self.root, self.show_login)
        
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MainApplication()
    app.run()


