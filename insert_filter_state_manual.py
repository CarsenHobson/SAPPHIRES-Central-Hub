import sqlite3
import datetime
import logging
from typing import Optional, Tuple

DB_PATH = '/home/Mainhub/SAPPHIRESmanual.db'  # Adjust path if needed

logging.basicConfig(
    filename='insert_filter_state.log',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

def get_db_connection() -> sqlite3.Connection:
    """
    Attempts to open a connection to the SQLite DB.
    Logs and re-raises on error.
    """
    try:
        return sqlite3.connect(DB_PATH, timeout=5)
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        raise

def get_last_state(table_name: str, column_name: str) -> Tuple[Optional[int], str]:
    """
    Returns (id, state_value) of the most recent entry in the specified table and column.
    If none found, returns (None, "OFF").
    """
    query = f'SELECT id, {column_name} FROM {table_name} ORDER BY id DESC LIMIT 1'
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchone()
            if not result:
                logging.info(f"No rows found in {table_name} table; returning OFF as default.")
                return (None, "OFF")
            return result
    except sqlite3.Error as e:
        logging.error(f"Error fetching last_state from {table_name}.{column_name}: {e}")
        return (None, "OFF")
    except Exception as ex:
        logging.exception(f"Unexpected error in get_last_state: {ex}")
        return (None, "OFF")

def insert_filter_state(state: str) -> None:
    """
    Inserts a new row into filter_state with 'ON' or 'OFF' along with a timestamp.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query = 'INSERT INTO filter_state (timestamp, filter_state) VALUES (?, ?)'

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (timestamp, state))
            conn.commit()
            logging.info(f"Inserted filter_state={state} at {timestamp}")
    except sqlite3.Error as e:
        logging.error(f"Error inserting filter_state={state}: {e}")
    except Exception as ex:
        logging.exception(f"Unexpected error in insert_filter_state: {ex}")

if __name__ == '__main__':
    # Retrieve the last user and system states:
    user_id, user_state = get_last_state('user_control', 'user_input')
    system_id, system_state = get_last_state('system_control', 'system_input')

    # Decide which state to insert. You can customize this logic as needed:
    if user_state == 'ON' or system_state == 'ON':
        insert_filter_state('ON')
    else:
        insert_filter_state('OFF')
