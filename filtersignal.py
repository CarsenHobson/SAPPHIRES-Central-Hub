import sqlite3
import logging
import paho.mqtt.client as mqtt

# Constants
DB_PATH = '/home/mainhubs/SAPPHIREStest.db'
MQTT_USERNAME = "SAPPHIRE"
MQTT_PASSWORD = "SAPPHIRE"
BROKER_ADDRESS = "10.42.0.1"
MQTT_TOPIC = "filter_signal"

# Configure logging at the top level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)


def get_db_connection():
    """
    Attempts to open a connection to the SQLite DB.
    Logs and re-raises on error.
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        raise


def get_last_filter_state():
    """
    Returns (id, filter_state) of the most recent entry in filter_state.
    If no rows exist, returns (None, "OFF").
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, filter_state FROM filter_state ORDER BY id DESC LIMIT 1')
            result = cursor.fetchone()

            if not result:
                logging.info("No rows found in filter_state table; returning OFF as default.")
                return (None, "OFF")

            return result  # (id, filter_state)
    except sqlite3.Error as e:
        logging.error(f"Error fetching last_filter_state: {e}")
        return (None, "OFF")
    except Exception as ex:
        logging.exception(f"Unexpected error in get_last_filter_state: {ex}")
        return (None, "OFF")


def on_publish(client, userdata, result):
    """
    Callback for when a message has been published.
    """
    logging.info(f"Message published with result code: {result}")


def main():
    # Set up MQTT client
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_publish = on_publish

    try:
        client.connect(BROKER_ADDRESS, 1883, 60)
        logging.info(f"Connected to MQTT broker at {BROKER_ADDRESS}")
    except Exception as e:
        logging.error(f"Failed to connect to the MQTT broker: {e}")
        return

    try:
        last_id, last_filter_value = get_last_filter_state()
        logging.info(f"Last filter state: id={last_id}, state={last_filter_value}")

        # Publish only if the state is ON
        if last_filter_value.upper() == 'ON':
            ret = client.publish(MQTT_TOPIC, "ON", qos=1)
            logging.info(f"Publishing 'ON' to topic '{MQTT_TOPIC}'. Return code: {ret.rc}")
        else:
            logging.info("Filter state is not ON; no message published.")

    except Exception as e:
        logging.error(f"An error occurred while processing filter state: {e}")


if __name__ == "__main__":
    main()