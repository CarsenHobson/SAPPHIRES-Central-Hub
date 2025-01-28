import paho.mqtt.client as mqtt
import time
import sqlite3
from datetime import datetime
import ast

# Define the MQTT broker and topic
broker_address = "10.42.1.1"
topic = "ZeroW2"

data_values = {"pm2.5": 0, "Temperature (F)": 0, "Humidity (%)": 0, "Wifi Strength": 0}

# SQLite setup
db_file = 'SAPPHIRES.db'

# Function to insert data into the database
def insert_data(pm25_value, temperature, humidity, wifi_strength):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Get the current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Insert the PM2.5 value into the database
        cursor.execute(
            '''
            INSERT INTO Outdoor (timestamp, pm25_value, temperature, humidity, wifi_strength)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (timestamp, pm25_value, temperature, humidity, wifi_strength)
        )
        
        conn.commit()
    except sqlite3.Error as e:
        # Catch any SQLite errors such as missing table, disk I/O issues, etc.
        print(f"SQLite Error: {e}")
    finally:
        # Ensure the connection is closed even if an error occurs
        if 'conn' in locals():
            conn.close()

# Callback function to handle incoming messages
def on_message(client, userdata, message):
    global data_values
    payload = message.payload.decode("utf-8").strip()
    print(f"Received message: '{payload}'")

    # First, parse the payload safely
    try:
        payload_dict = ast.literal_eval(payload)
    except (ValueError, SyntaxError) as parse_err:
        # This handles the case where payload is not valid Python literal syntax
        print(f"Error parsing payload: {parse_err}")
        return  # Exit the function so we don't attempt to use `payload_dict`

    # Extract data from payload_dict with some checks
    try:
        # Use .get() to safely access dictionary keys without raising KeyError
        if "PM2.5" in payload_dict:
            data_values["pm2.5"] = float(payload_dict["PM2.5"])
        if "Temperature (F)" in payload_dict:
            data_values["temperature"] = float(payload_dict["Temperature (F)"])
        if "Humidity (%)" in payload_dict:
            data_values["humidity"] = float(payload_dict["Humidity (%)"])
        if "Wifi Strength" in payload_dict:
            data_values["Wifi Strength"] = float(payload_dict["Wifi Strength"])
    except ValueError as val_err:
        # This handles the case where the numeric conversion via float() fails
        print(f"Received non-numeric data where a number was expected: {val_err}")
        return

    # Now attempt to insert into the database
    try:
        insert_data(
            data_values["pm2.5"],
            data_values["temperature"],
            data_values["humidity"],
            data_values["Wifi Strength"],
        )
    except Exception as db_err:
        # Catch any other unexpected error from insert_data
        print(f"Unexpected error while inserting data: {db_err}")

# Callback function to confirm subscription
def on_subscribe(client, userdata, mid, granted_qos):
    print(f"Subscribed to topic with QoS {granted_qos[0]}")

# Check if the current hour is 6 AM
current_hour = datetime.now().hour
if current_hour != 6:
    # Setup the MQTT client
    client = mqtt.Client()

    # Attach callback functions
    client.on_message = on_message
    client.on_subscribe = on_subscribe

    # Connect to the broker, handling potential errors
    try:
        client.connect(broker_address)
    except Exception as e:
        print(f"Error connecting to broker '{broker_address}': {e}")
        # Optionally, you could return or exit here if connection fails
        exit(1)

    # Subscribe to the topic safely
    try:
        client.subscribe(topic)
    except Exception as e:
        print(f"Error subscribing to topic '{topic}': {e}")
        # Optionally handle subscription errors here as needed

    # Start the MQTT loop (use loop_forever to ensure it runs continuously)
    client.loop_start()

    time.sleep(59)

    client.loop_stop()
else:
    print("Script is not running because it is 6 AM.")
