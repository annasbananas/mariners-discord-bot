import json
import os
import logging
from datetime import datetime
from pytz import timezone

# Configure a basic logger for better debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the path to your JSON file.
# It's a good practice to make this configurable.
# If you are using a Docker volume, this path should be within the mounted directory.
STATUS_FILE_PATH = 'data/status.json'

def get_status_from_file():
    """
    Reads the status data from the JSON file.

    Returns:
        dict: The status data as a dictionary.
        Returns a default dictionary if the file doesn't exist or is invalid.
    """
    # Define a default status dictionary for a clean slate
    default_status = {
        "game" : {
                "id": "",
                "status": "",
                "last_update_sent_at": ""
        }
    }

    if not os.path.exists(STATUS_FILE_PATH):
        logging.warning(f"Status file not found at {STATUS_FILE_PATH}. Creating a new one.")
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(STATUS_FILE_PATH), exist_ok=True)
        # Write the default status to the file
        with open(STATUS_FILE_PATH, 'w') as f:
            json.dump(default_status, f, indent=4)

    try:
        with open(STATUS_FILE_PATH, 'r') as f:
            status_data = json.load(f)
        logging.info(f"Successfully read status from file. Data: {status_data}")


    except json.JSONDecodeError:
        # This handles cases where the file might be empty or corrupted
        logging.error(f"Error decoding JSON from {STATUS_FILE_PATH}. File might be corrupted.")
        # Optionally, you can back up the corrupted file and create a new one
        os.rename(STATUS_FILE_PATH, f"{STATUS_FILE_PATH}.corrupted_{datetime.now().strftime('%Y%m%d%H%M%S')}")
        logging.warning("Corrupted file has been renamed. A new status file will be created.")

    except Exception as e:
        # A generic catch-all for other potential issues
        logging.error(f"An unexpected error occurred while reading the status file: {e}")

    return status_data.get("game", {})

def save_status_to_file(game_id, status):
    """
    Saves the provided status dictionary to the JSON file.

    Args:
        status_data (dict): The dictionary containing the status to save.
    """
    try:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(STATUS_FILE_PATH), exist_ok=True)
        current_time = datetime.now(timezone("America/Los_Angeles")).isoformat()
        current_status = {
            "game" : {
                "id": game_id,
                "status": status,
                "last_update_sent_at": current_time
            }
        }
        with open(STATUS_FILE_PATH, 'w') as f:
            json.dump(current_status, f, indent=4)
        logging.info("Successfully saved status to file.")
        
    except Exception as e:
        logging.error(f"Failed to save status to file: {e}")