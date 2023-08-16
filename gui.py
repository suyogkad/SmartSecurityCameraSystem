import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
import cv2
from motion_detection import detect_motion  # <-- import the detect_motion function


class VideoApp(QWidget):
    def __init__(self):
        super().__init__()

        # Create a timer to update the video feed.
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame_slot)

        self.cap = cv2.VideoCapture('sample2.mp4')

        ret, self.frame1 = self.cap.read()  # Read the first frame
        self.video_label = QLabel()

        start_button = QPushButton('Start Video', self)
        start_button.clicked.connect(self.start_video)

        layout = QVBoxLayout()
        layout.addWidget(start_button)
        layout.addWidget(self.video_label)

        self.setLayout(layout)

    def next_frame_slot(self):
        ret, frame2 = self.cap.read()
        if ret:
            frame_with_motion = detect_motion(self.frame1, frame2)  # Call the motion detection function
            frame_with_motion = cv2.cvtColor(frame_with_motion, cv2.COLOR_BGR2RGB)

            height, width, channel = frame_with_motion.shape
            bytes_per_line = 3 * width
            q_image = QImage(frame_with_motion.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(q_image)
            self.video_label.setPixmap(pixmap)

            self.frame1 = frame2  # Update frame1 to be the previous frame2

    def start_video(self):
        self.timer.start(int(1000. / 24))

    def closeEvent(self, event):
        self.cap.release()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VideoApp()
    window.show()
    sys.exit(app.exec_())
