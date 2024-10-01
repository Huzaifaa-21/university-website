# db.py
import mysql.connector
from mysql.connector import Error

def create_db_connection(database=None):
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            port=3306,  # Use the correct port (3308 as per your earlier context)
            password="Lko@6388895330",
            database=database
        )
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def create_database():
    connection = create_db_connection()
    if connection is None:
        print("Failed to create a database connection.")
        return

    try:
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS university")
        connection.commit()
        print("Database 'university' checked/created.")
    except Error as e:
        print(f"Error creating database: {e}")
    finally:
        cursor.close()
        connection.close()

def create_table():
    db = create_db_connection("university")
    if db is None:
        print("Failed to connect to the 'university' database.")
        return

    try:
        cursor = db.cursor()
        create_table_query = """
        CREATE TABLE IF NOT EXISTS admission_applications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            phone_number VARCHAR(50) NOT NULL,
            board_name VARCHAR(255) NOT NULL,
            class_name VARCHAR(50) NOT NULL,
            percentage FLOAT NOT NULL,
            additional_details TEXT
        );
        """
        cursor.execute(create_table_query)
        db.commit()
        print("Table 'admission_applications' checked/created.")
    except Error as e:
        print(f"Error creating table: {e}")
    finally:
        cursor.close()
        db.close()