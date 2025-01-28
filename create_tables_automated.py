import sqlite3
import logging

DB_PATH = '/home/mainhubs/SAPPHIRESautomated.db'  # Adjust path as needed

def get_db_connection():
    """Safely returns a connection to the SQLite DB or logs an error."""
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except sqlite3.Error as e:
        logging.error(f"Error connecting to database at {DB_PATH}: {e}")
        return None

def create_tables():
    """
    Create the necessary tables if they do not exist.
    Ensures the environment is ready for data storage.
    """
    create_tables_script = """
    CREATE TABLE IF NOT EXISTS Indoor (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        pm25 REAL,
        temperature REAL,
        humidity REAL
    );

    CREATE TABLE IF NOT EXISTS baseline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        baseline_value REAL
    );

    CREATE TABLE IF NOT EXISTS user_control (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        user_input TEXT
    );

    CREATE TABLE IF NOT EXISTS filter_state (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        filter_state TEXT
    );

    CREATE TABLE IF NOT EXISTS Outdoor (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        pm25 REAL,
        temperature REAL,
        humidity REAL,
        wifi_strength REAL
    );
    """
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            logging.error("create_tables: Cannot proceed (no DB connection).")
            return
        cursor = conn.cursor()
        cursor.executescript(create_tables_script)
        conn.commit()
        logging.info("Tables created or verified successfully.")
    except sqlite3.Error as e:
        logging.error(f"Error creating tables: {e}")
    except Exception as ex:
        logging.exception(f"Unexpected error in create_tables: {ex}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    try:
        create_tables()
    except Exception as e:
        logging.error(f"Error executing code: {e}")
