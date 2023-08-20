import os
import sys
import datetime
import torch
import cv2
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
                             QFileDialog, QWidget, QTextBrowser)
from PyQt5.QtGui import QPixmap, QIcon, QImage
from PyQt5.QtCore import Qt, QTimer
import sqlite3
from PyQt5.QtCore import QSize

# Initialize the model
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', device='cpu')



def process_frame(frame):
    # Inference
    results = model(frame)
    detected_info = [(model.names[int(i[-1])], i[-2]) for i in results.pred[0]]
    frame = results.render()[0]
    return frame, detected_info


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.title = 'Smart Security Camera'
        self.cap = None
        self.timer = None
        self.is_recording = False
        self.out = None
        self.recording_path = "LiveRecordings"
        self.button_style = """
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border-radius: 15px;
            padding: 10px 20px;
            font-size: 16px;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
        """
        self.init_home_page()
        self.create_database()
        self.last_detected_info = {}  # Stores the last detected info


    def create_database(self):
        self.conn = sqlite3.connect('videoLogs.db')
        self.cursor = self.conn.cursor()
        c = self.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS VideoLogs 
                     (id INTEGER PRIMARY KEY,
                      title TEXT, 
                      url TEXT, 
                      detection_timestamp TEXT, 
                      annotated_info TEXT, 
                      saved_clip_location TEXT,
                      recorded_date TEXT)''')
        self.conn.commit()

    def init_home_page(self):
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet("background-color: white;")

        main_layout = QVBoxLayout()

        # Logo at the top
        logo_label = QLabel(self)
        pixmap = QPixmap('logo.png')
        logo_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio))
        logo_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(logo_label)

        info_label = QLabel("Welcome to the Smart Security Camera application.\nChoose a video or start a live feed.",
                            self)
        info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(info_label)

        # Buttons layout
        button_layout = QHBoxLayout()
        # Change the font size for buttons and labels:
        button_style = """
        QPushButton {
            background-color: #4CAF50;
            color: white;
            border-radius: 15px;
            padding: 10px 20px;
            font-size: 16px;
        }
        
        QPushButton:hover {
            background-color: #45a049;
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

        main_layout.addLayout(button_layout)
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def browse_files(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", "MP4 Files (*.mp4);;All Files (*)",
                                                  options=options)
        if fileName:
            print(fileName)

    def start_live_feed(self):
        self.init_video_page()

    def init_video_page(self):
        layout = QVBoxLayout()
        self.video_surface = QLabel(self)
        layout.addWidget(self.video_surface)

        self.log_view = QTextBrowser(self)
        layout.addWidget(self.log_view)

        controls_layout = QHBoxLayout()
        go_back_button = QPushButton("Go Back", self)
        go_back_button.clicked.connect(self.stop_and_go_back)
        controls_layout.addWidget(go_back_button)

        # save_button = QPushButton("Save Session", self)
        # save_button.setStyleSheet(self.button_style)
        # save_button.clicked.connect(self.save_session)
        # controls_layout.addWidget(save_button)

        # self.save_button = save_button

        self.recording_button = QPushButton("Start Recording", self)
        self.recording_button.setStyleSheet(self.button_style)
        self.recording_button.clicked.connect(self.toggle_recording)
        controls_layout.addWidget(self.recording_button)

        layout.addLayout(controls_layout)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(20)

    # method for toggling recording state
    def toggle_recording(self):
        if self.is_recording:
            self.is_recording = False
            self.recording_button.setText("Start Recording")
            if self.out:
                self.out.release()
                self.out = None
        else:
            self.is_recording = True
            self.recording_button.setText("End Recording")
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            current_time_str = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join(self.recording_path, f'recording_{current_time_str}.avi')
            self.out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))

    def stop_and_go_back(self):
        if self.timer:
            self.timer.stop()
        if self.cap:
            self.cap.release()
        self.init_home_page()

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            detected_frame, detected_info = process_frame(frame)
            self.update_logs(detected_info)

            height, width, channel = detected_frame.shape
            bytes_per_line = 3 * width
            q_img = QImage(detected_frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            self.video_surface.setPixmap(QPixmap.fromImage(q_img))

        if self.is_recording:
            self.out.write(frame)

    def update_logs(self, detected_info):
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for item in detected_info:
            class_name, confidence = item
            if confidence > 0.7:
                # Check if the item is already in the last_detected_info
                if class_name in self.last_detected_info:
                    self.last_detected_info[class_name]["end_time"] = current_time
                else:
                    self.last_detected_info[class_name] = {"start_time": current_time, "end_time": current_time}

        # Update the log view (in a more real-world scenario, we might buffer and limit how often we update the GUI for performance)
        text_to_display = ""
        for class_name, times in self.last_detected_info.items():
            text_to_display += f"{class_name} detected from {times['start_time']} to {times['end_time']}\n"

        self.log_view.setText(text_to_display)

    def save_session(self):
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for class_name, times in self.last_detected_info.items():
            self.cursor.execute(
                "INSERT INTO VideoLogs (title, url, detection_timestamp, annotated_info, saved_clip_location, recorded_date) VALUES (?, ?, ?, ?, ?, ?)",
                ("Live Feed", "Camera URL", f"{times['start_time']} to {times['end_time']}", class_name,
                 "Saved Clip Location (if any)", current_time))
            self.conn.commit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec_())
