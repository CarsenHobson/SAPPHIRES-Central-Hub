import sqlite3
import logging

DB_PATH = '/home/mainhubs/SAPPHIRESmanual.db'  # Adjust path as needed

def get_db_connection():
    """
    Attempts to open a connection to the SQLite DB.
    Logs and re-raises on error.
    """
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        raise

def create_tables():
    """
    Create/upgrade tables. If there's an error, we log it.
    """
    create_tables_script = """
    CREATE TABLE IF NOT EXISTS Indoor (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        pm25 REAL,
        temperature REAL,
        humidity REAL
    );
    CREATE TABLE IF NOT EXISTS Outdoor (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        pm25_value REAL,
        temperature REAL,
        humidity REAL,
        wifi_strength REAL
    );
    CREATE TABLE IF NOT EXISTS system_control (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        system_input TEXT CHECK (filter_state IN ('ON', 'OFF'))
    );
    CREATE TABLE IF NOT EXISTS user_control (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        user_input TEXT CHECK (filter_state IN ('ON', 'OFF'))
    );
    CREATE TABLE IF NOT EXISTS filter_state (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        filter_state TEXT CHECK (filter_state IN ('ON','OFF'))
    );
    CREATE TABLE IF NOT EXISTS processed_events (
        processed_id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        processed_timestamp TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS reminders (
        reminder_id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id INTEGER NOT NULL,
        reminder_time TEXT NOT NULL,
        reminder_type TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS baseline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        baseline_value REAL
    );
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.executescript(create_tables_script)
        conn.commit()
        logging.info("Tables created or verified successfully.")
    except sqlite3.Error as e:
        logging.error(f"Error creating tables: {e}")
    except Exception as ex:
        logging.exception(f"Unexpected error creating tables: {ex}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    try:
        create_tables()
    except Exception as e:
        logging.error(f"Error executing code: {e}")
