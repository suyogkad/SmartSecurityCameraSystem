import os
from dotenv import load_dotenv
import sys
import datetime
import torch
import cv2
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
                             QFileDialog, QWidget, QTextBrowser, QMessageBox)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer
import sqlite3
import warnings

load_dotenv()
warnings.filterwarnings("ignore", category=UserWarning, module='urllib3')


# initializing the model here
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', device='cpu')

# my telegram settings
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# defining ROI coordinates here [top-left-x, top-left-y, bottom-right-x, bottom-right-y]
roi_start_point = None
roi_end_point = None
drawing = False  # set true if the user is drawing ROI
ROI = [100, 100, 600, 600]
if roi_start_point and roi_end_point:
    ROI = [roi_start_point[0], roi_start_point[1], roi_end_point[0], roi_end_point[1]]

# global variables
roi_set = False # new variable to check if the ROI is set or not
roi_start_point = None
roi_end_point = None
drawing = False  # set true if the user is drawing the ROI

def send_telegram_alert(title, intrusion_status=None, intrusion_time=None, immediate=False, detected_object=None):
    """function to send alerts using telegram bot"""
    if immediate and detected_object:
        message = (f"Intrusion detected at monitored area! {detected_object} at {intrusion_time}. Check log from: "
                   f"https://smartsecurity-01.web.app/.")
    else:
        return

    response = requests.post(
        f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
        data={'chat_id': CHAT_ID, 'text': message}
    ).json()
    return response



def roi_callback(event, x, y, flags, param):
    global roi_start_point, roi_end_point, drawing, frame
    """to handles mouse events to set the ROI."""

    # if left mouse button clicked, record the starting ROI point
    if event == cv2.EVENT_LBUTTONDOWN:
        if not drawing:
            drawing = True
            roi_start_point = (x, y)
        else:
            drawing = False
            roi_end_point = (x, y)
            cv2.rectangle(frame, roi_start_point, roi_end_point, (0, 255, 0), 2)
            cv2.imshow('Video Feed', frame)



def process_frame(self, frame, last_detected):
    """funtion to process the updated frames"""
    global roi_start_point, roi_end_point
    # Draw the ROI if it has been set
    if roi_start_point and roi_end_point:
        cv2.rectangle(frame, roi_start_point, roi_end_point, (0, 255, 0), 2)
    detected_info = []
    current_detected_objects = []
    intrusion_detected = False

    # initializing model to process frames
    results = model(frame)
    detected_info = [(model.names[int(i[-1])], i[-2]) for i in results.pred[0]]
    frame = results.render()[0]
    current_detected_objects = [item[0] for item in detected_info]

    if roi_set: # only checks detections if ROI has been set
        # to check each detection to see if it's within the ROI
        for *box, _, cls in results.pred[0]:
            x1, y1, x2, y2 = map(int, box)
            detected_object = model.names[int(cls)]
            if (x1 >= ROI[0] and y1 >= ROI[1] and x2 <= ROI[2] and y2 <= ROI[3]):
                # check if this object was not in the last_detected list
                if detected_object not in last_detected:
                    # sending immediate alert for any NEW object inside the ROI
                    send_telegram_alert(f"Intrusion detected: {detected_object} in the monitored area!", immediate=True, detected_object=detected_object, intrusion_time=datetime.datetime.now().strftime('%H:%M:%S'))
                    intrusion_detected = True

    return frame, detected_info, current_detected_objects, intrusion_detected



class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Smart Security Camera')
        self.setGeometry(100, 100, 800, 600)
        self.cap = None
        self.timer = QTimer(self)  # initializing the timer
        self.timer.timeout.connect(self.update_frame)  # for connecting timer's timeout signal
        self.is_recording = False
        self.out = None
        self.recording_path = "savedRecordings"
        self.last_detected_info = {}
        self.create_database()
        self.init_home_page()

    def create_database(self):
        """creates a database if it doesn't exist."""
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

    def set_roi(self):
        """function to set ROI using a mouse callback."""
        global roi_set
        cv2.namedWindow("Set ROI")
        cv2.setMouseCallback("Set ROI", roi_callback)
        while True:
            ret, frame = self.cap.read()
            if ret:
                if roi_start_point and roi_end_point:
                    cv2.rectangle(frame, roi_start_point, roi_end_point, (0, 255, 0), 2)
                cv2.imshow('Set ROI', frame)
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # press 'Esc' key to break the loop
                    break

        cv2.destroyWindow("Set ROI")
        if roi_start_point and roi_end_point:
            ROI[0], ROI[1] = roi_start_point
            ROI[2], ROI[3] = roi_end_point
            roi_set = True

    def init_home_page(self):
        """function to initialize the home page."""
        layout = QVBoxLayout()

        # top logo properties
        logo_label = QLabel(self)
        pixmap = QPixmap('logo.png')
        logo_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        # middle text properties
        about_label = QLabel("Thank you for choosing Smart Security. This application detects objects in real-time video feeds.", self)
        about_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(about_label)

        # home page buttons properties
        button_layout = QHBoxLayout()
        self.browse_button = QPushButton('Browse Video Files', self)
        self.browse_button.setStyleSheet("background-color: green; border-radius: 25px; font-size: 16px; color: #ffffff;")
        self.browse_button.clicked.connect(self.browse_files)
        button_layout.addWidget(self.browse_button)

        # to set the buttons properties
        self.live_feed_button = QPushButton('Live Video Feed', self)
        self.live_feed_button.setStyleSheet("background-color: green; border-radius: 25px; font-size: 16px; color: #ffffff;")
        self.live_feed_button.clicked.connect(self.start_live_feed)
        button_layout.addWidget(self.live_feed_button)

        # to set the window properties
        layout.addLayout(button_layout)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.setStyleSheet("background-color: white;")

    def browse_files(self):
        """function to open a file dialogbox to start processing the selected video."""
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "MP4 Files (*.mp4);;All Files (*)", options=options)
        if fileName:
            self.cap = cv2.VideoCapture(fileName)
            self.init_video_page(fileName)
            self.start_video()

    def start_live_feed(self):
        """function to start the live video feed."""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QMessageBox.warning(self, "Camera Error", "Could not open camera.") # shows camera error message
            return
        self.init_video_page("Live Feed")
        self.start_video()

    def init_video_page(self, video_title):
        """function to initialize the video playback page."""
        layout = QVBoxLayout()
        self.video_surface = QLabel(self)
        layout.addWidget(self.video_surface)

        self.log_view = QTextBrowser(self)
        layout.addWidget(self.log_view)

        # properties for go back button
        controls_layout = QHBoxLayout()
        go_back_button = QPushButton("Go Back", self)
        go_back_button.setStyleSheet("background-color: #3498db; border-radius: 10px; font-size: 16px; color: #ffffff;")
        go_back_button.clicked.connect(self.stop_and_go_back)
        controls_layout.addWidget(go_back_button)

        # properties for start recording button
        self.recording_button = QPushButton("Start Recording", self)
        self.recording_button.setStyleSheet("background-color: #3498db; border-radius: 10px; font-size: 16px; color: #ffffff;")
        self.recording_button.clicked.connect(self.toggle_recording)
        controls_layout.addWidget(self.recording_button)

        layout.addLayout(controls_layout)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.setStyleSheet("background-color: white;") # set layout color to white

        self.video_title = video_title

        self.monitor_area_button = QPushButton("Monitor Area", self)  # monitor Button
        self.monitor_area_button.setStyleSheet(
            "background-color: #3498db; border-radius: 10px; font-size: 16px; color: #ffffff;")
        self.monitor_area_button.clicked.connect(self.set_roi)
        controls_layout.addWidget(self.monitor_area_button)

        layout.addLayout(controls_layout)

    def start_video(self):
        """function to start the video or live feed."""
        self.last_detected = set()  # to keep track of last detected objects
        self.timer.start(20)

    def toggle_recording(self):
        """function to toggle between recording and not recording UI."""
        if self.is_recording:
            self.is_recording = False
            self.recording_button.setText("Start Recording")
            self.recording_button.setStyleSheet("background-color: #3498db; border-radius: 10px; font-size: 16px; color: #ffffff;")
            if self.out:
                self.out.release()
                self.out = None
                self.save_session()
        else:
            self.is_recording = True
            self.recording_button.setText("● Recording...")  # add a dot to indicate recording
            self.recording_button.setStyleSheet("background-color: red; border-radius: 10px; font-size: 16px; color: #ffffff;")
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            video_name = f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.mp4"
            self.current_recording_path = os.path.join(self.recording_path, video_name)
            self.out = cv2.VideoWriter(self.current_recording_path, fourcc, 20.0, (int(self.cap.get(3)), int(self.cap.get(4))))
            self.last_detected_info = {}  # this will reset the detection information

    def update_frame(self):
        """function to update the video frame, process it and check for detections in ROI."""
        ret, frame = self.cap.read()
        if ret:
            frame, detected_info, current_detected_objects, intrusion_detected = self.process_frame(frame, [])
            self.last_detected = set(current_detected_objects)

            # to draw the ROI
            cv2.rectangle(frame, (ROI[0], ROI[1]), (ROI[2], ROI[3]), (0, 255, 0), 2)

            # to log the detections
            current_time = datetime.datetime.now().strftime('%H:%M:%S')
            for item, confidence in detected_info:
                if item not in self.last_detected_info:
                    self.last_detected_info[item] = {
                        "first_detected": current_time,
                        "last_detected": current_time
                    }
                else:
                    self.last_detected_info[item]["last_detected"] = current_time

                # to show logs in the console
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
        """function to stop the video feed or playback and go back to the home page."""
        self.timer.stop()
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.out:
            self.out.release()
            self.out = None
        self.init_home_page()

    def save_session(self):
        """function to save session to database with intrusion data."""
        c = self.conn.cursor()
        # storing detections
        detection_times = ",".join([f"{obj}:{info['first_detected']}-{info['last_detected']}" for obj, info in
                                    self.last_detected_info.items()])
        detection_types = ",".join([i for i in self.last_detected_info])
        intrusion_status = "Detected" if any(
            [item for item in self.last_detected_info if item in ["person", "car", "bike"]]) else "Not Detected"

        # this will create a list of intrusion times
        intrusion_time_list = []
        for obj in ["person", "car", "bike"]:
            if obj in self.last_detected_info:
                time_range = f"{self.last_detected_info[obj]['first_detected']} - {self.last_detected_info[obj]['last_detected']}"
                intrusion_time_list.append(f"{obj} detected from {time_range}")

        # to convert list to string for storage
        intrusion_time = ", ".join(intrusion_time_list)

        # to insert values in the tables
        c.execute(
            "INSERT INTO VideoLogs (title, detection_times, detection_types, saved_clip_location, recorded_date, intrusion_status, intrusion_detected_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (self.video_title, detection_times, detection_types, self.current_recording_path,
             datetime.datetime.now().strftime('%Y-%m-%d'), intrusion_status, intrusion_time))
        self.conn.commit()

        # to display a confirmation message
        QMessageBox.information(self, "Information", "Session data has been saved to the database.")

    def closeEvent(self, event):
        """function to clean resources on app close."""
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.out:
            self.out.release()
            self.out = None
        if self.conn:
            self.conn.close()
            self.conn = None
        event.accept()


if __name__ == '__main__':
    # to set the mouse callback for ROI selection
    cv2.namedWindow('Video Feed')
    cv2.setMouseCallback('Video Feed', roi_callback)

    app = QApplication(sys.argv)
    main_window = App()
    main_window.show()
    sys.exit(app.exec_())