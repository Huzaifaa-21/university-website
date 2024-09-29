from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Database connection
def create_db_connection(database=None):
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            port=3306,
            password="Lko@6388895330",
            database=database
        )
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Function to create the database if it doesn't exist
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

# Function to create the table if it doesn't exist
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

# Creating routes for different pages

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/notices')
def notices():
    return render_template('notices.html')

@app.route('/student-corner')
def student_corner():
    return render_template('student-corner.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/admission')
def admission():
    return render_template('admission.html')

@app.route('/admission-form')
def admission_form():
    return render_template('admission-form.html')

@app.route('/submit-application', methods=['POST'])
def submit_application():
    # Retrieve form data
    full_name = request.form.get('full_name')
    email = request.form.get('email')
    phone_number = request.form.get('phone_number')
    board_name = request.form.get('board_name')
    class_name = request.form.get('class_name')
    percentage = request.form.get('percentage')
    additional_details = request.form.get('additional_details')

    # Input validation
    if not all([full_name, email, phone_number, board_name, class_name, percentage]):
        flash('All fields except "Additional Details" are required.', 'danger')
        return redirect(url_for('admission_form'))

    try:
        # Convert percentage to float and validate
        percentage = float(percentage)
        if percentage < 0 or percentage > 100:
            flash('Percentage must be between 0 and 100.', 'danger')
            return redirect(url_for('admission_form'))
    except ValueError:
        flash('Invalid percentage value. Please enter a number.', 'danger')
        return redirect(url_for('admission_form'))

    # Database insertion
    db = create_db_connection("university")
    if db is None:
        flash('Could not connect to the database. Please try again later.', 'danger')
        return redirect(url_for('admission_form'))

    cursor = db.cursor()
    sql = """INSERT INTO admission_applications 
             (full_name, email, phone_number, board_name, class_name, percentage, additional_details)
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    values = (full_name, email, phone_number, board_name, class_name, percentage, additional_details)
    
    try:
        cursor.execute(sql, values)
        db.commit()
        flash('Application submitted successfully!', 'success')
    except Error as e:
        db.rollback()
        flash(f'Error submitting application: {e}', 'danger')
    finally:
        cursor.close()
        db.close()

    return redirect(url_for('admission_form'))

if __name__ == '__main__':
    # Create database and table before running the app
    create_database()
    create_table()
    app.run(debug=True)