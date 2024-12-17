import paho.mqtt.client as mqtt
import os
import time
import RPi.GPIO as GPIO

# MQTT settings
MQTT_BROKER = "10.42.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "Filter"

# GPIO settings
GPIO_PIN = 14
GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
GPIO.setup(GPIO_PIN, GPIO.OUT)  # Set pin 14 as an output pin
GPIO.output(GPIO_PIN, GPIO.LOW)  # Initialize the pin to LOW (OFF)

# Variable to track the last message received
last_message = None

def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        client.subscribe(MQTT_TOPIC)
        print("Connected and subscribed to topic")

def on_message(client, userdata, message):
    global last_message
    new_message = message.payload.decode()

    if new_message != last_message:
        if new_message == "ON":
            GPIO.output(GPIO_PIN, GPIO.HIGH)  # Turn GPIO pin 14 ON
            print("GPIO 14 turned ON")
        elif new_message == "OFF":
            GPIO.output(GPIO_PIN, GPIO.LOW)  # Turn GPIO pin 14 OFF
            print("GPIO 14 turned OFF")

        last_message = new_message  # Update last message received
    else:
        print("No change in message, GPIO pin state remains unchanged")

def on_subscribe(client, userdata, mid, reason_code_list, properties):
    if reason_code_list[0].is_failure:
        print(f"Broker rejected subscription: {reason_code_list[0]}")
    else:
        print(f"Broker granted the following QoS: {reason_code_list[0].value}")

def on_unsubscribe(client, userdata, mid, reason_code_list, properties):
    if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
        print("Unsubscribe succeeded")
    else:
        print(f"Broker replied with failure: {reason_code_list[0]}")

if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_subscribe = on_subscribe
    client.on_unsubscribe = on_unsubscribe

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_start()

    # Wait for messages for 59 seconds
    time.sleep(59)

    client.loop_stop()
    client.disconnect()

    # Cleanup GPIO setup when the script ends
    GPIO.cleanup()
