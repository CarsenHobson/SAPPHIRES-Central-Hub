import paho.mqtt.client as mqtt
import time
import sqlite3
from datetime import datetime
import ast

# Define the MQTT broker and topic
LOCAL_MQTT_BROKER = "10.42.0.1"
LOCAL_MQTT_PORT = 1883
LOCAL_MQTT_TOPICS = ["ZeroW1", "ZeroW2", "ZeroW3", "ZeroW4"]

data_values = {"pm2.5": 0, "Temperature (F)": 0, "Humidity (%)": 0, "Wifi Strength": 0}

# SQLite setup
db_file = 'SAPPHIRESautomated.db' #Choose the right data base needed for stage of stud
#db_file = 'SAPPHIRESmanual.db'

# Function to insert data into the database
def insert_data(table_name, pm25_value, temperature, humidity, wifi_strength):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Get the current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Insert the data into the corresponding table
        query = f'''
            INSERT INTO {table_name} (timestamp, pm25, temperature, humidity, wifi_strength)
            VALUES (?, ?, ?, ?, ?)
        '''
        cursor.execute(query, (timestamp, pm25_value, temperature, humidity, wifi_strength))

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
    print(f"Received message from {message.topic}: '{payload}'")

    # Determine the table name based on the topic
    topic_to_table = {
        "ZeroW1": "Outdoor_One",
        "ZeroW2": "Outdoor_Two",
        "ZeroW3": "Outdoor_Three",
        "ZeroW4": "Outdoor_Four",
    }
    table_name = topic_to_table.get(message.topic)
    if not table_name:
        print(f"Unknown topic '{message.topic}'")
        return

    # First, parse the payload safely
    try:
        payload_dict = ast.literal_eval(payload)
    except (ValueError, SyntaxError) as parse_err:
        print(f"Error parsing payload: {parse_err}")
        return

    # Extract data from payload_dict with some checks
    try:
        data_values["pm2.5"] = float(payload_dict.get("PM2.5", 0))
        data_values["temperature"] = float(payload_dict.get("Temperature (F)", 0))
        data_values["humidity"] = float(payload_dict.get("Humidity (%)", 0))
        data_values["Wifi Strength"] = float(payload_dict.get("Wifi Strength", 0))
    except ValueError as val_err:
        print(f"Received non-numeric data where a number was expected: {val_err}")
        return

    # Insert the data into the appropriate table
    try:
        insert_data(
            table_name,
            data_values["pm2.5"],
            data_values["temperature"],
            data_values["humidity"],
            data_values["Wifi Strength"],
        )
    except Exception as db_err:
        print(f"Unexpected error while inserting data: {db_err}")


# Callback function to confirm subscription
def on_subscribe(client, userdata, mid, granted_qos):
    print(f"Subscribed to topic with QoS {granted_qos[0]}")


# Setup the MQTT client
client = mqtt.Client()

# Attach callback functions
client.on_message = on_message
client.on_subscribe = on_subscribe

# Connect to the broker, handling potential errors
try:
    client.connect(LOCAL_MQTT_BROKER, LOCAL_MQTT_PORT)
except Exception as e:
    print(f"Error connecting to broker '{LOCAL_MQTT_BROKER}': {e}")
    exit(1)

# Subscribe to the topics
for topic in LOCAL_MQTT_TOPICS:
    try:
        client.subscribe(topic)
    except Exception as e:
        print(f"Error subscribing to topic '{topic}': {e}")

# Start the MQTT loop for 59 seconds
start_time = time.time()
run_duration = 59  # Duration in seconds

# Run the loop for the specified duration
while time.time() - start_time < run_duration:
    client.loop(timeout=1.0)  # Process MQTT messages with a 1-second timeout

# Stop the client after the duration ends
client.disconnect()
print("Stopped MQTT client after 59 seconds.")
