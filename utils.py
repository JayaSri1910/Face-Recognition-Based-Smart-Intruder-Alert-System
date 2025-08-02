import os
import face_recognition
import numpy as np
from datetime import datetime
from PIL import Image
import uuid
import requests
from tensorflow.keras.models import load_model
import cv2

# Load mask detection model globally once
_mask_model = None

# Load all known face encodings and names
def load_known_faces(known_faces_dir='known_faces'):
    known_encodings = []
    known_names = []

    print("[INFO] Loading known faces...")

    for root, dirs, files in os.walk(known_faces_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                path = os.path.join(root, file)

                try:
                    # Open with PIL and resize to speed up
                    image = Image.open(path)
                    image = image.convert("RGB")
                    image.thumbnail((500, 500))  # Resize for faster processing
                    image_np = np.array(image)

                    encodings = face_recognition.face_encodings(image_np)
                    if encodings:
                        known_encodings.append(encodings[0])
                        person_name = os.path.basename(root)
                        known_names.append(person_name)
                        print(f"[LOADED] {person_name} from {file}")
                    else:
                        print(f"[WARNING] No face found in: {path}")

                except Exception as e:
                    print(f"[ERROR] Failed to load {path}: {e}")

    print(f"[INFO] Loaded {len(known_encodings)} known faces.")
    return known_encodings, known_names

# Compare a given encoding to known encodings
def recognize_face(encoding, known_encodings, known_names, tolerance=0.65):
    matches = face_recognition.compare_faces(known_encodings, encoding, tolerance)
    face_distances = face_recognition.face_distance(known_encodings, encoding)
    if True in matches:
        best_match_index = np.argmin(face_distances)
        return known_names[best_match_index]
    return "Unknown"

# Save intruder face image locally with timestamp
def save_intruder_image(face_image, folder="intruder_logs"):
    os.makedirs(folder, exist_ok=True)
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.jpg"
    path = os.path.join(folder, filename)
    Image.fromarray(face_image).save(path)
    return path

# Send intruder image alert via Telegram
def send_telegram_alert(image_path, name="Unknown"):
    bot_token = "7573996184:AAGM4SrMkj_OUjA4JMx5VzVRtRAHLODspdU"
    chat_id = "7369298145"
    
    caption = f"🚨 INTRUDER ALERT! 🚨\n\n*Name*: {name}\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"

    try:
        with open(image_path, 'rb') as photo:
            response = requests.post(url, data={
                'chat_id': chat_id,
                'caption': caption,
                'parse_mode': 'Markdown'
            }, files={'photo': photo})

        if response.status_code == 200:
            print("[INFO] Telegram alert sent.")
        else:
            print(f"[ERROR] Telegram error: {response.text}")

    except Exception as e:
        print(f"[ERROR] Failed to send Telegram alert: {e}")
def add_new_face(name, face_image, known_faces_dir="known_faces"):
    person_dir = os.path.join(known_faces_dir, name)
    os.makedirs(person_dir, exist_ok=True)
    
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}.jpg"
    path = os.path.join(person_dir, filename)
    
    Image.fromarray(face_image).save(path)
    print(f"[INFO] New face image saved at: {path}")
    return path

def load_mask_model(model_path="models/mask_detector.model"):
    global _mask_model
    if _mask_model is None:
        _mask_model = load_model(model_path)
    return _mask_model

def detect_mask(face_image):
    """
    Input: face_image - cropped BGR image of face (numpy array)
    Output: 'Mask' or 'No Mask' or 'Unknown' if error
    """
    try:
        model = load_mask_model()

        # Preprocess image to 224x224 and normalize
        face = cv2.resize(face_image, (224, 224))
        face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
        face = face.astype("float32") / 255.0
        face = np.expand_dims(face, axis=0)  # shape (1,224,224,3)

        (mask, no_mask) = model.predict(face)[0]
        return "Mask" if mask > no_mask else "No Mask"
    except Exception as e:
        print(f"[ERROR] Mask detection failed: {e}")
        return "Unknown"