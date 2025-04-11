import time
import sys
from datetime import datetime
import sqlite3


DATABASE_FILE_PATH = 'SAPPHIRESautomated.db' #Use the appropriate database for the state of the study
#DATABASE_FILE_PATH = 'SAPPHIRESmanual.db'
WINDOW_SIZE = 20  # Number of readings to consider
TABLES = ['Outdoor_One', 'Outdoor_Two', 'Outdoor_Three', 'Outdoor_Four']

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
# Helper Functions
###########################################################
def fetch_last_20_rows_columns(table_name):
    """
    Fetch the last 20 rows of PM2.5 and timestamp from a specified table.
    Returns lists of pm25_values and timestamp_values.
    """
    pm25_values = []
    timestamp_values = []

    try:
        query = f"SELECT pm25, timestamp FROM {table_name} ORDER BY rowid DESC LIMIT 20"
        cursor.execute(query)
        rows = cursor.fetchall()

        for pm25_value, timestamp_str in rows:
            if pm25_value is None:
                continue

            try:
                timestamp_unix = time.mktime(datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S").timetuple())
                pm25_values.append(pm25_value)
                timestamp_values.append(timestamp_unix)
            except (ValueError, TypeError):
                continue

    except sqlite3.Error as e:
        print(f"Database error while fetching data from {table_name}: {str(e)}")

    return pm25_values, timestamp_values


def read_baseline_value():
    """Read the baseline PM2.5 value from the database, defaulting to 7.5 on error."""
    try:
        cursor.execute("SELECT baseline_value FROM baseline ORDER BY timestamp DESC LIMIT 1")
        rows = cursor.fetchall()

        if rows:
            baseline_val = rows[0][0]
            return float(baseline_val) if baseline_val else 7.5
        else:
            return 7.5

    except sqlite3.Error as e:
        print(f"Database error while reading baseline value: {str(e)}")
        return 7.5


def get_last_relay_state():
    """Fetch the most recent relay state from the filter_state table, defaulting to 'OFF' on error."""
    try:
        cursor.execute("SELECT filter_state FROM filter_state ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        return result[0] if result else 'OFF'
    except sqlite3.Error as e:
        print(f"Error fetching the most recent relay state: {str(e)}")
        return 'OFF'


def check_rising_edge(table_name):
    """
    Check for a rising edge in PM2.5 levels for a specific table and update the filter state
    if threshold conditions are met.
    """
    global current_relay_state

    baseline_pm25 = read_baseline_value()
    current_time = time.time()
    one_hour_ago = current_time - 3600

    pm25_values, timestamp_values = fetch_last_20_rows_columns(table_name)

    if len(pm25_values) >= WINDOW_SIZE and all(t >= one_hour_ago for t in timestamp_values):
        threshold = 1.25
        if (current_relay_state == 'OFF'
                and all(val > threshold * baseline_pm25 for val in pm25_values)):
            current_relay_state = 'ON'
            print(f"{table_name}: PM2.5 is above threshold. Relay turned ON.")
        elif (current_relay_state == 'ON'
              and all(val <= baseline_pm25 for val in pm25_values)):
            current_relay_state = 'OFF'
            print(f"{table_name}: PM2.5 is at or below baseline. Relay turned OFF.")
    else:
        print(
            f"{table_name}: Not enough data points ({len(pm25_values)} out of {WINDOW_SIZE}) or data too old. Skipping.")

    insert_relay_state()


def insert_relay_state():
    """Insert the relay state into the filter_state table."""
    try:
        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO system_control (timestamp, system_input) 
            VALUES (?, ?)
        ''', (current_time_str, current_relay_state))
        connection.commit()
    except sqlite3.Error as e:
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
        current_relay_state = get_last_relay_state()
        print(f"Initial filter state: {current_relay_state}")

        # Check rising edge for each table
        for table in TABLES:
            check_rising_edge(table)

    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
    finally:
        try:
            connection.close()
        except sqlite3.Error as e:
            print(f"Error closing the database connection: {str(e)}")
