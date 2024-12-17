import paho.mqtt.client as mqtt
import time
import sqlite3
from datetime import datetime
import ast

# Define the MQTT broker and topic
broker_address = "10.42.1.1"
topic = "ZeroW2"

data_values = {"pm2.5":0, "Temperature (F)":0, "Humidity (%)":0, "Wifi Strength":0}

# SQLite setup
db_file = 'SAPPHIRES.db'

# Function to insert data into the database
def insert_data(pm25_value, temperature, humidity, wifi_strength):
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Get the current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Insert the PM2.5 value into the database
    cursor.execute('''
        INSERT INTO Outdoor (timestamp, pm25_value, temperature, humidity, wifi_strength)
        VALUES (?, ?, ?, ?, ?)
    ''', (timestamp, pm25_value, temperature, humidity, wifi_strength))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

# Callback function to handle incoming messages
def on_message(client, userdata, message):
    global data_values
    payload = message.payload.decode("utf-8").strip()
    print(f"Received message: '{payload}'")
    payload_dict = ast.literal_eval(payload)

    try:
        if "PM2.5" in payload:
            data_values["pm2.5"] = payload_dict["PM2.5"]
        if "Temperature (F)" in payload_dict:
            data_values["temperature"] = payload_dict["Temperature (F)"]
        if "Humidity (%)" in payload_dict:
            data_values["humidity"] = payload_dict["Humidity (%)"]
        if "Wifi Strength" in payload_dict:
            data_values["Wifi Strength"] = payload_dict["Wifi Strength"]
        
        insert_data(data_values["pm2.5"], data_values["temperature"], data_values["humidity"], data_values["Wifi Strength"])

    except ValueError:
        print("Received message is not a valid floating-point number.")

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

    # Connect to the broker
    client.connect(broker_address)

    # Subscribe to the topic
    client.subscribe(topic)

    # Start the MQTT loop (use loop_forever to ensure it runs continuously)
    client.loop_start()

    time.sleep(59)

    client.loop_stop()
else:
    print("Script is not running because it is 6 AM.")
