import unittest
from app import detect_objects


class TestObjectDetection(unittest.TestCase):

    def test_object_detection(self):
        # Loading a test image which contains a 'person' and 'cell phone'
        test_image_path = 'tests/testimage.jpg'

        # Call object detection function
        detected_labels = detect_objects(test_image_path)

        # Check if 'cell phone' and 'person' labels are detected
        self.assertIn('cell phone', detected_labels)
        self.assertIn('person', detected_labels)

        # Print the detected object labels to the console
        print(f"Detected labels: {', '.join(detected_labels)}")


if __name__ == "__main__":
    unittest.main()
