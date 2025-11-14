import boto3
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime
import tempfile
import os

S3_BUCKET = "ec-user-logs"

def list_s3_files(bucket_name):
    s3 = boto3.client('s3')
    paginator = s3.get_paginator("list_objects_v2")
    files = []
    try:
        for page in paginator.paginate(Bucket=bucket_name):
            for obj in page.get("Contents", []):
                if obj["Key"].endswith(".csv"):
                    files.append(obj["Key"])
        return files
    except Exception as e:
        print(f"Error listing files: {e}")
        return []

def download_s3_file(key, local_path):
    s3 = boto3.client('s3')
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    s3.download_file(S3_BUCKET, key, local_path)
    print(f"Downloaded {key} -> {local_path}")

def filter_files_by_date(files, start_date, end_date):
    filtered = []
    for key in files:
        parts = key.split("/")
        if len(parts) < 2:
            continue
        timestamp_str = parts[1]
        try:
            ts = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")
            ts_date = ts.date()
            if start_date <= ts_date <= end_date:
                filtered.append(key)
        except Exception as e:
            print(f"[WARN] Could not parse timestamp from {key}: {e}")
            continue
    return filtered

def process_emotion_csv(input_csv, window_size=25):
    df = pd.read_csv(input_csv)
    if df.empty or 'dominant_emotion' not in df.columns:
        print(f"Invalid CSV: {input_csv}")
        return

    emotions = df['dominant_emotion'].tolist()
    timestamps = df['timestamp'].tolist()
    smoothed = [(timestamps[i], Counter(emotions[max(0, i-window_size+1):i+1]).most_common(1)[0][0])
                for i in range(len(emotions))]

    out_df = pd.DataFrame(smoothed, columns=['timestamp', 'smoothed_emotion'])

    plot_bar_chart(out_df)
    plot_time_series(out_df)

def plot_bar_chart(df):
    counts = df['smoothed_emotion'].value_counts().sort_values(ascending=True)
    plt.figure(figsize=(8,5))
    counts.plot(kind='barh', color='skyblue')
    plt.title("Overall Smoothed Emotion Distribution")
    plt.xlabel("Count")
    plt.ylabel("Emotion")
    plt.grid(axis='x', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.show()
    plt.close()

def plot_time_series(df):
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    levels = {e:i for i,e in enumerate(df['smoothed_emotion'].unique())}
    reverse_levels = {v:k for k,v in levels.items()}
    df['emotion_id'] = df['smoothed_emotion'].map(levels)

    plt.figure(figsize=(12,5))
    plt.scatter(df['timestamp'], df['emotion_id'], color='purple', s=30)
    plt.yticks(list(reverse_levels.keys()), list(reverse_levels.values()))
    plt.xticks(rotation=45)
    plt.title("Smoothed Emotion Over Time")
    plt.xlabel("Timestamp")
    plt.ylabel("Emotion")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()
    plt.show()
    plt.close()


def visualize_logs():
    def run_visualization():
        start_date = start_cal.get_date()
        end_date = end_cal.get_date()

        files = list_s3_files(S3_BUCKET)
        files = filter_files_by_date(files, start_date, end_date)

        if not files:
            messagebox.showinfo("Info", "No logs found for selected date range")
            return

        for key in files:
            local_csv = os.path.join(tempfile.gettempdir(), os.path.basename(key))
            download_s3_file(key, local_csv)
            process_emotion_csv(local_csv)

    root = tk.Tk()
    root.title("Visualize Emotion Logs")
    root.geometry("200x180")
    root.configure(bg="white")
    style = ttk.Style(root)
    style.theme_use('clam')

    tk.Label(root, 
             text="Start Date:",
             background='white', 
             ).pack(pady=(10, 0))
    start_cal = DateEntry(root, width=12, 
                          background='darkblue',
                          foreground='white', 
                          borderwidth=2, 
                          year=datetime.now().year)
    start_cal.pack(pady=(0, 10))

    tk.Label(root, 
             text="End Date:",
             background='white'
             ).pack(pady=(5, 0))
    end_cal = DateEntry(root, width=12, 
                        background='darkblue',
                        foreground='white', 
                        borderwidth=2, 
                        year=datetime.now().year)
    end_cal.pack(pady=(0, 15))

    tk.Button(root, text="Visualize Logs", 
              command=run_visualization,
              bg="DeepSkyBlue", 
              fg="white",
              width=15, 
              relief="flat"
              ).pack(pady=10)

    root.mainloop()