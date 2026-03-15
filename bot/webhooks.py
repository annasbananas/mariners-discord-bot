import requests
from constants import WEBHOOK_URL
import logging

logger = logging.getLogger(__name__)

def send_webhook(message):
    try:
        response = requests.post(
            WEBHOOK_URL,
            json={"content": message}
        )
        logger.info(f"Webhook sent successfully: {response.json()}")
        return response.json()
    except Exception as e:
        logger.error(f"Error sending webhook: {e}") 
        return None