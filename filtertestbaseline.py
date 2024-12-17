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

    # Connect to the SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Check if any 'filter_state' value is set to 'ON' within the last 60 minutes in the 'filter_state' table
    cursor.execute('''
        SELECT 1 FROM filter_state 
        WHERE filter_state = "ON" 
        AND timestamp >= ?
        LIMIT 1
    ''', (time_60_minutes_ago_str,))
    result = cursor.fetchone()

    # Close the connection
    conn.close()

    # If result is not None, that means at least one entry with filter_state "ON" exists in the last 60 minutes
    if result:
        print("Filter state was ON in the last 60 minutes. Exiting the script.")
        sys.exit()

def get_last_60_pm25_values():
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

    # Close the connection
    conn.close()

    # Return a list of the PM2.5 values (ignoring the SQL tuples)
    return [row[0] for row in results]

def check_baseline_value(latest_baseline):
    try:
        cursor.execute("SELECT baseline FROM pm25_data ORDER BY timestamp DESC LIMIT 5")
        rows = cursor.fetchall()
        baseline_values = [row[0] for row in rows]
        average_baseline_values = sum(baseline_values) / len(baseline_values) 
        if latest_baseline > 1.5 * average_baseline_values and latest_baseline < 7.5:
           return 7.5
        else:
            return latest_baseline
    except sqlite3.Error as e:
        print(f"Database error: {str(e)}")
        return 7.5  # Default in case of a database error
    
def calculate_average(values):
    if not values:
        return 0.0
    return sum(values) / len(values)

def create_baseline_table():
    # Connect to the SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Create the baseline table if it doesn't already exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS baseline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            baseline_value REAL
        )
    ''')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def insert_baseline_value(average_value):
    # Connect to the SQLite database
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Insert the average value into the baseline table with the current timestamp
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO baseline (timestamp, baseline_value)
        VALUES (?, ?)
    ''', (timestamp, average_value))

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

def main():
    # Step 1: Check if any filter_state is "ON" in the last 60 minutes, and exit if true
    check_filter_state_on_last_60_minutes()

    # Step 2: Get the last 60 PM2.5 values
    pm25_values = get_last_60_pm25_values()

    # Step 3: Calculate the average of those values
    average_pm25 = calculate_average(pm25_values)

    # Step 4: Create the baseline table if it doesn't exist
    create_baseline_table()
    baseline = check_baseline_value(average_pm25)
    # Step 5: Insert the calculated average into the baseline table
    insert_baseline_value(baseline)

if __name__ == '__main__':
    main()
