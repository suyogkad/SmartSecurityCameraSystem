import cv2
import torch
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer

# initializing the model here
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', device='cpu')

def process_frame(frame):
    """function to process the frames"""
    results = model(frame)
    detected_info = [(model.names[int(i[-1])], i[-2]) for i in results.pred[0]]
    frame = results.render()[0]
    return frame, detected_info

class VideoBrowser(QWidget):
    def __init__(self, video_path, video_surface, log_view, parent=None):
        super(VideoBrowser, self).__init__(parent)
        self.video_path = video_path
        self.cap = None
        self.timer = None
        self.video_surface = video_surface
        self.log_view = log_view
        self.init_ui()

    def init_ui(self):
        """function to start UI"""
        layout = QVBoxLayout()

        self.start_button = QPushButton("Start", self)
        self.start_button.clicked.connect(self.start_video)
        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def start_video(self):
        """function to start video on button press"""
        self.cap = cv2.VideoCapture(self.video_path)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(20)

    def update_frame(self):
        """function to update the frame on every detection"""
        ret, frame = self.cap.read()
        if ret:
            detected_frame, detected_info = process_frame(frame)

            # to display the video frame
            height, width, channel = detected_frame.shape
            bytes_per_line = 3 * width
            q_img = QImage(detected_frame.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
            self.video_surface.setPixmap(QPixmap.fromImage(q_img))

            # to display the detected information
            text_to_display = "\n".join([f"{item[0]}: {item[1]:.2f}" for item in detected_info])
            self.log_view.setText(text_to_display)

    def stop_video(self):
        """function to end video on button press"""
        if self.timer:
            self.timer.stop()
        if self.cap:
            self.cap.release()