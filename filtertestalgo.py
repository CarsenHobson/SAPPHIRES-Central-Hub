import time
import sys
from datetime import datetime
import sqlite3

# Constants
DATABASE_FILE_PATH = 'SAPPHIRES.db'
WINDOW_SIZE = 20  # Number of readings to consider

# Database connection
try:
    connection = sqlite3.connect(DATABASE_FILE_PATH)
    cursor = connection.cursor()
except sqlite3.Error as e:
    print(f"Error connecting to database: {str(e)}")
    sys.exit(1)

# Create the filter_state table if it doesn't exist
try:
    cursor.execute('''CREATE TABLE IF NOT EXISTS filter_state (
                      id INTEGER PRIMARY KEY AUTOINCREMENT,
                      timestamp TEXT,
                      filter_state TEXT)''')
    connection.commit()
except sqlite3.Error as e:
    print(f"Error creating table: {str(e)}")
    sys.exit(1)

# Data storage
pm25_values = []
timestamp_values = []
current_relay_state = 'OFF'  # Default value if no previous state is found

def fetch_last_20_rows_columns():
    """Fetch the last 20 rows of PM2.5 and timestamp from the database."""
    global pm25_values, timestamp_values
    pm25_values.clear()
    timestamp_values.clear()

    try:
        cursor.execute("SELECT pm25_value, timestamp FROM pm25_data ORDER BY rowid DESC LIMIT 20")
        rows = cursor.fetchall()
        for pm25_value, timestamp in rows:
            pm25_values.append(pm25_value)
            # Assuming the timestamp is a string in the format 'YYYY-MM-DD HH:MM:SS'
            timestamp_unix = time.mktime(datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").timetuple())
            timestamp_values.append(timestamp_unix)
    except sqlite3.Error as e:
        print(f"Error fetching data from database: {str(e)}")

def read_baseline_value():
    """Read the baseline PM2.5 value from the database."""
    try:
        cursor.execute("SELECT baseline FROM pm25_data ORDER BY timestamp DESC LIMIT 1")
        baseline = cursor.fetchall()
        return baseline       
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
        return 7.5  # Default in case of a database error

def get_last_relay_state():
    """Fetch the most recent relay state from the filter_state table."""
    try:
        cursor.execute("SELECT filter_state FROM filter_state ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        if result:
            return result[0]  # 'ON' or 'OFF'
        else:
            return 'OFF'  # Default to 'OFF' if no entry found
    except sqlite3.Error as e:
        print(f"Error fetching the most recent relay state: {str(e)}")
        return 'OFF'

def check_rising_edge():
    """Check for a rising edge in PM2.5 levels and update the filter state."""
    global current_relay_state

    baseline_pm25 = read_baseline_value()

    current_time = time.time()
    one_hour_ago = current_time - 3600
    fetch_last_20_rows_columns()

    if len(pm25_values) >= WINDOW_SIZE and all(timestamp >= one_hour_ago for timestamp in timestamp_values):
        threshold = 1.25
        if current_relay_state == 'OFF' and all(data_point > threshold * baseline_pm25 for data_point in pm25_values):
            current_relay_state = 'ON'
            print("PM2.5 is above threshold. Relay turned ON.")
        elif current_relay_state == 'ON' and all(data_point <= baseline_pm25 for data_point in pm25_values):
            current_relay_state = 'OFF'
            print("PM2.5 is at or below baseline. Relay turned OFF.")
    else:
        print(f"Not enough data points ({len(pm25_values)} out of {WINDOW_SIZE}). Skipping rising edge calculation.")

    # Insert the relay_state into the filter_state table with the current timestamp
    try:
        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''INSERT INTO filter_state (timestamp, filter_state) 
                          VALUES (?, ?)''', (current_time_str, current_relay_state))
    except sqlite3.Error as e:
        print(f"Error inserting data into filter_state table: {str(e)}")

if __name__ == "__main__":
    try:
        # Fetch the most recent relay state from the database when the script starts
        current_relay_state = get_last_relay_state()
        print(f"Initial relay state: {current_relay_state}")
        
        check_rising_edge()
        connection.commit()
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
    finally:
        try:
            connection.close()
        except sqlite3.Error as e:
            print(f"Error closing the database connection: {str(e)}")
