import cv2

def get_webcam(fps=30, width=1920, height=1080):
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        raise IOError("ERROR: Could not open webcam.")
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)
    
    return cap