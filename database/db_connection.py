import mysql.connector
from mysql.connector import Error

DB_NAME = "personal_info_db"

def get_server_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="1234"
        )
    except Error as e:
        print(f"❌ Cannot connect to MySQL server: {e}")
        return None


def get_connection():
    """Connects to the target database safely."""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="1234",
            database=DB_NAME
        )
        if conn.is_connected():
            return conn
    except Error as e:
        print(f"❌ Database connection failed: {e}")
        return None

def ensure_database_exists():
    """Checks if database exists, and creates it if not."""
    conn = get_server_connection()
    if conn is None:
        return
    cursor = conn.cursor()
    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        print(f"✅ Database check complete — '{DB_NAME}' is ready.")
    except Error as e:
        print(f"❌ Error ensuring database exists: {e}")
    finally:
        cursor.close()
        conn.close()


def ensure_table_exists():
    """Checks if the Persons table exists; creates it if not."""
    conn = get_connection()
    if conn is None:
        return
    cursor = conn.cursor()
    try:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS Persons (
                person_id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                dob DATE,
                gender VARCHAR(20),
                phone VARCHAR(15) UNIQUE,
                email VARCHAR(100) UNIQUE,
                address TEXT
            )
        """)
        conn.commit()
        print("✅ Table check complete — 'Persons' table is ready.")
    except Error as e:
        print(f"❌ Error ensuring table exists: {e}")
    finally:
        cursor.close()
        conn.close()
