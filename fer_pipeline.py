import cv2
from fer.fer import FER
import time
import os
import json
from camera_utils import get_webcam
from visual_utils import draw_emotion_data, draw_status_text
from csv_logger import EmotionCSVLogger
import pyvirtualcam

def run_fer_loop(stop_event):
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
    else:
        config = {}

    print("Loading FER emotion detector...")
    try:
        detector = FER(mtcnn=True)
        print("FER detector loaded with MTCNN.")
    except Exception as e:
        print(f"Error with MTCNN: {e}")
        try:
            detector = FER(mtcnn=False)
            print("FER loaded with OpenCV cascade.")
        except Exception as e2:
            print(f"FER loading failed: {e2}")
            return

    emoji_paths = {
        "angry": "emojis/angry.png",
        "disgust": "emojis/disgust.png",
        "fear": "emojis/fear.png",
        "happy": "emojis/happy.png",
        "sad": "emojis/sad.png",
        "surprise": "emojis/surprised.png",
        "neutral": "emojis/neutral.png",
    }

    width = 1920
    height = 1080
    fps = 30

    try:
        cap = get_webcam(
            fps=config.get("capture_fps", 30),
            width=config.get("frame_width", 1920),
            height=config.get("frame_height", 1080)
        )
    except IOError as e:
        print(e)
        return

    prev_time = time.time()
    last_emotion_time = 0
    emotion_interval = config.get("emotion_polling_rate", 0.2)
    emotion_history = {}
    frame_count = 0
    emotions_data = []
    logging_active = False
    username = os.getenv("EC_USERNAME")
    csv_logger = EmotionCSVLogger(username)

    with pyvirtualcam.Camera(width=width, height=height, fps=fps, fmt=pyvirtualcam.PixelFormat.BGR) as cam:
        print(f"✅ Virtual camera started: {cam.device}")
        while not stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                print("Frame read error.")
                break

            frame_count += 1
            curr_time = time.time()

            frame_copy = cv2.resize(frame, (640, 480))
            lab = cv2.cvtColor(frame_copy, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_clahe = clahe.apply(l)
            lab_clahe = cv2.merge((l_clahe, a, b))
            frame_copy = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
            frame_copy = cv2.GaussianBlur(frame_copy, (5, 5), sigmaX=0.8)

            if config.get("mirror_toggle", False):
                frame = cv2.flip(frame, 1)

            if curr_time - last_emotion_time >= emotion_interval:
                rgb_input = cv2.cvtColor(frame_copy, cv2.COLOR_BGR2RGB)
                raw_emotions = detector.detect_emotions(rgb_input)
                last_emotion_time = curr_time
                emotions_data = []
                enabled_emotions = config.get("enabled_emotions", ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"])

                for face_data in raw_emotions:
                    filtered = {k: v for k, v in face_data["emotions"].items() if k in enabled_emotions}
                    if filtered:
                        face_data["emotions"] = filtered
                        emotions_data.append(face_data)

                        top_emotion = max(filtered, key=filtered.get)
                        if logging_active:
                            csv_logger.log("user", top_emotion)

            frame = draw_emotion_data(frame, emotions_data, emotion_history, emoji_paths)

            if config.get("fps_toggle", False):
                fps = 1 / (curr_time - prev_time) if curr_time != prev_time else 0
                prev_time = curr_time
                draw_status_text(frame, fps, frame_count)

            if config.get("logging_toggle", True) and not logging_active:
                csv_logger.start_new_log()
                logging_active = True

            cam.send(frame)
            cam.sleep_until_next_frame()


    cap.release()
    cv2.destroyAllWindows()

    if logging_active:
        print("[LOGGING] Stopping CSV logger and processing data...")
        csv_logger.stop()

    print("FER session ended.")