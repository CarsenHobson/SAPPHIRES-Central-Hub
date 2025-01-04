import sqlite3
import sys
import datetime  # For timestamp calculations

# Database file path
db_file = 'pm25_data.db'  # Replace with your actual database file path

def check_filter_state_on_last_60_minutes():
    # Get the current time and calculate the time 60 minutes ago
    current_time = datetime.datetime.now()
    time_60_minutes_ago = current_time - datetime.timedelta(minutes=60)

    # Format the timestamps to match the format in the database (assuming they are stored as TEXT)
    time_60_minutes_ago_str = time_60_minutes_ago.strftime('%Y-%m-%d %H:%M:%S')

    conn = None
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Check if any 'filter_state' value is set to 'ON' within the last 60 minutes
        cursor.execute('''
            SELECT 1 FROM filter_state
            WHERE filter_state = "ON"
            AND timestamp >= ?
            LIMIT 1
        ''', (time_60_minutes_ago_str,))
        result = cursor.fetchone()

        # If result is not None, that means at least one entry with filter_state "ON" exists in the last 60 minutes
        if result:
            print("Filter state was ON in the last 60 minutes. Exiting the script.")
            sys.exit()

    except sqlite3.Error as e:
        print(f"Database error in check_filter_state_on_last_60_minutes: {str(e)}")
        # Decide if you want to exit or continue
        sys.exit(1)
    finally:
        if conn:
            conn.close()

def get_last_60_pm25_values():
    conn = None
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Fetch the last 60 PM2.5 values (sorted by timestamp in descending order)
        cursor.execute('''
            SELECT pm25_value FROM pm25_data
            ORDER BY timestamp DESC
            LIMIT 60
        ''')
        results = cursor.fetchall()
        # Return a list of the PM2.5 values (ignoring the SQL tuples)
        return [row[0] for row in results]

    except sqlite3.Error as e:
        print(f"Database error in get_last_60_pm25_values: {str(e)}")
        # Return an empty list if there's an error
        return []
    finally:
        if conn:
            conn.close()

def check_baseline_value(latest_baseline):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Get the last 5 baseline values
        cursor.execute("SELECT baseline FROM pm25_data ORDER BY timestamp DESC LIMIT 5")
        rows = cursor.fetchall()
        
        if not rows:
            # If there are no rows, return the latest_baseline or a default
            return latest_baseline
        
        baseline_values = [row[0] for row in rows]
        average_baseline_values = sum(baseline_values) / len(baseline_values)

        # Check the condition for the baseline
        if 1.5 * average_baseline_values < latest_baseline < 7.5:
            return 7.5
        else:
            return latest_baseline

    except sqlite3.Error as e:
        print(f"Database error in check_baseline_value: {str(e)}")
        # Return a default in case of a database error
        return 7.5
    finally:
        if conn:
            conn.close()

def calculate_average(values):
    if not values:
        return 0.0
    return sum(values) / len(values)

def insert_baseline_value(average_value):
    conn = None
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Insert the average value into the baseline table with the current timestamp
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO baseline (timestamp, baseline_value)
            VALUES (?, ?)
        ''', (timestamp, average_value))

        # Commit the changes
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in insert_baseline_value: {str(e)}")
    finally:
        if conn:
            conn.close()

def main():
    # Step 1: Check if any filter_state is "ON" in the last 60 minutes, and exit if true
    check_filter_state_on_last_60_minutes()

    # Step 2: Get the last 60 PM2.5 values
    pm25_values = get_last_60_pm25_values()

    # Step 3: Calculate the average of those values
    average_pm25 = calculate_average(pm25_values)

    # Step 4: Check if we need to adjust the baseline value before inserting
    baseline = check_baseline_value(average_pm25)

    # Step 5: Insert the (possibly adjusted) baseline value
    insert_baseline_value(baseline)

if __name__ == '__main__':
    main()
