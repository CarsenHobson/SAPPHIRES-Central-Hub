import paho.mqtt.client as mqtt
import os
import sys
import time
import RPi.GPIO as GPIO

# MQTT settings
MQTT_BROKER = "10.42.0.1"
MQTT_PORT = 1883
MQTT_TOPIC = "Filter"

# GPIO settings
GPIO_PIN = 1

# Variable to track the last message received
last_message = None

def on_connect(client, userdata, flags, reason_code, properties):
    # Check if the reason_code indicates a failed connection
    # For MQTT v5, reason_code is an instance of MQTTReasonCode
    # For MQTT v3.1/3.1.1, it's usually an integer status code
    try:
        # If you’re using MQTT v5 callbacks, reason_code is an MQTTReasonCode object
        # You might do something like: if reason_code != mqtt.CONNACK_ACCEPTED:
        # If you’re using older MQTT versions, reason_code is an int; 0 means success.
        if hasattr(reason_code, 'is_failure') and reason_code.is_failure():
            print(f"Failed to connect: {reason_code}. loop_forever() will retry connection.")
        else:
            client.subscribe(MQTT_TOPIC)
            print("Connected and subscribed to topic")
    except Exception as e:
        print(f"Unexpected error in on_connect: {e}")

def on_message(client, userdata, message):
    global last_message
    try:
        new_message = message.payload.decode()
    except UnicodeDecodeError as e:
        print(f"Failed to decode message payload: {e}")
        return

    if new_message != last_message:
        try:
            if new_message == "ON":
                GPIO.output(GPIO_PIN, GPIO.HIGH)  # Turn GPIO pin 14 ON
                print("GPIO 14 turned ON")
            elif new_message == "OFF":
                GPIO.output(GPIO_PIN, GPIO.LOW)  # Turn GPIO pin 14 OFF
                print("GPIO 14 turned OFF")
            else:
                print(f"Unknown message received: {new_message}")

            last_message = new_message  # Update last message received
        except RuntimeError as e:
            print(f"GPIO operation failed: {e}")
    else:
        print("No change in message, GPIO pin state remains unchanged")

def on_subscribe(client, userdata, mid, reason_code_list, properties):
    try:
        # reason_code_list is a list of reason codes, one for each subscription request
        # For MQTTv5, each entry can be an MQTTSubscribeReasonCode
        if reason_code_list[0].is_failure():
            print(f"Broker rejected subscription: {reason_code_list[0]}")
        else:
            print(f"Broker granted the following QoS: {reason_code_list[0].value}")
    except Exception as e:
        print(f"Error in on_subscribe: {e}")

def on_unsubscribe(client, userdata, mid, reason_code_list, properties):
    try:
        if len(reason_code_list) == 0 or not reason_code_list[0].is_failure():
            print("Unsubscribe succeeded")
        else:
            print(f"Broker replied with failure: {reason_code_list[0]}")
    except Exception as e:
        print(f"Error in on_unsubscribe: {e}")

if __name__ == "__main__":
    try:
        # Setup GPIO in a try/except
        GPIO.setmode(GPIO.BCM)  # Use BCM pin numbering
        GPIO.setup(GPIO_PIN, GPIO.OUT)  # Set pin 14 as an output pin
        GPIO.output(GPIO_PIN, GPIO.LOW)  # Initialize the pin to LOW (OFF)
    except RuntimeError as e:
        print(f"Failed to initialize GPIO: {e}")
        sys.exit(1)  # Exit, since GPIO is critical for this script

    # Instantiate the MQTT client
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_subscribe = on_subscribe
    client.on_unsubscribe = on_unsubscribe

    # Connect to the broker in a try/except
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except ConnectionRefusedError as e:
        print(f"Connection to MQTT broker refused: {e}")
        GPIO.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"MQTT connection error: {e}")
        GPIO.cleanup()
        sys.exit(1)

    try:
        client.loop_start()
        # Wait for messages for 59 seconds
        time.sleep(59)
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error during MQTT loop or sleep: {e}")
    finally:
        # Always stop the loop and disconnect before cleaning up
        client.loop_stop()
        client.disconnect()
        GPIO.cleanup()
