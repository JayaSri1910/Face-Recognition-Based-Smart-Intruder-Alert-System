import os
import cv2
import face_recognition
import time  # Added for sleep

def capture_faces(person_name, num_images=10):
    save_dir = os.path.join('known_faces', person_name)
    os.makedirs(save_dir, exist_ok=True)

    video_capture = cv2.VideoCapture(0)

    if not video_capture.isOpened():
        print("[ERROR] Cannot open camera.")
        return

    count = 0
    print(f"[INFO] Please show your face. Capturing {num_images} images...")

    while count < num_images:
        ret, frame = video_capture.read()
        if not ret:
            print("[ERROR] Failed to read frame.")
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)

        if len(face_locations) > 0:
            top, right, bottom, left = face_locations[0]

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, f"Count: {count + 1}", (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            face_image = frame[top:bottom, left:right]
            img_path = os.path.join(save_dir, f"{person_name}_{count + 1}.jpg")
            cv2.imwrite(img_path, face_image)

            count += 1
            time.sleep(0.5)  # Small delay instead of cv2.waitKey(500)

        cv2.imshow("Smart Intruder Alert System", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    print(f"[INFO] Captured {count} images for {person_name}")
if __name__ == "__main__":
    name = input("Enter person's name: ").strip()
    capture_faces(name)

