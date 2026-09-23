import os
import sys
import datetime
import torch
import cv2
import requests
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
                             QFileDialog, QWidget, QTextBrowser, QMessageBox)
from PyQt5.QtGui import QPixmap, QImage, QFont, QIcon
from PyQt5.QtCore import Qt, QTimer
import sqlite3
import pandas as pd
import firebase_manager
import firebase_manager as fm
from firebase_manager import FirebaseManager
import warnings
from dotenv import load_dotenv

load_dotenv()
warnings.filterwarnings("ignore", category=UserWarning, module='urllib3')

# loading the model for detection
myModel = torch.hub.load('ultralytics/yolov5', 'yolov5s', device='cpu')

# telegram settings (loaded from .env)
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# objects detected inside the ROI, with the times they were seen
last_detected_info = {}

# defining ROI coordinates
roi_start_point = None
roi_end_point = None
drawing = False  # True if the user is drawing the ROI
ROI = [100, 100, 400, 400]
if roi_start_point and roi_end_point:
    ROI = [roi_start_point[0], roi_start_point[1], roi_end_point[0], roi_end_point[1]]

# global variables
roi_start_point = None
roi_end_point = None
drawing = False  # True if the user is drawing the ROI


def send_telegram_alert(title, intrusion_status=None, intrusion_time=None, immediate=False, detected_object=None):
    """function to send alerts using telegram bot with detailed info"""
    if immediate and detected_object:
        message = f"Intrusion detected at {intrusion_time} due to a detected {detected_object}."
    elif intrusion_status == "Detected":
        message = f"Intrusion detected at monitored area! {intrusion_time}. View from: https://smartsecurity-01.web.app/"
    else:
        return

    if not BOT_TOKEN or not CHAT_ID:
        return  # telegram alerts are disabled when no credentials are set

    response = requests.post(
        f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
        data={'chat_id': CHAT_ID, 'text': message}
    ).json()
    return response


def roi_callback(event, x, y, flags, param, frame):
    """function to handle mouse events to set the ROI."""
    global roi_start_point, roi_end_point, drawing

    # if left mouse button is clicked, record starting ROI point
    if event == cv2.EVENT_LBUTTONDOWN:
        if not drawing:
            drawing = True
            roi_start_point = (x, y)
        else:
            drawing = False
            roi_end_point = (x, y)
            cv2.rectangle(frame, roi_start_point, roi_end_point, (0, 255, 0), 2)
            cv2.imshow('Video Feed', frame)


def detect_objects(image_path='tests/testimage.jpg'):
    """function to detect objects in an image"""

    # Inference
    results = myModel(image_path)

    # Extract detected object labels
    detected_labels = [results.names[int(det[5])] for det in results.pred[0]]

    return detected_labels


# Updated the process_frame function
def process_frame(frame, last_detected):
    global roi_start_point, roi_end_point
    # Draw the ROI if it has been set
    if roi_start_point and roi_end_point:
        cv2.rectangle(frame, roi_start_point, roi_end_point, (0, 255, 0), 2)

    detected_info = []
    current_detected_objects = []
    intrusion_detected = False

    # to process the frame using model
    results = myModel(frame)
    detected_info = [(myModel.names[int(i[-1])], i[-2]) for i in results.pred[0]]
    frame = results.render()[0].copy()
    current_detected_objects = [item[0] for item in detected_info]

    # to check each detection and see if it's within the ROI
    for *box, _, cls in results.pred[0]:
        x1, y1, x2, y2 = map(int, box)
        detected_object = myModel.names[int(cls)]
        if (x1 >= ROI[0] and y1 >= ROI[1] and x2 <= ROI[2] and y2 <= ROI[3]):
            # updating the last_detected_info
            if detected_object not in last_detected_info.keys():
                last_detected_info[detected_object] = [datetime.datetime.now().strftime('%I:%M:%S %p')]
            else:
                last_detected_info[detected_object].append(datetime.datetime.now().strftime('%I:%M:%S %p'))

            # sending alert only if the object is not in the last_detected set
            if detected_object not in last_detected:
                intrusion_detected = True
                # sending immediate alert for any object inside ROI
                send_telegram_alert(f"Intrusion detected: {detected_object} in the monitored area!")

    return frame, detected_info, current_detected_objects, intrusion_detected


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Smart Security Camera')
        self.setGeometry(100, 100, 800, 600)
        self.cap = None
        self.timer = QTimer(self)  # Initializing the timer
        self.timer.timeout.connect(self.update_frame)  # Connecting timer's timeout signal
        self.is_recording = False
        self.out = None
        self.recording_path = "."
        self.last_detected_info = {}
        self.create_database()
        self.init_home_page()
        try:
            self.fm = FirebaseManager()
        except Exception:
            self.fm = None  # cloud backup is unavailable without firebase credentials
            print("Firebase credentials not found. Recordings will be saved locally only.")

    def create_database(self):
        """Create a database if it doesn't exist."""
        self.conn = sqlite3.connect('videoLogs.db')
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS VideoLogs 
                     (id INTEGER PRIMARY KEY,
                      title TEXT,
                      detection_times TEXT,
                      detection_types TEXT,
                      saved_clip_location TEXT,
                      recorded_date TEXT,
                      intrusion_status TEXT,
                      intrusion_detected_at TEXT)''')
        self.conn.commit()

    def init_home_page(self):
        """Initialize the home page."""
        # Apply the modern 'Poppins' font to the entire window.
        self.setFont(QFont('Poppins', 11))

        main_layout = QVBoxLayout()

        # Top row with logo and about icon
        top_layout = QHBoxLayout()
        logo_label = QLabel(self)
        pixmap = QPixmap('assets/logo.png')
        logo_label.setPixmap(pixmap.scaled(300, 300, Qt.KeepAspectRatio))
        logo_label.setAlignment(Qt.AlignCenter)

        # About icon
        about_icon = QPushButton(QIcon('assets/about_icon.png'), "", self)
        about_icon.setToolTip('About this software')
        about_icon.clicked.connect(self.show_about_window)
        about_icon.setMaximumSize(40, 40)
        about_icon.setStyleSheet("background-color: transparent; border: none;")

        top_layout.addWidget(logo_label, 1, Qt.AlignCenter)
        top_layout.addWidget(about_icon, 0, Qt.AlignRight)

        # about the system
        description_style = """
        QLabel {
            font-size: 18px;
            text-align: center;
            margin-left: 30px;
            margin-right: 30px;
        }
        """

        description_text = """
        Vigilantly guarding your space with state-of-the-art intrusion detection.<br>
        Capture every unusual movement, ensuring no breach goes unnoticed. <br>Provides smart features
        like intrusion mobile alerts,<br> cloud security and data backup.
        """

        about_label = QLabel(description_text, self)
        about_label.setStyleSheet(description_style)
        about_label.setAlignment(Qt.AlignCenter)

        # Buttons
        button_layout = QHBoxLayout()

        # Button Styles
        button_style = """
        QPushButton {
            background-color: #FF5408;
            border-radius: 25px;
            font-size: 16px;
            color: #ffffff;
            padding: 15px 25px;
            border: 2px solid rgba(255, 102, 34, 0.5);
        }
        QPushButton:hover {
            background-color: #E84D00;
        }
        """

        self.browse_button = QPushButton('Browse Video Files', self)
        self.browse_button.setStyleSheet(button_style)
        self.browse_button.clicked.connect(self.browse_files)
        button_layout.addWidget(self.browse_button)

        self.live_feed_button = QPushButton('Live Video Feed', self)
        self.live_feed_button.setStyleSheet(button_style)
        self.live_feed_button.clicked.connect(self.start_live_feed)
        button_layout.addWidget(self.live_feed_button)

        # Add layouts/widgets to the main layout
        main_layout.addLayout(top_layout)
        main_layout.addWidget(about_label)
        main_layout.addLayout(button_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.setStyleSheet("background-color: white;")

    def show_about_window(self):
        msg = QMessageBox()
        msg.setWindowTitle("About")
        msg.setText("Smart Security v3.0 - Advanced Intrusion Detection System")
        msg.setInformativeText("Developer: hi@suyogkadariya.com.np")
        msg.setIcon(QMessageBox.Information)
        msg.exec()

    def browse_files(self):
        """Open a file dialog and start processing the selected video."""
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "MP4 Files (*.mp4);;All Files (*)",
                                                  options=options)
        if fileName:
            self.cap = cv2.VideoCapture(fileName)
            self.init_video_page(fileName)
            self.start_video()

    def start_live_feed(self):
        """Start the live video feed."""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QMessageBox.warning(self, "Camera Error", "Could not open camera.")
            return
        self.init_video_page("Live Feed")
        self.start_video()

    def init_video_page(self, video_title):
        """Initialize the video playback page."""
        layout = QVBoxLayout()
        self.video_surface = QLabel(self)
        layout.addWidget(self.video_surface)

        self.log_view = QTextBrowser(self)
        layout.addWidget(self.log_view)

        controls_layout = QHBoxLayout()
        go_back_button = QPushButton("Go Back", self)
        go_back_button.setStyleSheet("background-color: #3498db; border-radius: 10px; font-size: 16px; color: #ffffff;")
        go_back_button.clicked.connect(self.stop_and_go_back)
        controls_layout.addWidget(go_back_button)

        self.recording_button = QPushButton("Start Recording", self)
        self.recording_button.setStyleSheet(
            "background-color: #3498db; border-radius: 10px; font-size: 16px; color: #ffffff;")
        self.recording_button.clicked.connect(self.toggle_recording)
        controls_layout.addWidget(self.recording_button)

        layout.addLayout(controls_layout)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.setStyleSheet("background-color: white;")

        self.video_title = video_title

    def start_video(self):
        """Start the video or live feed."""
        self.last_detected = set()  # Keep track of last detected objects
        self.timer.start(20)

    def toggle_recording(self):
        """Toggle between recording and not recording."""
        if self.is_recording:
            self.is_recording = False
            self.recording_button.setText("Start Recording")
            self.recording_button.setStyleSheet(
                "background-color: #3498db; border-radius: 10px; font-size: 16px; color: #ffffff;")
            if self.out:
                self.out.release()
                self.out = None
                self.save_session()
                self.move_recording_to_saved_folder()
        else:
            self.is_recording = True
            self.recording_button.setText("● Recording...")  # Adding a circle to indicate recording
            self.recording_button.setStyleSheet(
                "background-color: red; border-radius: 10px; font-size: 16px; color: #ffffff;")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_name = f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4"
            self.current_recording_path = os.path.join(self.recording_path, video_name)
            self.out = cv2.VideoWriter(self.current_recording_path, fourcc, 20.0,
                                       (int(self.cap.get(3)), int(self.cap.get(4))))
            self.last_detected_info = {}  # Resetting detection information

    def update_frame(self):
        """Update the video frame, process it, and check for detections in ROI."""
        ret, frame = self.cap.read()
        if ret:
            frame, detected_info, current_detected_objects, intrusion_detected = process_frame(frame,
                                                                                               self.last_detected)
            self.last_detected = set(current_detected_objects)

            # Draw the ROI
            cv2.rectangle(frame, (ROI[0], ROI[1]), (ROI[2], ROI[3]), (0, 255, 0), 2)

            # Logging detections
            current_time = datetime.datetime.now().strftime('%I:%M:%S %p')
            for item, confidence in detected_info:
                if item not in self.last_detected_info:
                    self.last_detected_info[item] = {
                        "first_detected": current_time,
                        "last_detected": current_time
                    }
                else:
                    self.last_detected_info[item]["last_detected"] = current_time

                # Logging for display
                self.log_view.append(f"[{current_time}] Detected {item} with confidence {confidence:.2f}%")

            if intrusion_detected:
                self.log_view.append(f"[{current_time}] Intrusion detected in the monitored area!")

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = frame.shape
            step = channel * width
            qImg = QImage(frame.data, width, height, step, QImage.Format_RGB888)
            self.video_surface.setPixmap(QPixmap.fromImage(qImg))

            if self.is_recording:
                self.out.write(frame)
        else:
            self.stop_and_go_back()

    def stop_and_go_back(self):
        """Stop the video feed or playback and go back to the home page."""
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.out:
            self.out.release()
            self.out = None
        self.init_home_page()

    def save_session(self):
        """Save session to database with intrusion data."""
        # destination path for the original videos
        destination_path = "originalVideos/" + os.path.basename(self.current_recording_path)

        # Check for internet connectivity
        try:
            fm_instance = FirebaseManager()
            video_url = fm_instance.upload_original_video(self.current_recording_path, destination_path)
        except Exception as e:
            print("Error uploading to Firebase. Run firebase_manager.py manually after connecting to the internet.")
            # Save the video locally in the savedRecordings folder
            local_save_path = os.path.join('savedRecordings', os.path.basename(self.current_recording_path))
            shutil.copy2(self.current_recording_path, local_save_path)
            print(f"Video saved locally at: {local_save_path}")
            return

        c = self.conn.cursor()
        # Storing detections as "object:first_detected-last_detected"
        detection_times = ",".join([f"{obj}:{info['first_detected']}-{info['last_detected']}" for obj, info in
                                    self.last_detected_info.items()])
        detection_types = ",".join([i for i in self.last_detected_info])
        intrusion_status = "Detected" if any(
            [item for item in self.last_detected_info if item in ["person", "car", "bike"]]) else "Not Detected"
        intrusion_time_list = []
        for obj in ["person", "car", "bike"]:
            if obj in self.last_detected_info:
                time_range = f"{self.last_detected_info[obj]['first_detected']} - {self.last_detected_info[obj]['last_detected']}"
                intrusion_time_list.append(f"{obj} detected from {time_range}")
        intrusion_time = ", ".join(intrusion_time_list)

        c.execute(
            "INSERT INTO VideoLogs (title, detection_times, detection_types, saved_clip_location, recorded_date, intrusion_status, intrusion_detected_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.video_title, detection_times, detection_types, self.current_recording_path,
             datetime.datetime.now().strftime('%Y-%m-%d'), intrusion_status, intrusion_time))
        self.conn.commit()

        # After saving, send a telegram alert if an intrusion is detected
        if intrusion_status == "Detected":
            send_telegram_alert(self.video_title, intrusion_status, intrusion_time)

    def move_recording_to_saved_folder(self):
        """Move the recorded video to the savedRecordings folder."""
        dest_folder = "savedRecordings"
        if not os.path.exists(dest_folder):
            os.makedirs(dest_folder)

        dest_path = os.path.join(dest_folder, os.path.basename(self.current_recording_path))
        shutil.move(self.current_recording_path, dest_path)
        self.current_recording_path = dest_path

    def closeEvent(self, event):
        if self.cap:
            self.cap.release()
        if self.out:
            self.out.release()
        self.conn.close()  # Closing the database connection
        event.accept()


def export_to_csv():
    # connect to the SQLite database
    conn = sqlite3.connect('videoLogs.db')

    # to query data from the database into pandas dataframe
    query = "SELECT * FROM VideoLogs"
    df = pd.read_sql_query(query, conn)

    # add a new column for full video path
    df['full_video_path'] = './savedRecordings/' + df['saved_clip_location']

    # export the dataframe to CSV file
    df.to_csv('dataset.csv', index=False)

    # close the connection
    conn.close()


if __name__ == '__main__':
    # to set the mouse callback for ROI selection
    cv2.namedWindow('Video Feed')
    cv2.setMouseCallback('Video Feed', roi_callback)

    app = QApplication(sys.argv)
    main_window = App()
    main_window.show()
    sys.exit(app.exec_())
