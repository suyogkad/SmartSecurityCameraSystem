import firebase_admin
import requests
from firebase_admin import credentials, firestore, storage
import os
import sqlite3
import subprocess
import zlib
import time
from warnings import simplefilter
from dotenv import load_dotenv

load_dotenv()
simplefilter(action='ignore', category=UserWarning)

MAX_RETRIES = 5
RETRY_WAIT = 5  # seconds to wait for retries

# firebase settings (loaded from .env)
FIREBASE_CREDENTIALS = os.getenv('FIREBASE_CREDENTIALS', 'firebase-credentials.json')
FIREBASE_STORAGE_BUCKET = os.getenv('FIREBASE_STORAGE_BUCKET')

class FirebaseManager:

    def __init__(self):
        # declaring firebase credentials
        self.cred = credentials.Certificate(FIREBASE_CREDENTIALS)

        # to check if default app already exists, if not then initialize
        if not firebase_admin._apps.get('[DEFAULT]'):
            firebase_admin.initialize_app(self.cred, {'storageBucket': FIREBASE_STORAGE_BUCKET})

        self.db = firestore.client()

    def safe_upload(self, func, *args, **kwargs):
        retries = 0
        while retries < MAX_RETRIES:
            try:
                return func(*args, **kwargs)
            except requests.exceptions.ReadTimeout:
                print(f"Upload failed due to timeout. Retrying in {RETRY_WAIT} seconds...")
                time.sleep(RETRY_WAIT)
                retries += 1
        print("Max retries reached. Upload failed.")

    def reencode_video(self, input_path, output_path):
        """function to re-encode each video using FFmpeg."""
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-strict', 'experimental',
            '-movflags', '+faststart',
            '-loglevel', 'panic',  # this will suppress ffmpeg output
            output_path
        ]
        subprocess.run(cmd)

    def upload_records_to_firestore(self):
        """function to upload database records to firebase storage"""
        conn = sqlite3.connect('videoLogs.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM VideoLogs")
        rows = cursor.fetchall()

        for row in rows:
            data = {
                'id': row[0],
                'title': row[1],
                'detection_times': row[2],
                'detection_types': row[3],
                'saved_clip_location': row[4],
                'recorded_date': row[5],
                'intrusion_status': row[6],
                'intrusion_detected_at': row[7],
            }
            doc_ref = self.db.collection('VideoLogs').document()
            doc_ref.set(data)

        conn.close()

    def compress_and_upload_video(self, file_path, destination_path):
        """function to compress videos when uploading to firebase"""
        with open(file_path, 'rb') as f:
            original_data = f.read()
            compressed_data = zlib.compress(original_data)

        file_basename = os.path.basename(file_path)
        temp_path = os.path.join(os.path.dirname(file_path),
                                 file_basename.split('.')[0] + "_compressed." + file_basename.split('.')[1])

        with open(temp_path, 'wb') as f:
            f.write(compressed_data)

        bucket = storage.bucket()
        blob = bucket.blob(destination_path)
        self.safe_upload(blob.upload_from_filename, temp_path)

        os.remove(temp_path)

    def upload_original_video(self, file_path, destination_path):
        bucket = storage.bucket()
        blob = bucket.blob(destination_path)
        self.safe_upload(blob.upload_from_filename, file_path)

        # returning direct URL to access this video from Firebase Storage
        return blob.public_url

    def upload_all_recordings(self):
        """function to upload original and optimized recordings"""
        saved_recordings_path = 'savedRecordings'
        total_files = sum([len(files) for r, d, files in os.walk(saved_recordings_path) if
                           any(file.endswith(('.mp4', '.avi')) for file in files)])
        processed_files = 0

        for root, dirs, files in os.walk(saved_recordings_path):
            for file in files:
                if file.endswith(('.mp4', '.avi')):
                    processed_files += 1
                    print(f"Encoding and Uploading! {int((processed_files / total_files) * 100)}% completed...")

                    file_path = os.path.join(root, file)
                    reencoded_path = os.path.join(root, "reencoded_" + file)
                    self.reencode_video(file_path, reencoded_path)  # to re-encode the video

                    compressed_destination_path = os.path.join('optimizedVideos',
                                                               file.split('.')[0] + "_compressed." + file.split('.')[1])
                    original_destination_path = os.path.join('originalVideos', "reencoded_" + file)

                    # uploading compressed video
                    self.compress_and_upload_video(reencoded_path, compressed_destination_path)

                    # uploading re-encoded video and getting its URL
                    original_video_url = self.upload_original_video(reencoded_path, original_destination_path)

                    # update firestore with the new URL of re-encoded videos
                    doc_ref = self.db.collection('VideoLogs').where('saved_clip_location', '==', file_path).get()
                    if doc_ref:
                        doc_ref[0].reference.update({'saved_clip_location': original_video_url})

                    os.remove(reencoded_path)  # remove reencoded video from local storage

        print("Process Completed!")

    def execute_all(self):
        self.upload_records_to_firestore()
        self.upload_all_recordings()


if __name__ == '__main__':
    manager = FirebaseManager()
    manager.execute_all()
