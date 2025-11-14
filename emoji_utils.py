import cv2
import os

def overlay_emoji(frame, path, x, y, scale=0.3):
    if not os.path.exists(path):
        return frame
        
    emoji = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if emoji is None:
        return frame

    h, w = emoji.shape[:2]
    emoji = cv2.resize(emoji, (int(w * scale), int(h * scale)))

    if emoji.shape[2] == 4:  # RGBA
        alpha = emoji[:, :, 3] / 255.0
        for c in range(3):
            y1, y2 = max(0, y), min(frame.shape[0], y + emoji.shape[0])
            x1, x2 = max(0, x), min(frame.shape[1], x + emoji.shape[1])

            if y1 < y2 and x1 < x2:
                emoji_h, emoji_w = y2 - y1, x2 - x1
                frame[y1:y2, x1:x2, c] = (
                    alpha[:emoji_h, :emoji_w] * emoji[:emoji_h, :emoji_w, c]
                    + (1 - alpha[:emoji_h, :emoji_w]) * frame[y1:y2, x1:x2, c]
                )
    else:
        y1, y2 = max(0, y), min(frame.shape[0], y + emoji.shape[0])
        x1, x2 = max(0, x), min(frame.shape[1], x + emoji.shape[1])
        if y1 < y2 and x1 < x2:
            frame[y1:y2, x1:x2] = emoji[:y2-y1, :x2-x1]

    return frame