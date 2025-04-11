import sqlite3
import sys
import datetime  s


db_file = 'SAPPHIRESautomated.db' #Use the appropriate database for the state of the study
#db_file = 'SAPPHRIESmanual.db' 
TABLES = ['Outdoor_One', 'Outdoor_Two', 'Outdoor_Three', 'Outdoor_Four']

def check_filter_state_on_last_60_minutes():
    current_time = datetime.datetime.now()
    time_60_minutes_ago = current_time - datetime.timedelta(minutes=60)
    time_60_minutes_ago_str = time_60_minutes_ago.strftime('%Y-%m-%d %H:%M:%S')

    conn = None
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 1 FROM filter_state
            WHERE filter_state = "ON"
            AND timestamp >= ?
            LIMIT 1
        ''', (time_60_minutes_ago_str,))
        result = cursor.fetchone()

        if result:
            print("Filter state was ON in the last 60 minutes. Exiting the script.")
            sys.exit()

    except sqlite3.Error as e:
        print(f"Database error in check_filter_state_on_last_60_minutes: {str(e)}")
        sys.exit(1)
    finally:
        if conn:
            conn.close()


def get_pm25_values_from_all_tables():
    all_pm25_values = []
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        for table in TABLES:
            try:
                cursor.execute(f'''
                    SELECT pm25 FROM {table} 
                    ORDER BY timestamp DESC 
                    LIMIT 60
                ''')
                rows = cursor.fetchall()
                all_pm25_values.extend(row[0] for row in rows if row[0] is not None)
            except sqlite3.Error as e:
                print(f"Database error while fetching data from table {table}: {str(e)}")
    finally:
        if conn:
            conn.close()

    return all_pm25_values


def check_baseline_value(latest_baseline):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        cursor.execute("SELECT baseline FROM pm25_data ORDER BY timestamp DESC LIMIT 5")
        rows = cursor.fetchall()

        if not rows:
            return latest_baseline

        baseline_values = [row[0] for row in rows]
        average_baseline_values = sum(baseline_values) / len(baseline_values)

        if 1.5 * average_baseline_values < latest_baseline < 7.5:
            return 7.5
        else:
            return latest_baseline

    except sqlite3.Error as e:
        print(f"Database error in check_baseline_value: {str(e)}")
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
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
            INSERT INTO baseline (timestamp, baseline_value)
            VALUES (?, ?)
        ''', (timestamp, average_value))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error in insert_baseline_value: {str(e)}")
    finally:
        if conn:
            conn.close()


def main():
    # Step 1: Check if any filter_state is "ON" in the last 60 minutes, and exit if true
    check_filter_state_on_last_60_minutes()

    # Step 2: Get PM2.5 values from all specified tables
    all_pm25_values = get_pm25_values_from_all_tables()

    # Step 3: Calculate the average of those values
    average_pm25 = calculate_average(all_pm25_values)

    # Step 4: Check if we need to adjust the baseline value before inserting
    baseline = check_baseline_value(average_pm25)

    # Step 5: Insert the (possibly adjusted) baseline value
    insert_baseline_value(baseline)


if __name__ == '__main__':
    main()
