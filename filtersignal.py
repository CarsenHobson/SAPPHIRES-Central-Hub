import time
import sqlite3
import logging
import paho.mqtt.client as mqtt

DB_PATH = '/home/Mainhub/SAPPHIRESautomated.db'
BROKER_ADDRESS = "10.42.0.1"
MQTT_TOPIC = "Filter"
RUN_DURATION = 59  

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)

def get_db_connection():
    
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
            
            return result  
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
    """
    Main routine that:
      - Connects to MQTT broker
      - Loops for RUN_DURATION seconds, checking and publishing filter state
    """
    
    client = mqtt.Client()
    client.on_publish = on_publish

 
    try:
        client.connect(BROKER_ADDRESS, 1883, 60)
        logging.info(f"Connected to MQTT broker at {BROKER_ADDRESS}")
    except Exception as e:
        logging.error(f"Failed to connect to the MQTT broker: {e}")
        return

    start_time = time.time()

    
    while (time.time() - start_time) < RUN_DURATION:
        try:
            last_id, last_filter_value = get_last_filter_state()
            logging.info(f"Last filter state: id={last_id}, state={last_filter_value}")

            # Publish only if the state is ON
            if last_filter_value.upper() == 'ON':
                client.publish(MQTT_TOPIC, "ON", qos=1)
                logging.info(f"Publishing 'ON' to topic '{MQTT_TOPIC}'")
            else:
                client.publish(MQTT_TOPIC, "OFF", qos=1)
                logging.info("Filter state is not ON; Published OFF")
                
        except Exception as e:
            logging.error(f"An error occurred while processing filter state: {e}")

        
        time.sleep(1)

   
    client.disconnect()
    logging.info("Finished the 59-second loop and disconnected from MQTT broker.")

if __name__ == "__main__":
    main()
