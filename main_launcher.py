import tkinter as tk
from tkinter import messagebox, simpledialog
from tkinter import ttk
import os
from PIL import Image, ImageTk
import threading
import subprocess
from capture_known_faces import capture_faces

VALID_USERNAME = "admin"
VALID_PASSWORD = "23"

class SmartIntruderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Intruder Alert System")
        self.geometry("700x500")
        self.resizable(False, False)
        self['bg'] = '#2C3E50'

        self.login_frame = None
        self.control_panel_frame = None
        self.create_login_frame()

    def create_login_frame(self):
        if self.control_panel_frame:
            self.control_panel_frame.destroy()

        self.login_frame = tk.Frame(self)
        self.login_frame.pack(fill='both', expand=True)

        bg_img = Image.open("login_bg.jpg").resize((800, 500), Image.Resampling.LANCZOS)
        self.bg_image = ImageTk.PhotoImage(bg_img)

        bg_label = tk.Label(self.login_frame, image=self.bg_image)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        form_frame = tk.Frame(self.login_frame, bg='#ffffff', bd=0)
        form_frame.place(x=50, y=100, width=300, height=340)

        tk.Label(form_frame, text="Login", font=("Arial", 22, "bold"), bg='#ffffff', fg='#2C3E50').pack(pady=10)
        tk.Label(form_frame, text="Username", font=("Arial", 12), bg='#ffffff', anchor='w').pack(fill='x', padx=20, pady=(10, 0))
        self.username_entry = ttk.Entry(form_frame, font=("Arial", 12))
        self.username_entry.pack(padx=20, pady=5, fill='x')

        tk.Label(form_frame, text="Password", font=("Arial", 12), bg='#ffffff', anchor='w').pack(fill='x', padx=20, pady=(10, 0))
        self.password_entry = ttk.Entry(form_frame, font=("Arial", 12), show="*")
        self.password_entry.pack(padx=20, pady=5, fill='x')
        self.show_password_var = tk.BooleanVar()
        show_password_cb = tk.Checkbutton(
        form_frame, 
        text="Show Password", 
        bg='#ffffff', 
        variable=self.show_password_var,
        command=self.toggle_password_visibility)  # <-- Variable to track checkbox state
        
    
        show_password_cb.pack(padx=20, pady=(5, 10), anchor='w')  # Checkbox for show password


        self.feedback_label = tk.Label(form_frame, text="", font=("Arial", 10), bg='#ffffff', fg='red',height=1)
        self.feedback_label.pack(pady=5)
        style=ttk.Style()
        style.configure("Login.TButton",font=("Arial",14))

        login_btn = ttk.Button(form_frame, text="Login", command=self.check_login,style="Login.TButton")
        login_btn.pack(pady=10,ipadx=10,ipady=5)
    def toggle_password_visibility(self):
       if self.show_password_var.get():
        self.password_entry.config(show='')
       else:
        self.password_entry.config(show='*')

    def check_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        if username == VALID_USERNAME and password == VALID_PASSWORD:
            self.login_frame.destroy()
            self.create_control_panel()
        else:
            self.feedback_label.config(text="Incorrect username or password!", fg='red')

    def create_control_panel(self):
        # Main frame (control panel)
        self.control_panel_frame = tk.Frame(self, width=700, height=500)
        self.control_panel_frame.pack(fill='both', expand=True)

        # Load and resize the main background image
        bg_img = Image.open("control.jpg").resize((700, 500), Image.Resampling.LANCZOS)
        self.control_bg_image = ImageTk.PhotoImage(bg_img)

        # Set main background image in label filling the frame
        bg_label = tk.Label(self.control_panel_frame, image=self.control_bg_image)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Title label on top, with transparent bg (just the main bg visible)
        title = tk.Label(self.control_panel_frame, text="Control Panel", font=("Arial", 24, "bold"), bg='#34495E', fg='white')
        title.place(x=240, y=20)

        # Button frame size and position — adjust these as you want
             # y coordinate in pixels
        btn_frame_width = 700 # width in pixels
        btn_frame_height = 230 # height in pixels
        btn_frame_x = (750-btn_frame_width)//2  # x coordinate in pixels
        btn_frame_y = (500-btn_frame_height)//2

        # Crop the exact area from main bg image for the button frame background
        cropped_img = bg_img.crop((btn_frame_x, btn_frame_y, btn_frame_x + btn_frame_width, btn_frame_y + btn_frame_height))
        cropped_img = cropped_img.resize((btn_frame_width, btn_frame_height), Image.Resampling.LANCZOS)
        self.btn_bg_image = ImageTk.PhotoImage(cropped_img)

        # Create button frame with fixed size and place it exactly
        btn_frame = tk.Frame(self.control_panel_frame, width=btn_frame_width, height=btn_frame_height)
        btn_frame.place(x=btn_frame_x, y=btn_frame_y)

        # Place cropped background image as a label inside the button frame
        btn_bg_label = tk.Label(btn_frame, image=self.btn_bg_image)
        btn_bg_label.place(x=0, y=0, width=btn_frame_width,height=btn_frame_height)

        # Configure button style
        style = ttk.Style()
        style.configure('TButton', font=('Arial', 14, 'bold'), padding=10)

        # Place buttons inside btn_frame using grid (no frame bg, transparent visually)
        ttk.Button(btn_frame, text="Show Intruder Logs", width=25,
                   command=lambda: self.show_image_viewer("intruder_logs")).grid(row=0, column=0, padx=10, pady=10)
        ttk.Button(btn_frame, text="Known Faces", width=25,
                   command=self.show_known_faces).grid(row=0, column=1, padx=10, pady=10)
        ttk.Button(btn_frame, text="Add To Known Images", width=25,
                   command=self.prompt_person_name).grid(row=1, column=0, padx=10, pady=10)
        ttk.Button(btn_frame, text="Start Capturing", width=25,
                   command=self.start_detection_thread).grid(row=1, column=1, padx=10, pady=10)
        ttk.Button(btn_frame, text="Exit", width=25,
                   command=self.exit_app).grid(row=2, column=0, columnspan=2, pady=10)

        # Status label below button frame, with main bg color
        self.status_label = tk.Label(self.control_panel_frame, text="", font=("Arial", 12), bg='#34495E', fg='white')
        self.status_label.pack(pady=20)

    def show_known_faces(self):
        known_folder = "known_faces"
        if not os.path.exists(known_folder):
            messagebox.showinfo("No Faces", "No known faces found.")
            return

        win = tk.Toplevel(self)
        win.title("Known Faces")
        win.geometry("800x600")
        win.configure(bg='#2C3E50')

        persons = [d for d in os.listdir(known_folder) if os.path.isdir(os.path.join(known_folder, d))]
        if not persons:
            messagebox.showinfo("Empty", "No known persons found.")
            return

        for person in persons:
            btn = ttk.Button(win, text=person, command=lambda p=person: self.show_image_viewer(os.path.join(known_folder, p)))
            btn.pack(pady=5)

    def show_image_viewer(self, folder):
        if not os.path.exists(folder):
            messagebox.showinfo("No Images", "Folder does not exist.")
            return

        files = [f for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        if not files:
            messagebox.showinfo("No Images", "No images found in the folder.")
            return

        viewer = tk.Toplevel(self)
        viewer.title(f"Viewing: {folder}")
        viewer.geometry("800x600")
        viewer.configure(bg='#2C3E50')

        canvas = tk.Canvas(viewer, bg='#2C3E50')
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(viewer, orient="vertical", command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        frame = tk.Frame(canvas, bg='#2C3E50')
        canvas.create_window((0, 0), window=frame, anchor='nw')

        self.images = []

        for idx, file in enumerate(files):
            path = os.path.join(folder, file)
            img = Image.open(path)
            img.thumbnail((150, 150))
            photo = ImageTk.PhotoImage(img)
            self.images.append(photo)

            sub_frame = tk.Frame(frame, bg='#2C3E50')
            sub_frame.grid(row=idx // 4, column=idx % 4, padx=10, pady=10)

            lbl = tk.Label(sub_frame, image=photo, bg='#2C3E50')
            lbl.pack()

            del_btn = ttk.Button(
                sub_frame, text="Delete",
                command=lambda p=path, w=sub_frame, v=viewer: self.delete_image(p, w, v)
            )
            del_btn.pack(pady=5)

    def delete_image(self, path, widget, viewer):
        # Make sure messagebox is on top of the viewer window
        viewer.lift()
        viewer.attributes('-topmost', True)

        # Show confirmation dialog with 'viewer' as parent to keep it on top
        response = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this image?", parent=viewer)
        if response:
            try:
                os.remove(path)
                widget.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete image:\n{e}", parent=viewer)
        # Remove topmost after dialog closes to allow normal behavior
        viewer.attributes('-topmost', False)

    def start_detection_thread(self):
        self.status_label.config(text="Starting detection...")
        thread = threading.Thread(target=self.run_main_py_detection, daemon=True)
        thread.start()

    def run_main_py_detection(self):
        try:
            self.status_label.config(text="Detection running...")
            subprocess.run([r'd:\smart_intruder_alert_system\venv310\Scripts\python.exe', r'd:\smart_intruder_alert_system\main.py'], check=True)
            self.status_label.config(text="Detection stopped.")
        except subprocess.CalledProcessError as e:
            self.status_label.config(text="Error running detection.")
            messagebox.showerror("Error", f"Detection failed: {e}")

    def prompt_person_name(self):
        person_name = simpledialog.askstring("Enter Name", "Enter the person's name:")
        if person_name:
            self.status_label.config(text=f"Capturing images for {person_name}...")
            thread = threading.Thread(target=self.run_capture_known, args=(person_name,), daemon=True)
            thread.start()

    def run_capture_known(self, name):
        try:
            capture_faces(name)
            self.status_label.config(text=f"Capture completed for {name}.")
        except Exception as e:
            self.status_label.config(text="Error during capture.")
            messagebox.showerror("Error", str(e))

    def exit_app(self):
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.destroy()

if __name__ == "__main__":
    app = SmartIntruderApp()
    app.mainloop()