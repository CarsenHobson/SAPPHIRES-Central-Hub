ximport sqlite3
import random
import datetime
import time

database = 'SAPPHIREStest.db'

# Helper function to create a database connection
def get_db_connection():
    return sqlite3.connect(database, timeout=5)

# Generate random float values within a range
def random_float(low, high, decimals=2):
    return round(random.uniform(low, high), decimals)

def insert_indoor_data(cursor):
    timestamp = datetime.datetime.now()
    pm25 = random_float(0, 150)
    temperature = random_float(60, 85)
    humidity = random_float(30, 60)
    cursor.execute('''
                       INSERT INTO Indoor (timestamp, pm25, temperature, humidity)
                       VALUES (?, ?, ?, ?)
                   ''', (timestamp.strftime("%Y-%m-%d %H:%M:%S"), pm25, temperature, humidity))

def insert_outdoor_data(cursor):
    timestamp = datetime.datetime.now()
    pm25 = random_float(0, 150)
    temperature = random_float(50, 100)
    humidity = random_float(20, 70)
    wifi_strength = random_float(-80, -30, decimals=1)
    cursor.execute('''
                    INSERT INTO Outdoor (timestamp, pm25, temperature, humidity, wifi_strength)
                    VALUES (?, ?, ?, ?, ?)
                ''', (timestamp.strftime("%Y-%m-%d %H:%M:%S"), pm25, temperature, humidity, wifi_strength))

def insert_system_control(cursor):
    timestamp = datetime.datetime.now()
    system_input = 'ON' if timestamp.minute == 30 else 'OFF'
    cursor.execute('''INSERT INTO system_control (timestamp, system_input) VALUES (?, ?)''', 
                   (timestamp.strftime("%Y-%m-%d %H:%M:%S"), system_input))

def insert_baseline_value(cursor):
    baseline = 10
    timestamp = datetime.datetime.now()
    cursor.execute('''
                        INSERT INTO baseline (timestamp, baseline_value)
                        VALUES (?, ?)
                    ''', (timestamp.strftime("%Y-%m-%d %H:%M:%S"), baseline))

if __name__ == '__main__':
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        insert_baseline_value(cursor)
        conn.commit()
        while True:
            insert_indoor_data(cursor)
            insert_outdoor_data(cursor)
            insert_system_control(cursor)
            conn.commit()
            time.sleep(30)
    except KeyboardInterrupt:
        print("Terminating the script.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        if conn:
            conn.close()
