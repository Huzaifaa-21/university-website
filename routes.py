import datetime
import os
from flask import Flask, render_template, request, redirect, session, url_for, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from fpdf import FPDF
from db import create_db_connection, create_database, create_table
from functools import wraps
from otp_auth import generate_otp, send_otp_via_email

app = Flask(__name__)
app.secret_key = 'your_secret_key'

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
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Clear previous session error messages
        session.pop('email_error', None)
        session.pop('password_error', None)

        if not email:
            session['email_error'] = "Email is required!"
        if not password:
            session['password_error'] = "Password is required!"

        if not email or not password:
            return redirect(url_for('login'))

        db = create_db_connection("university")
        if db is None:
            session['email_error'] = "Database connection error!"
            return redirect(url_for('login'))

        cursor = db.cursor(dictionary=True)

        try:
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if user:
                if check_password_hash(user['password'], password):
                    otp = generate_otp()
                    session['email'] = email
                    session['otp'] = otp
                    session['otp_expiry'] = (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')
                    session['otp_attempts'] = 0

                    if send_otp_via_email(email, otp):
                        flash(f"OTP has been sent to {email}.", "info")
                        return redirect(url_for('verify_otp'))
                    else:
                        session['email_error'] = "Failed to send OTP!"
                else:
                    session['password_error'] = "Incorrect password!"
                    return redirect(url_for('login'))
            else:
                # Notify user they will be redirected to user creation page
                flash("You are not an existing user. Redirecting to the user creation page.", "info")
                return redirect(url_for('create_user'))

        except Exception as e:
            session['email_error'] = f"An error occurred: {e}"
            return redirect(url_for('login'))
        finally:
            cursor.close()
            db.close()

    return render_template('login.html')

@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')  # Add more fields as needed

        if not email or not password:
            flash("All fields are required!", "danger")
            return redirect(url_for('create_user'))

        db = create_db_connection("university")
        cursor = db.cursor()

        # Check if user already exists
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if user:
            flash("User already exists! Please login.", "danger")
            return redirect(url_for('login'))

        # Hash the password before storing it
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Insert new user into the database with hashed password
        cursor.execute("INSERT INTO users (email, password) VALUES (%s, %s)", (email, hashed_password))
        db.commit()

        flash("Account created successfully! You can now log in.", "success")
        return redirect(url_for('login'))

    return render_template('create_user.html')

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

@app.route('/admission-preview')
@login_required
def admission_preview():
    application_data = session.get('application_data')
    return render_template('preview_application.html', application_data=application_data)

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
        return render_template('admission-form.html', 
                               full_name=full_name, 
                               email=email, 
                               phone_number=phone_number, 
                               board_name=board_name, 
                               class_name=class_name, 
                               percentage=percentage, 
                               additional_details=additional_details)

    try:
        # Convert percentage to float and validate
        percentage = float(percentage)
        if percentage < 0 or percentage > 100:
            flash('Percentage must be between 0 and 100.', 'danger')
            return render_template('admission-form.html', 
                                   full_name=full_name, 
                                   email=email, 
                                   phone_number=phone_number, 
                                   board_name=board_name, 
                                   class_name=class_name, 
                                   percentage=percentage, 
                                   additional_details=additional_details)
    except ValueError:
        flash('Invalid percentage value. Please enter a number.', 'danger')
        return render_template('admission-form.html', 
                               full_name=full_name, 
                               email=email, 
                               phone_number=phone_number, 
                               board_name=board_name, 
                               class_name=class_name, 
                               percentage=percentage, 
                               additional_details=additional_details)

    # Database insertion
    db = create_db_connection("university")
    if db is None:
        flash('Could not connect to the database. Please try again later.', 'danger')
        return render_template('admission-form.html', 
                               full_name=full_name, 
                               email=email, 
                               phone_number=phone_number, 
                               board_name=board_name, 
                               class_name=class_name, 
                               percentage=percentage, 
                               additional_details=additional_details)

    cursor = db.cursor()
    sql = """INSERT INTO admission_applications 
             (full_name, email, phone_number, board_name, class_name, percentage, additional_details) 
             VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    data = (full_name, email, phone_number, board_name, class_name, percentage, additional_details)
    try:
        cursor.execute(sql, data)
        db.commit()
        flash('Application submitted successfully!', 'success')
    except Exception as e:
        flash(f'An error occurred: {e}', 'danger')
    finally:
        cursor.close()
        db.close()

    # Store application data in session for later use
    session['application_data'] = {
        'full_name': full_name,
        'email': email,
        'phone_number': phone_number,
        'board_name': board_name,
        'class_name': class_name,
        'percentage': percentage,
        'additional_details': additional_details
    }
    
    print(f"Session Data: {session.get('application_data')}")
    print("Application submitted successfully. Redirecting to preview page.")
    return redirect(url_for('admission_preview'))


@app.route('/generate-pdf')
@login_required
def generate_pdf():
    application_data = session.get('application_data')
    if not application_data:
        flash("No application data found.", "danger")
        return redirect(url_for('admission_form'))

    # Create the "downloaded" directory if it doesn't exist
    if not os.path.exists("downloaded"):
        os.makedirs("downloaded")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add application details to the PDF
    for key, value in application_data.items():
        pdf.cell(200, 10, f"{key}: {value}", ln=True)

    # Save PDF
    pdf_file_path = f"downloaded/{application_data['full_name'].replace(' ', '_')}_application.pdf"
    pdf.output(pdf_file_path)

    # Send the PDF file for download
    return send_file(pdf_file_path, as_attachment=True, download_name=os.path.basename(pdf_file_path))

if __name__ == '__main__':
    create_database()  # Create database if not exists
    create_table()     # Create necessary tables
    app.run(debug=True)
