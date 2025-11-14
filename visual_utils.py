import cv2
import os
import json
from collections import deque
from emoji_utils import overlay_emoji

emotion_colors = {
    "angry": (0, 0, 255),
    "disgust": (0, 128, 128),
    "fear": (128, 0, 128),
    "happy": (0, 255, 0),
    "sad": (255, 0, 0),
    "surprise": (0, 255, 255),
    "neutral": (80, 80, 80)
}

EMOJI_RESOLUTION = 160

SCROLL_BUFFER_SIZE = 600
emotion_likelihood_history = {
    emotion: deque(maxlen=SCROLL_BUFFER_SIZE) for emotion in emotion_colors
}

def draw_emotion_data(frame, emotions_data, emotion_history, emoji_paths):
    config_path = "config.json"
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
    else:
        config = {}

    frame_height, frame_width = frame.shape[:2]

    left_x = int(frame_width * 1/20)
    right_x = int(frame_width * 7/8)
    top_y = int(frame_height * 1/20)
    bottom_y = int(frame_height * 7/8)

    emoji_scale = 0.4
    emoji_size = int(EMOJI_RESOLUTION * emoji_scale)

    if not emotions_data:
        return frame

    face_data = emotions_data[0]
    emotions = face_data["emotions"]
    top_emotion = max(emotions, key=emotions.get)

    for i, face_data in enumerate(emotions_data):
        emotions = face_data["emotions"]
        top_emotion = max(emotions, key=emotions.get)

        face_id = f"face_{i}"
        if face_id in emotion_history:
            alpha = 0.6
            for emotion in emotions:
                if emotion in emotion_history[face_id]:
                    emotions[emotion] = (alpha * emotions[emotion] +
                                         (1 - alpha) * emotion_history[face_id][emotion])
            top_emotion = max(emotions, key=emotions.get)
        emotion_history[face_id] = emotions.copy()

        emoji_path = emoji_paths.get(top_emotion.lower())
        if config.get("emoji_toggle", True) and emoji_path:
            location = config.get("overlay_location", 1)

            if location == 0:  # Top right
                emoji_x = right_x
                emoji_y = top_y
                bars_below = True
            elif location == 1:  # Top left
                emoji_x = left_x
                emoji_y = top_y
                bars_below = True
            elif location == 2:  # Bottom left
                emoji_x = left_x
                emoji_y = bottom_y
                bars_below = False
            elif location == 3:  # Bottom right
                emoji_x = right_x
                emoji_y = bottom_y
                bars_below = False
            else:
                emoji_x = right_x
                emoji_y = top_y
                bars_below = True

            frame = overlay_emoji(frame, emoji_path, emoji_x, emoji_y, scale=emoji_scale)

        if config.get("emotion_levels_over_time", True):
            for emotion in emotion_likelihood_history:
                emotion_likelihood_history[emotion].append(emotions.get(emotion, 0.0))

            graph_width = 300
            graph_height = 150

            graph_x = emoji_x - frame_width // 25

            if bars_below:
                graph_y = emoji_y + emoji_size + 20
            else:
                graph_y = emoji_y - graph_height - 20
            
            overlay = frame.copy()

            cv2.rectangle(overlay, (graph_x, graph_y),
              (graph_x + graph_width, graph_y + graph_height),
              (30, 30, 30), -1)
            
            alpha = 0.35
            cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

            enabled_emotions = config.get("enabled_emotions", ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"])
            for emotion in enabled_emotions:
                history = emotion_likelihood_history.get(emotion, [])
                color = emotion_colors.get(emotion, (255, 255, 255))

                for i in range(1, len(history)):
                    x1 = graph_x + int((i - 1) / SCROLL_BUFFER_SIZE * graph_width)
                    x2 = graph_x + int(i / SCROLL_BUFFER_SIZE * graph_width)
                    y1 = graph_y + graph_height - int(history[i - 1] * graph_height)
                    y2 = graph_y + graph_height - int(history[i] * graph_height)
                    cv2.line(frame, (x1, y1), (x2, y2), color, 1, cv2.LINE_AA)
                
            return frame

def draw_status_text(frame, fps, frame_count):
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)