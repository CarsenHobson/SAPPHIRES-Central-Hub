import time
from sps30 import SPS30
import sqlite3
import board
from adafruit_bme280 import basic as adafruit_bme280
# Database path
db_path = '/home/Mainhub/SAPPHIRESautomated.db'
#db_path = '/home/Mainhub/SAPPHIRESmanual.db'

# Connect to the SQLite database
conn = sqlite3.connect(db_path)

# Create a cursor object
cur = conn.cursor()

# Initialize the SPS30 sensor
sps30 = SPS30(port=1)

#Initialize bme280
i2c = board.I2C()
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

def celsius_to_fahrenheit(celsius):
    return (celsius * 9 / 5) + 32

try:
    # Read measured values from the sensor
    sps30.read_measured_values()
    pm25 = sps30.dict_values['pm2p5']
    temperature_celsius = bme280.temperature
    temperature_fahrenheit = celsius_to_fahrenheit(temperature_celsius)
    humidity = bme280.humidity
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')

    # Insert the pm25 value and timestamp into the database
    insert_query = '''
    INSERT INTO Indoor (timestamp, pm25, temperature, humidity)
    VALUES (?, ?, ?, ?)
    '''
    cur.execute(insert_query, (current_time, pm25, temperature_fahrenheit, humidity))

    # Commit the changes
    conn.commit()

    print(f"Values inserted successfully at {current_time}.")

except KeyboardInterrupt:
    # Stop the sensor measurement if interrupted
    sps30.stop_measurement()
    print("\nKeyboard interrupt detected. SPS30 turned off.")

finally:
    # Close the database connection
    conn.close()
