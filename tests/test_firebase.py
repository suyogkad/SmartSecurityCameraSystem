import unittest
from unittest.mock import patch, Mock
from firebase_manager import FirebaseManager


class TestFirebaseOperations(unittest.TestCase):

    def setUp(self):
        # Mocking firebase_admin and firestore
        self.firebase_admin_mock = Mock()
        self.firestore_mock = Mock()

        # Patching the relevant methods and classes
        self.patcher1 = patch('firebase_manager.credentials.Certificate', return_value="mocked_credentials")
        self.patcher2 = patch('firebase_manager.firebase_admin', self.firebase_admin_mock)
        self.patcher3 = patch('firebase_manager.firestore.client', return_value=self.firestore_mock)

        # Start the patching
        self.patcher1.start()
        self.patcher2.start()
        self.patcher3.start()

        self.firebase_manager = FirebaseManager()

    def tearDown(self):
        # Stop the patching
        self.patcher1.stop()
        self.patcher2.stop()
        self.patcher3.stop()

    def test_upload_records_to_firestore(self):
        # Mock the firestore methods
        mock_collection = Mock()
        mock_query = Mock()

        self.firestore_mock.collection.return_value = mock_collection
        mock_collection.where.return_value = mock_query
        mock_query.get.return_value = []

        # Invoke the method
        self.firebase_manager.upload_records_to_firestore()

        mock_collection.where.assert_called_once_with('title', '==', 'Test Video Title')

    @patch("firebase_manager.sqlite3.connect")
    def test_upload_records_to_firestore(self, mock_connect):
        # Mock SQLite connection and cursor
        mock_conn = Mock()
        mock_cursor = Mock()

        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock the return value for cursor.execute
        mock_cursor.execute.return_value = None
        mock_cursor.fetchone.return_value = None


if __name__ == '__main__':
    unittest.main()
