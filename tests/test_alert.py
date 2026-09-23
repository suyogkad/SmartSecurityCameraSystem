import unittest
from app import send_telegram_alert
import warnings
warnings.simplefilter("ignore", category=UserWarning)
warnings.filterwarnings("ignore", module="urllib3")

class TestTelegramAlerts(unittest.TestCase):

    def test_telegram_alert(self):
        try:
            response = send_telegram_alert("Test alert message!", intrusion_status="Detected",
                                           intrusion_time="12:34 PM")

            # check if response contains the "ok" key and its value is True
            self.assertTrue(response.get("ok"))

        except Exception as e:
            self.fail(f"Sending Telegram alert raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()