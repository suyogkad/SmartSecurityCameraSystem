import unittest
import torch

class TestModelLoading(unittest.TestCase):

    def test_load_model(self):
        """Testing if the model loads correctly."""
        try:
            model = torch.hub.load('ultralytics/yolov5', 'yolov5s', device='cpu')
            self.assertIsNotNone(model)
            self.assertTrue(hasattr(model, 'forward'))
        except Exception as e:
            self.fail(f"Model loading failed with error: {e}")






