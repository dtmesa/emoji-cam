import json
import os
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox as messagebox
import boto3
from botocore.exceptions import ClientError


CONFIG_FILE = "config.json"
S3_BUCKET = "ec-user-logs" # HARDCODED BUCKET NAME

default_config = {
    "emotion_polling_rate": 0.2,
    "frame_width": 1920,
    "frame_height": 1080,
    "fps": 30,
    "emoji_toggle": True,
    "emotion_label_toggle": True,
    "mirror_toggle": False,
    "fps_toggle": False,
    "logging_toggle": True,
    "overlay_location": 1,
    "emotion_levels_over_time": True,
    "enabled_emotions": ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
}

display_names = {
    "emotion_polling_rate": "Polling Rate (s)",
    "frame_width": "Frame Width (px)",
    "frame_height": "Frame Height (px)",
    "fps": "FPS",
    "emoji_toggle": "Emoji Display",
    "emotion_label_toggle": "Current Emotion Display",
    "mirror_toggle": "Mirror Video",
    "fps_toggle": "FPS Display",
    "logging_toggle": "Session Logging",
    "overlay_location": "Overlay Location",
    "emotion_levels_over_time": "Emotion Time Plots",
    "enabled_emotions": "Emotions to Detect"
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return default_config.copy()
    
    with open(CONFIG_FILE, 'r') as f:
        user_config = json.load(f)
    
    merged = default_config.copy()
    merged.update(user_config)
    return merged
    
def save_config(data):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def edit_settings(parent):
    config = load_config()

    window = tk.Toplevel(parent)
    window.title("Edit FER Settings")
    window.configure(bg="white")

    location_options = {
    "Top Right": 0,
    "Top Left": 1,
    "Bottom Left": 2,
    "Bottom Right": 3
    }
    fields = {}
    toggles = {}
    rev_location_options = {v: k for k, v in location_options.items()}

    for idx, key in enumerate(["emotion_polling_rate", "frame_width", "frame_height", "fps"]):
        tk.Label(window, text=display_names[key] + ":", 
                 bg="white", 
                 fg="black"
                 ).grid(row=idx, 
                        column=0, 
                        sticky="e")
        entry = tk.Entry(window, bg="white", fg="black")
        entry.insert(0, str(config.get(key, default_config[key])))
        entry.grid(row=idx, column=1)
        fields[key] = entry

    toggle_keys = [
        "emotion_levels_over_time", 
        "emoji_toggle", 
        "mirror_toggle", 
        "fps_toggle", 
        "logging_toggle", 
    ]
    for i, key in enumerate(toggle_keys):
        var = tk.BooleanVar(value=config.get(key, default_config[key]))
        chk = tk.Checkbutton(window, 
                             text=display_names.get(key, key), 
                             variable=var, 
                             bg="white", 
                             fg="black", 
                             selectcolor="white"
                             )
        chk.grid(row=i//2 + 5, column=i % 2, sticky="w", padx=10)
        toggles[key] = var

    tk.Label(window, 
             text=display_names["overlay_location"] + ":",
             bg="white", 
             fg="black"
             ).grid(row=10, column=0, sticky="e")

    style = ttk.Style()
    style.theme_use('clam')
    style.configure("TCombobox",
                    fieldbackground="white",
                    background="white",
                    foreground="black")

    overlay_var = tk.StringVar(value=rev_location_options.get(config.get("overlay_location", 0)))

    location_menu = ttk.Combobox(
        window,
        textvariable=overlay_var,
        values=list(location_options.keys()),
        state="readonly",
        style="TCombobox"
        )
    
    location_menu.grid(row=10, column=1)

    tk.Label(window, text="Enabled Emotions:", bg="white", fg="black")\
        .grid(row=11, column=0, sticky="w", padx=10, pady=(10, 0), columnspan=2)

    emotion_options = ["angry", "disgust", "fear", "happy", "sad", "surprise", "neutral"]
    emotion_vars = {}

    emotion_frame = tk.Frame(window, bg="white")
    emotion_frame.grid(row=12, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 10))

    for i, emotion in enumerate(emotion_options):
        var = tk.BooleanVar(value=emotion in config.get("enabled_emotions", emotion_options))
        chk = tk.Checkbutton(emotion_frame, text=emotion.capitalize(), variable=var, bg="white", fg="black", selectcolor="white")
        chk.grid(row=i // 3, column=i % 3, sticky="w", padx=5, pady=2)
        emotion_vars[emotion] = var

    def save():
        for key, entry in fields.items():
            val = entry.get()
            try:
                _ = float(val) if '.' in val else int(val)
            except ValueError:
                messagebox.showerror("Invalid input", f"Please enter a valid number for {display_names[key]}.")
                entry.focus_set()
                return

        for key, entry in fields.items():
            val = entry.get()
            config[key] = float(val) if '.' in val else int(val)

        for key, var in toggles.items():
            config[key] = var.get()

        config["overlay_location"] = location_options[overlay_var.get()]
        config["enabled_emotions"] = [emotion for emotion, var in emotion_vars.items() if var.get()]
        save_config(config)
        print("Config updated.")
        window.destroy()

    tk.Button(window, 
              text="Save & Close", 
              command=save, 
              bg="Salmon", 
              fg="white",
              relief="flat"
              ).grid(row=13, columnspan=2, pady=10)

    window.mainloop()

def clear_logs():
    s3 = boto3.client('s3')
    username = os.getenv("EC_USERNAME")
    
    if not messagebox.askyesno("Confirm Clear Logs", f"Are you sure you want to delete all logs for {username}?"):
        return

    try:
        paginator = s3.get_paginator("list_objects_v2")
        to_delete = []
        for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=f"{username}/"):
            for obj in page.get("Contents", []):
                to_delete.append({'Key': obj['Key']})

        if not to_delete:
            messagebox.showinfo("Clear Logs", "No logs found for this user.")
            return

        for i in range(0, len(to_delete), 1000):
            batch = to_delete[i:i+1000]
            s3.delete_objects(Bucket=S3_BUCKET, Delete={'Objects': batch})

        messagebox.showinfo("Clear Logs", f"All logs for {username} cleared successfully.")

    except ClientError as e:
        messagebox.showerror(f"Failed to clear logs:\n{e}")