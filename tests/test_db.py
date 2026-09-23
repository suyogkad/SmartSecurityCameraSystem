import unittest
import sqlite3
import os
import tempfile

# use a throwaway database so the real videoLogs.db is never touched
TEST_DB = os.path.join(tempfile.gettempdir(), 'test_videoLogs.db')

class TestDatabaseOperations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up the database for the entire class once."""
        cls.conn = sqlite3.connect(TEST_DB)
        c = cls.conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS VideoLogs 
                     (id INTEGER PRIMARY KEY,
                      title TEXT,
                      detection_times TEXT,
                      detection_types TEXT,
                      saved_clip_location TEXT,
                      recorded_date TEXT,
                      intrusion_status TEXT,
                      intrusion_detected_at TEXT)''')
        cls.conn.commit()
        print("Database setup completed.")

    def test_database_creation(self):
        """Test the creation of the database and the VideoLogs table."""
        # check if the database file exists
        self.assertTrue(os.path.exists(TEST_DB), "Database file doesn't exist.")
        print("Database file exists.")

        # check if the VideoLogs table exists
        c = self.conn.cursor()
        c.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='VideoLogs';''')
        table_exists = c.fetchone()
        self.assertIsNotNone(table_exists, "VideoLogs table doesn't exist.")
        print("VideoLogs table exists.")

    def test_save_session(self):
        """Test saving a session to the database."""
        print("Saving session to the database...")

        video_title = "Test Video Title"
        last_detected_info = {
            "person": {"first_detected": "10:00", "last_detected": "10:05"},
            "car": {"first_detected": "10:10", "last_detected": "10:15"}
        }
        detection_times = ",".join([f"{obj}:{info['first_detected']}-{info['last_detected']}" for obj, info in last_detected_info.items()])
        detection_types = ",".join([i for i in last_detected_info])
        intrusion_status = "Detected" if any([item for item in last_detected_info if item in ["person", "car", "bike"]]) else "Not Detected"
        intrusion_time_list = []
        for obj in ["person", "car", "bike"]:
            if obj in last_detected_info:
                time_range = f"{last_detected_info[obj]['first_detected']} - {last_detected_info[obj]['last_detected']}"
                intrusion_time_list.append(f"{obj} detected from {time_range}")
        intrusion_time = ", ".join(intrusion_time_list)

        c = self.conn.cursor()
        c.execute(
            "INSERT INTO VideoLogs (title, detection_times, detection_types, saved_clip_location, recorded_date, intrusion_status, intrusion_detected_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (video_title, detection_times, detection_types, "placeholder_path",
             "2023-08-21", intrusion_status, intrusion_time))
        self.conn.commit()

        print("Session saved.")

        # check if the saved session exists in the database
        c.execute('''SELECT * FROM VideoLogs WHERE title=?''', ("Test Video Title",))
        saved_session = c.fetchone()
        self.assertIsNotNone(saved_session, "Failed to save session to the database.")
        print("Saved session found in the database.")

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        cls.conn.close()
        os.remove(TEST_DB)  # Delete the database file
        print("Database cleanup completed.")

if __name__ == "__main__":
    unittest.main()
