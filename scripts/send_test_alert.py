import os
from dotenv import load_dotenv
import requests

load_dotenv()


def send_telegram_alert(message):
    """Send alerts using telegram bot."""
    response = requests.post(
        f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage',
        data={'chat_id': CHAT_ID, 'text': message}
    ).json()
    return response

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
response = send_telegram_alert("API Test! Check log from: https://smartsecurity-01.web.app/")
print(response)