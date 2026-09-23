import sys
import unittest
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

# Basic mockup of the application
class SampleApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sample App")
        self.setGeometry(100, 100, 280, 80)

        # Label
        self.label = QLabel(self)
        self.label.setText("Welcome to Sample App!")
        self.label.move(10, 10)

        # Navigation button
        self.nav_button = QPushButton("Navigate", self)
        self.nav_button.move(10, 40)
        self.nav_button.clicked.connect(self.on_nav_clicked)

    def on_nav_clicked(self):
        self.label.setText("Navigation clicked!")

# Unittest for the app
class TestUIComponentsAndNavigation(unittest.TestCase):
    def setUp(self):
        """Set up the application and the main window."""
        self.app = QApplication(sys.argv)
        self.main_window = SampleApp()
        self.main_window.show()

    def test_label_text(self):
        """Test if the label displays the correct text."""
        self.assertEqual(self.main_window.label.text(), "Welcome to Sample App!")

    def test_navigation(self):
        """Test navigation button click."""
        QTest.mouseClick(self.main_window.nav_button, Qt.LeftButton)
        self.assertEqual(self.main_window.label.text(), "Navigation clicked!")

    def tearDown(self):
        """Clean up after tests."""
        self.main_window.close()

if __name__ == "__main__":
    unittest.main()
