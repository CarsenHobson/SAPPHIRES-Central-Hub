import time
import sys
from datetime import datetime
import sqlite3

# Constants
DATABASE_FILE_PATH = 'SAPPHIRES.db'
WINDOW_SIZE = 20  # Number of readings to consider

###########################################################
# Database Connection
###########################################################
try:
    connection = sqlite3.connect(DATABASE_FILE_PATH)
    cursor = connection.cursor()
except sqlite3.Error as e:
    print(f"Error connecting to database: {str(e)}")
    sys.exit(1)

###########################################################
# Create Tables (If Not Exists)
###########################################################
try:
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_control (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            filter_state TEXT
        )
    ''')
    # Commit immediately after successful DDL
    connection.commit()
except sqlite3.Error as e:
    print(f"Error creating table 'system_control': {str(e)}")
    # If creation of table fails, we can't proceed
    sys.exit(1)

###########################################################
# Data Storage
###########################################################
pm25_values = []
timestamp_values = []
current_relay_state = 'OFF'  # Default value if no previous state is found

###########################################################
# Helper Functions
###########################################################
def fetch_last_20_rows_columns():
    """
    Fetch the last 20 rows of PM2.5 and timestamp from the database.
    Updates the pm25_values and timestamp_values lists.
    """
    global pm25_values, timestamp_values
    pm25_values.clear()
    timestamp_values.clear()

    try:
        cursor.execute("SELECT pm25_value, timestamp FROM pm25_data ORDER BY rowid DESC LIMIT 20")
        rows = cursor.fetchall()
        
        for pm25_value, timestamp_str in rows:
            # Handle None or invalid data
            if pm25_value is None:
                print("Warning: Found a PM2.5 value of None. Skipping this row.")
                continue
            
            try:
                # Convert timestamp string (YYYY-MM-DD HH:MM:SS) to UNIX time
                timestamp_unix = time.mktime(datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").timetuple())
            except (ValueError, TypeError) as e:
                print(f"Warning: Error converting timestamp '{timestamp_str}' to UNIX time: {str(e)}")
                continue
            
            pm25_values.append(pm25_value)
            timestamp_values.append(timestamp_unix)

    except sqlite3.Error as e:
        print(f"Database error while fetching the last 20 rows: {str(e)}")
        # Potentially add logging or re-raise the exception if needed

def read_baseline_value():
    """Read the baseline PM2.5 value from the database, defaulting to 7.5 on error."""
    try:
        cursor.execute("SELECT baseline FROM pm25_data ORDER BY timestamp DESC LIMIT 1")
        rows = cursor.fetchall()
        
        if rows:
            baseline_val = rows[0][0]
            if baseline_val is None:
                print("Warning: Baseline value is None in the database. Using default of 7.5.")
                return 7.5

            # Ensure we can cast the baseline to float
            try:
                return float(baseline_val)
            except ValueError:
                print(f"Warning: Baseline value '{baseline_val}' is not numeric. Using default of 7.5.")
                return 7.5
        else:
            print("Warning: No baseline record found. Using default of 7.5.")
            return 7.5

    except sqlite3.Error as e:
        print(f"Database error while reading baseline value: {str(e)}")
        return 7.5

def get_last_relay_state():
    """Fetch the most recent relay state from the filter_state table, defaulting to 'OFF' on error."""
    try:
        cursor.execute("SELECT filter_state FROM filter_state ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        if result:
            return result[0]  # 'ON' or 'OFF'
        else:
            return 'OFF'
    except sqlite3.Error as e:
        print(f"Error fetching the most recent relay state: {str(e)}")
        return 'OFF'

def check_rising_edge():
    """
    Check for a rising edge in PM2.5 levels and update the filter state
    if threshold conditions are met.
    """
    global current_relay_state

    baseline_pm25 = read_baseline_value()

    current_time = time.time()
    one_hour_ago = current_time - 3600
    fetch_last_20_rows_columns()

    # Only proceed if we have enough data points within the last hour
    if len(pm25_values) >= WINDOW_SIZE and all(t >= one_hour_ago for t in timestamp_values):
        threshold = 1.25
        if (current_relay_state == 'OFF' 
                and all(val > threshold * baseline_pm25 for val in pm25_values)):
            current_relay_state = 'ON'
            print("PM2.5 is above threshold. Relay turned ON.")
        elif (current_relay_state == 'ON' 
              and all(val <= baseline_pm25 for val in pm25_values)):
            current_relay_state = 'OFF'
            print("PM2.5 is at or below baseline. Relay turned OFF.")
    else:
        print(f"Not enough data points ({len(pm25_values)} out of {WINDOW_SIZE}) or data too old. Skipping rising edge calculation.")

    # Insert the relay state into filter_state table (with rollback on error)
    try:
        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO filter_state (timestamp, filter_state) 
            VALUES (?, ?)
        ''', (current_time_str, current_relay_state))

        # Commit right after successful insert
        connection.commit()

    except sqlite3.Error as e:
        # Attempt to rollback if commit fails or if insert fails
        print(f"Database error during filter_state update: {str(e)}")
        try:
            connection.rollback()
        except sqlite3.Error as rollback_error:
            print(f"Rollback error: {rollback_error}")

###########################################################
# Main Execution
###########################################################
if __name__ == "__main__":
    try:
        # Fetch the most recent relay state from the database when script starts
        current_relay_state = get_last_relay_state()
        print(f"Initial relay state: {current_relay_state}")
        
        check_rising_edge()

    except Exception as e:
        # Catch-all for any unexpected errors
        print(f"An unexpected error occurred: {str(e)}")
    finally:
        # Always attempt to close the connection properly
        try:
            connection.close()
        except sqlite3.Error as e:
            print(f"Error closing the database connection: {str(e)}")
