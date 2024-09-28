from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL Database connection
def create_db_connection():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            port=3308,
            password="Huzaifa@21",
            database="university"
        )
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

@app.route('/')
def home():
    return render_template('index.html')

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
    db = create_db_connection()
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
    app.run(debug=True)
