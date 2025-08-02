import cv2
import time
import face_recognition
import numpy as np
import threading
import os
import tkinter as tk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk
from utils import load_known_faces, recognize_face, save_intruder_image, send_telegram_alert,detect_mask

# Globals
unknown_face_detected = False
frame_global = None
is_capturing = False
capture_cancelled = False
current_capture_name = ""
last_unknown_save_time=0

cooldown = 60


# Load known faces initially
known_encodings, known_names = load_known_faces()

# Tkinter GUI setup
window = tk.Tk()
window.title("Smart Intruder Alert System")

# Video frame label
video_label = tk.Label(window)
video_label.pack()

# Button frame (to keep buttons fixed below video)
button_frame = tk.Frame(window)
button_frame.pack(pady=10)

# Add to Known Button
add_button = tk.Button(button_frame, text="Add to Known", font=("Arial", 14), bg="green", fg="white")
add_button.pack(side=tk.LEFT, padx=10)
add_button.pack_forget()  # hidden initially

# Cancel Capture Button

#cancel_button.config(state="disabled")  # disabled initially

video_capture = cv2.VideoCapture(0,cv2.CAP_DSHOW)
for _ in range(5):
    ret,_=video_capture.read()
    if not ret:
        time.sleep(0.1)

def cancel_capture():
    global is_capturing,capture_cancelled
    cancel_button.config(bg="darkred",text="cancelling....")
    window.update_idletasks()
    time.sleep(0.2)
    capture_cancelled = True
    video_capture.release()
    window.destroy()
cancel_button = tk.Button(button_frame, text="Cancel Capture", font=("Arial", 14), bg="red", fg="white",command=cancel_capture)
cancel_button.pack(side=tk.LEFT, padx=10)
cancel_button.config(command=cancel_capture)

def update_video_frame(img):
    imgtk = ImageTk.PhotoImage(image=img)
    video_label.imgtk = imgtk
    video_label.configure(image=imgtk)

def capture_known_images(name):
    global capture_cancelled
    video_capture = cv2.VideoCapture(0)
    count = 0
    last_face_location = None

    while count < 10 and not capture_cancelled:
        ret, frame = video_capture.read()
        if not ret:
            continue

        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small_frame)

        if face_locations:
            face_location = face_locations[0]

            # Smoothing: Update only if big movement
            if last_face_location is None:
                last_face_location = face_location
            else:
                diff = sum(abs(a - b) for a, b in zip(face_location, last_face_location))
                if diff > 20:
                    last_face_location = face_location
        else:
            last_face_location = None

        # Draw rectangle only if face is detected
        if last_face_location:
            top, right, bottom, left = [v * 4 for v in last_face_location]
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

            face_img = frame[top:bottom, left:right]
            if face_img.size != 0:
                count += 1
                save_path = os.path.join('known_faces', name)
                os.makedirs(save_path, exist_ok=True)
                cv2.imwrite(f"{save_path}/{name}_{count}.jpg", face_img)
                time.sleep(1)

        # Display prompt and counter
        cv2.putText(frame, f"Look straight - Capturing image {count}/40", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        cv2.imshow("Capturing Known Faces", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            capture_cancelled = True
            break

    video_capture.release()
    cv2.destroyAllWindows()
    os._exit(0)

    # Post-capture logic
    if not capture_cancelled:
        known_encodings, known_names = load_known_faces()
        window.after(0, lambda: messagebox.showinfo("Success", f"{name} has been successfully added!"))
        window.after(2000,lambda:window.destroy())
    else:
        capture_cancelled = False
        window.after(0, lambda: messagebox.showinfo("Cancelled", f"Capture for {name} cancelled!"))
def add_to_known():
    global is_capturing, current_capture_name

    if is_capturing:
        return

    name = simpledialog.askstring("Enter Name", "Enter the name of the person:")
    if name:
        is_capturing = True
        current_capture_name = name
        threading.Thread(target=capture_known_images, args=(name,), daemon=True).start()

add_button.config(command=add_to_known)
frame_count = 0  # Global frame counter for skipping frames
last_face_locations = []
last_face_names = []
last_mask_statuses = []
def process_frame():
    global frame_global, unknown_face_detected, last_unknown_save_time
    global frame_count, last_face_locations, last_face_names, last_mask_statuses

    ret, frame = video_capture.read()
    if not ret:
        window.after(10, process_frame)
        return

    frame_global = frame.copy()
    unknown_face_detected = False

    # Resize frame smaller for faster face detection
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
    # Convert to grayscale to apply contrast enhancement
    gray_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)

# Apply CLAHE to improve contrast in low light
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray_small)

# Convert back to 3 channels so it matches original format
    enhanced_rgb = cv2.merge([enhanced_gray]*3)

# Now use this for face detection
    rgb_small_frame = enhanced_rgb

    frame_count += 1

    if not is_capturing:

        if frame_count % 6 == 0:  # Detect every 6th frame to reduce CPU load

            # Detect face locations and encodings in small frame
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            face_names = []
            mask_statuses = []

            for face_encoding, face_location in zip(face_encodings, face_locations):
                name = recognize_face(face_encoding, known_encodings, known_names)

                # Scale face location back to full frame size
                top, right, bottom, left = [v * 4 for v in face_location]

                # Safely crop face image (check boundaries)
                h, w = frame.shape[:2]
                top = max(0, top)
                left = max(0, left)
                bottom = min(h, bottom)
                right = min(w, right)
                face_image = frame[top:bottom, left:right]

                # Detect mask only if face_image is valid
                if face_image.size > 0:
                    mask_status = detect_mask(face_image)
                else:
                    mask_status = "Unknown"

                face_names.append(name)
                mask_statuses.append(mask_status)

                if name == "Unknown":
                    unknown_face_detected = True
                    current_time = time.time()
                    if current_time - last_unknown_save_time > cooldown:
                        path = save_intruder_image(face_image)
                        threading.Thread(target=send_telegram_alert, args=(path, name), daemon=True).start()
                        last_unknown_save_time = current_time

            # Cache results for in-between frames
            last_face_locations = face_locations
            last_face_names = face_names
            last_mask_statuses = mask_statuses

        else:
            # Use cached face data for intermediate frames
            face_locations = last_face_locations
            face_names = last_face_names
            mask_statuses = last_mask_statuses

            if face_locations:
                unknown_face_detected = any(name == "Unknown" for name in face_names)

        # Draw rectangles and labels on full frame
        for (top, right, bottom, left), name, mask_status in zip(face_locations, face_names, mask_statuses):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            label = name
            if mask_status == "Mask":
                label += ""
            elif mask_status == "No Mask":
                label += ""

            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.putText(frame, label, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        # Show or hide Add button based on detection
        if unknown_face_detected and not is_capturing:
            add_button.pack(side=tk.LEFT, padx=10)
        else:
            add_button.pack_forget()

    # Display the updated frame on GUI
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(rgb_frame)
    update_video_frame(img)

    # Schedule next frame processing
    window.after(10, process_frame)

if __name__ == "__main__":
    window.after(200,process_frame)
    window.mainloop()
    video_capture.release()
    cv2.destroyAllWindows()