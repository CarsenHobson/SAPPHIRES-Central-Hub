import time
from sps30 import SPS30
import sqlite3
import board
from adafruit_bme280 import basic as adafruit_bme280

db_path = '/home/Mainhub/SAPPHIRESautomated.db'
#db_path = '/home/Mainhub/SAPPHIRESmanual.db' #Use this directory if in manual state of study


conn = sqlite3.connect(db_path)


cur = conn.cursor()


sps30 = SPS30(port=1)


i2c = board.I2C()
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

def celsius_to_fahrenheit(celsius):
    return (celsius * 9 / 5) + 32

try:
    
    sps30.read_measured_values()
    pm25 = sps30.dict_values['pm2p5']
    temperature_celsius = bme280.temperature
    temperature_fahrenheit = celsius_to_fahrenheit(temperature_celsius)
    humidity = bme280.humidity
    current_time = time.strftime('%Y-%m-%d %H:%M:%S')

    
    insert_query = '''
    INSERT INTO Indoor (timestamp, pm25, temperature, humidity)
    VALUES (?, ?, ?, ?)
    '''
    cur.execute(insert_query, (current_time, pm25, temperature_fahrenheit, humidity))

   
    conn.commit()

    print(f"Values inserted successfully at {current_time}.")

except KeyboardInterrupt:
    
    sps30.stop_measurement()
    print("\nKeyboard interrupt detected. SPS30 turned off.")

finally:
  
    conn.close()
