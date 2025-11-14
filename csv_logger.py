import io
from datetime import datetime
import boto3
from botocore.exceptions import ClientError
import pandas as pd
from collections import Counter

class EmotionCSVLogger:
    S3_BUCKET = "ec-user-logs"

    def __init__(self, username, region_name="us-west-1"):
        self.username = username
        self.timestamp = None
        self.active = False
        self.entries = []
        self.s3_client = boto3.client('s3', region_name=region_name)

    def start_new_log(self):
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.entries = [["timestamp", "person_id", "dominant_emotion"]]
        self.active = True
        print(f"[LOG] Started new session for {self.username} at {self.timestamp}")

    def log(self, person_id: str, emotion: str):
        if not self.active:
            return
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.entries.append([timestamp, person_id, emotion])

    def stop(self):
        if not self.active:
            return
        self.active = False

        df_raw = pd.DataFrame(self.entries[1:], columns=self.entries[0])

        raw_csv_io = io.StringIO()
        df_raw.to_csv(raw_csv_io, index=False)
        raw_csv_io.seek(0)
        raw_key = f"{self.username}/{self.timestamp}/emotion_log_{self.username}_{self.timestamp}.csv"
        self.upload_to_s3_fileobj(raw_csv_io, raw_key)
        self.process_emotion_df(df_raw)
        raw_csv_io = io.StringIO()
        df_raw.to_csv(raw_csv_io, index=False)
        raw_csv_io.seek(0)
        raw_key = f"{self.username}/{self.timestamp}/emotion_log_{self.username}_{self.timestamp}.csv"
        self.upload_to_s3_fileobj(raw_csv_io, raw_key)

    def process_emotion_df(self, df, window_size=25):
        window_size = int(window_size)
        emotions = df['dominant_emotion'].tolist()
        timestamps = df['timestamp'].tolist()

        smoothed = [
            (timestamps[i], Counter(emotions[max(0, i-window_size+1): i+1]).most_common(1)[0][0])
            for i in range(len(emotions))
        ]
        df_smoothed = pd.DataFrame(smoothed, columns=['timestamp', 'smoothed_emotion'])
        return df_smoothed

    def upload_to_s3_fileobj(self, fileobj, s3_key):
        try:
            if isinstance(fileobj, io.StringIO):
                fileobj = io.BytesIO(fileobj.getvalue().encode('utf-8'))
            fileobj.seek(0)
            self.s3_client.upload_fileobj(fileobj, self.S3_BUCKET, s3_key)
            print(f"Uploaded to s3://{self.S3_BUCKET}/{s3_key}")
        except ClientError as e:
            print(f"Upload failed for {s3_key}: {e}")