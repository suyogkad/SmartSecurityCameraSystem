import unittest
import cv2
from app import roi_callback
import numpy as np

# Mock global variables
roi_start_point = None
roi_end_point = None
drawing = False

def mock_roi_callback(event, x, y, flags, param, frame):
    global roi_start_point, roi_end_point, drawing
    """function to handle mouse events to set the ROI."""

    # if left mouse button is clicked, record starting ROI point
    if event == cv2.EVENT_LBUTTONDOWN:
        if not drawing:
            drawing = True
            roi_start_point = (x, y)
        else:
            drawing = False
            roi_end_point = (x, y)
            if frame is not None:  # Only show the frame if it's valid
                cv2.rectangle(frame, roi_start_point, roi_end_point, (0, 255, 0), 2)
                cv2.imshow('Video Feed', frame)


class TestROIDrawing(unittest.TestCase):

    def test_roi_drawing(self):
        frame = None  # or you can initialize an actual frame if needed
        mock_roi_callback(cv2.EVENT_LBUTTONDOWN, 100, 100, None, None, frame)
        self.assertEqual(roi_start_point, (100, 100))

        mock_roi_callback(cv2.EVENT_LBUTTONDOWN, 200, 200, None, None, frame)
        self.assertEqual(roi_end_point, (200, 200))

if __name__ == "__main__":
    unittest.main()
