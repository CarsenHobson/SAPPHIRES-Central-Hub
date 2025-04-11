import sqlite3
import logging
from datetime import datetime

DB_PATH = '/home/Mainhub/SAPPHIRESautomated.db'  

def insert_system_control():
    """Insert 'ON' into the system_control table with a timestamp."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        timestamp = datetime.utcnow().isoformat()  
        cursor.execute("INSERT INTO system_control (timestamp, system_input) VALUES (?, ?)", (timestamp, "ON"))

        conn.commit()
        logging.info("Inserted 'ON' into system_control table successfully.")
    except sqlite3.Error as e:
        logging.error(f"Error inserting into system_control: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    insert_system_control()
