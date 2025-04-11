import paho.mqtt.client as mqtt
import time
import sqlite3
from datetime import datetime
import ast


LOCAL_MQTT_BROKER = "10.42.0.1"
LOCAL_MQTT_PORT = 1883
LOCAL_MQTT_TOPICS = ["ZeroW1", "ZeroW2", "ZeroW3", "ZeroW4"]

data_values = {"pm2.5": 0, "Temperature (F)": 0, "Humidity (%)": 0, "Wifi Strength": 0}


db_file = 'SAPPHIRESautomated.db' #Choose the right data base needed for stage of stud
#db_file = 'SAPPHIRESmanual.db'


def insert_data(table_name, pm25_value, temperature, humidity, wifi_strength):
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        
        query = f'''
            INSERT INTO {table_name} (timestamp, pm25, temperature, humidity, wifi_strength)
            VALUES (?, ?, ?, ?, ?)
        '''
        cursor.execute(query, (timestamp, pm25_value, temperature, humidity, wifi_strength))

        conn.commit()
    except sqlite3.Error as e:
       
        print(f"SQLite Error: {e}")
    finally:
        
        if 'conn' in locals():
            conn.close()

def on_connect(client, userdata, flags, reason_code, properties):
    try:
        for topic in LOCAL_MQTT_TOPICS:
            client.subscribe(topic)
            print(f"Subscribed to topic: {topic}")
    except Exception as e:
        print(f"Unexpected error in on_connect: {e}")



def on_message(client, userdata, message):
    global data_values
    payload = message.payload.decode("utf-8").strip()
    print(f"Received message: '{payload}'")

    
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

    
    try:
        payload_dict = ast.literal_eval(payload)
    except (ValueError, SyntaxError) as parse_err:
        print(f"Error parsing payload: {parse_err}")
        return

    
    try:
        data_values["pm2.5"] = float(payload_dict.get("PM2.5", 0))
        data_values["temperature"] = float(payload_dict.get("Temperature (F)", 0))
        data_values["humidity"] = float(payload_dict.get("Humidity (%)", 0))
        data_values["Wifi Strength"] = float(payload_dict.get("Wifi Strength", 0))
    except ValueError as val_err:
        print(f"Received non-numeric data where a number was expected: {val_err}")
        return

   
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

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message



try:
    client.connect(LOCAL_MQTT_BROKER, LOCAL_MQTT_PORT)
except Exception as e:
    print(f"Error connecting to broker '{LOCAL_MQTT_BROKER}': {e}")
    exit(1)


for topic in LOCAL_MQTT_TOPICS:
    try:
        client.subscribe(topic)
    except Exception as e:
        print(f"Error subscribing to topic '{topic}': {e}")


start_time = time.time()
run_duration = 59  


while time.time() - start_time < run_duration:
    client.loop(timeout=1.0)  


client.disconnect()
print("Stopped MQTT client after 59 seconds.")
