import datetime
from flask import Flask, render_template, request, redirect, session, url_for, flash, send_file
import mysql.connector
from mysql.connector import Error
from functools import wraps
from otp_auth import generate_otp, send_otp_via_email
from fpdf import FPDF
import os

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

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash("You must be logged in to access this page.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')

        if not email:
            flash("Email is required!", "danger")
            return redirect(url_for('login'))

        otp = generate_otp()
        session['email'] = email  # Store email in session
        session['otp'] = otp  # Store OTP in session
        session['otp_expiry'] = (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')  # Set OTP expiration
        session['otp_attempts'] = 0  # Initialize OTP attempts

        # Send OTP via email
        if send_otp_via_email(email, otp):
            flash(f"OTP has been sent to {email}.", "info")
            return redirect(url_for('verify_otp'))  # Redirect to OTP verification page
        else:
            flash("Failed to send OTP. Please try again.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        otp_expiry = session.get('otp_expiry')
        otp_attempts = session.get('otp_attempts', 0)

        # Check if OTP has expired
        if datetime.datetime.now() > datetime.datetime.strptime(otp_expiry, '%Y-%m-%d %H:%M:%S'):
            flash("OTP has expired. Please request a new one.", "danger")
            return redirect(url_for('login'))

        # Check OTP attempts
        if otp_attempts >= 3:
            flash("Maximum attempts exceeded. Please request a new OTP.", "danger")
            return redirect(url_for('login'))

        # Validate OTP
        if entered_otp == session.get('otp'):
            flash("Login successful!", "success")
            session['logged_in'] = True  # Mark the user as logged in
            
            session.pop('otp', None)  # Clear OTP from session
            session.pop('otp_expiry', None)  # Clear OTP expiration
            session.pop('otp_attempts', None)  # Clear OTP attempts

            return redirect(url_for('home'))  # Redirect to homepage
        else:
            session['otp_attempts'] += 1  # Increment attempt counter
            flash(f"Invalid OTP. You have {3 - session['otp_attempts']} attempts left.", "danger")
            return redirect(url_for('verify_otp'))

    return render_template('verify_otp.html')


@app.route('/logout')
@login_required
def logout():
    session.clear()  # Clear the entire session
    flash("You have been logged out.", "success")
    return redirect(url_for('login'))  # Redirect to the login page

@app.route('/')
@login_required
def home():
    return render_template('index.html')

@app.route('/about')
@login_required
def about():
    return render_template('about.html')

@app.route('/notices')
@login_required
def notices():
    return render_template('notices.html')

@app.route('/student-corner')
@login_required
def student_corner():
    return render_template('student-corner.html')

@app.route('/contact')
@login_required
def contact():
    return render_template('contact.html')

@app.route('/admission')
@login_required
def admission():
    return render_template('admission.html')

@app.route('/admission-form')
@login_required
def admission_form():
    return render_template('admission-form.html')

@app.route('/submit-application', methods=['POST'])
@login_required
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

        # Store application details in session for preview
        session['application_data'] = {
            'full_name': full_name,
            'email': email,
            'phone_number': phone_number,
            'board_name': board_name,
            'class_name': class_name,
            'percentage': percentage,
            'additional_details': additional_details
        }

        return redirect(url_for('preview_application'))  # Redirect to preview page

    except Error as e:
        db.rollback()
        flash(f'Error submitting application: {e}', 'danger')
    finally:
        cursor.close()
        db.close()

    return redirect(url_for('admission_form'))

@app.route('/preview-application')
@login_required
def preview_application():
    application_data = session.get('application_data')
    if not application_data:
        flash("No application data found.", "danger")
        return redirect(url_for('admission_form'))

    return render_template('preview_application.html', application_data=application_data)

@app.route('/download-pdf', methods=['POST'])
@login_required
def download_pdf():
    application_data = session.get('application_data')
    if not application_data:
        flash("No application data found.", "danger")
        return redirect(url_for('admission_form'))

    # Create a PDF file
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    for key, value in application_data.items():
        pdf.cell(200, 10, f"{key.replace('_', ' ').title()}: {value}", ln=True)

    # Ensure the 'downloaded' directory exists
    download_folder = 'downloaded'
    os.makedirs(download_folder, exist_ok=True)
    
    pdf_file_path = os.path.join(download_folder, 'application.pdf')
    pdf.output(pdf_file_path)

    # Send the PDF file for download
    return send_file(pdf_file_path, as_attachment=True)

if __name__ == '__main__':
    create_database()  # Ensure the database is created
    create_table()  # Ensure the table is created
    app.run(debug=True)
