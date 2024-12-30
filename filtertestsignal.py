import sqlite3
import RPi.GPIO as GPIO
import time
# Constants
DATABASE_FILE_PATH = 'pm25_data.db'
FILTER_PIN = 18  # GPIO pin to control
# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(FILTER_PIN, GPIO.OUT)
# Database connection
try:
    connection = sqlite3.connect(DATABASE_FILE_PATH)
    cursor = connection.cursor()
except sqlite3.Error as e:
    print(f"Error connecting to database: {str(e)}")
    exit(1)
def get_most_recent_filter_state():
    """Fetch the most recent filter state from the filter_state table."""
    try:
        cursor.execute("SELECT filter_state FROM filter_state ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        if result:
            return result[0]
        else:
            print("No filter state entries found.")
            return None
    except sqlite3.Error as e:
        print(f"Error fetching filter state: {str(e)}")
        return None
def control_gpio_based_on_filter_state():
    """Check the most recent filter state and control GPIO accordingly."""
    filter_state = get_most_recent_filter_state()
    if filter_state == 'ON':
        GPIO.output(FILTER_PIN, GPIO.HIGH)
        print("GPIO pin set to HIGH (Filter ON).")
    elif filter_state == 'OFF':
        GPIO.output(FILTER_PIN, GPIO.LOW)
        print("GPIO pin set to LOW (Filter OFF).")
    else:
        print("Invalid or no filter state found.")
if __name__ == "__main__":
    try:
        control_gpio_based_on_filter_state()
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Cleanup GPIO settings
        GPIO.cleanup()
        try:
            connection.close()
        except sqlite3.Error as e:
            print(f"Error closing the database connection: {str(e)}")
