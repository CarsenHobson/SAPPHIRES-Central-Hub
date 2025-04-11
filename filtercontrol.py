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
GPIO_PIN = 18
STATE_FILE = "/home/ZeroWcontrol/gpio_state.txt"  # File to store last known GPIO state

def save_state(state):
    """Save the last GPIO state to a file."""
    with open(STATE_FILE, "w") as f:
        f.write(state)

def load_state():
    """Load the last GPIO state from a file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return f.read().strip()
    return "OFF"  # Default to OFF if file does not exist
    
last_message = load_state()

def on_connect(client, userdata, flags, reason_code, properties):
    try:
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
                GPIO.output(GPIO_PIN, GPIO.HIGH)
                print("GPIO 18 turned ON")
            elif new_message == "OFF":
                GPIO.output(GPIO_PIN, GPIO.LOW)
                print("GPIO 18 turned OFF")
            else:
                print(f"Unknown message received: {new_message}")

            # Save state to remain across reboots
            save_state(new_message)
            last_message = new_message
        except RuntimeError as e:
            print(f"GPIO operation failed: {e}")
    else:
        print("No change in message, GPIO pin state remains unchanged")

if __name__ == "__main__":
    try:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(GPIO_PIN, GPIO.OUT)

        # Restore GPIO state from previous execution
        if last_message == "ON":
            GPIO.output(GPIO_PIN, GPIO.HIGH)
        else:
            GPIO.output(GPIO_PIN, GPIO.LOW)

        print(f"Restored GPIO state: {last_message}")

    except RuntimeError as e:
        print(f"Failed to initialize GPIO: {e}")
        sys.exit(1)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print(f"MQTT connection error: {e}")
        sys.exit(1)

    try:
        client.loop_start()
        time.sleep(59)
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error during MQTT loop or sleep: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
       
