import datetime
import os
from flask import Flask, render_template, request, redirect, session, url_for, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from fpdf import FPDF
from db import create_db_connection, create_database, create_table, get_user_from_db  # Ensure get_user_from_db is defined in db.py
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
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # Clear previous session error messages
        session.pop('email_error', None)
        session.pop('password_error', None)

        if not email or not password:
            session['email_error'] = "Email and password are required!"
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
                    # Store user role and other details in the session
                    otp = generate_otp()
                    session['email'] = email
                    session['logged_in'] = True
                    session['user_id'] = user['id']
                    session['role'] = user['role']  # Store user role in session
                    session['otp'] = otp  # Store OTP in session
                    session['otp_expiry'] = (datetime.datetime.now() + datetime.timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M:%S')  # Set OTP expiration
                    session['otp_attempts'] = 0  # Initialize OTP attempts

                    # Check if the user is an admin or a student and redirect accordingly
                    if user['role'] == 'admin':
                        if send_otp_via_email(email, otp):
                            flash(f"OTP has been sent to {email}.", "info")
                            return redirect(url_for('verify_otp'))  # Redirect to OTP verification page
                        else:
                            flash("Failed to send OTP. Please try again.", "danger")
                            return redirect(url_for('login'))
                    else:
                        flash(f"Welcome, {email}!", "success")
                        if send_otp_via_email(email, otp):
                            flash(f"OTP has been sent to {email}.", "info")
                            return redirect(url_for('verify_otp'))  # Redirect to OTP verification page
                        else:
                            flash("Failed to send OTP. Please try again.", "danger")
                            return redirect(url_for('login'))
                else:
                    session['password_error'] = "Incorrect password!"
            else:
                flash("You are not an existing user. Redirecting to the user creation page.", "info")
                return redirect(url_for('create_user'))

        except Exception as e:
            session['email_error'] = f"An error occurred: {e}"
        finally:
            cursor.close()
            db.close()

    return render_template('login.html')

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    if session.get('role') != 'admin':
        flash("You do not have access to this page.", "danger")
        return redirect(url_for('home'))

    db = create_db_connection("university")
    cursor = db.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM admission_applications")
        students = cursor.fetchall()  # Get all students' details

    except Exception as e:
        flash(f"An error occurred: {e}", "danger")
        students = []

    finally:
        cursor.close()
        db.close()

    return render_template('admin_dashboard.html', students=students)

@app.route('/create_user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role', 'student')  # Default role is 'student'

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

        # Insert new user into the database with hashed password and role
        cursor.execute("INSERT INTO users (email, password, role) VALUES (%s, %s, %s)", (email, hashed_password, role))
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
        if otp_expiry and datetime.datetime.now() > datetime.datetime.strptime(otp_expiry, '%Y-%m-%d %H:%M:%S'):
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

def get_current_user():
    user_id = session.get('user_id')  # Assuming user ID is stored in session
    print(f"User ID in session: {user_id}")
    if user_id:
        # Retrieve user from the database using user_id
        return get_user_from_db(user_id)  # Make sure this function is defined and works correctly
    return None

@app.route('/')
@login_required
def home():
    user = get_current_user()  # Replace this with your actual user retrieval logic
    is_admin = user['role'] == 'admin' if user else False  # Ensure user is not None
    print(f"User: {user}, Is Admin: {is_admin}")
    return render_template('index.html', is_admin=is_admin)

@app.route('/about')
@login_required
def about():
    user = get_current_user()
    is_admin = user['role'] == 'admin' if user else False
    return render_template('about.html', is_admin=is_admin)

@app.route('/notices')
@login_required
def notices():
    user = get_current_user()
    is_admin = user['role'] == 'admin' if user else False
    return render_template('notices.html', is_admin=is_admin)

@app.route('/student-corner')
@login_required
def student_corner():
    user = get_current_user()
    is_admin = user['role'] == 'admin' if user else False
    return render_template('student-corner.html', is_admin=is_admin)

@app.route('/contact')
@login_required
def contact():
    user = get_current_user()
    is_admin = user['role'] == 'admin' if user else False
    return render_template('contact.html', is_admin=is_admin)

@app.route('/admission')
@login_required
def admission():
    user = get_current_user()
    is_admin = user['role'] == 'admin' if user else False
    return render_template('admission.html', is_admin=is_admin)

@app.route('/admission-form')
@login_required
def admission_form():
    return render_template('admission-form.html')

@app.route('/admission-preview')
@login_required
def admission_preview():
    user = get_current_user()
    is_admin = user['role'] == 'admin' if user else False
    application_data = session.get('application_data')
    return render_template('preview_application.html', application_data=application_data, is_admin=is_admin)

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
        percentage_float = float(percentage)
        if not (0 <= percentage_float <= 100):
            raise ValueError("Percentage must be between 0 and 100.")
    except ValueError as ve:
        flash(f'Invalid percentage: {ve}', 'danger')
        return render_template('admission-form.html', 
                               full_name=full_name, 
                               email=email, 
                               phone_number=phone_number, 
                               board_name=board_name, 
                               class_name=class_name, 
                               percentage=percentage, 
                               additional_details=additional_details)

    # Save application data in the session for preview
    session['application_data'] = {
        'full_name': full_name,
        'email': email,
        'phone_number': phone_number,
        'board_name': board_name,
        'class_name': class_name,
        'percentage': percentage_float,
        'additional_details': additional_details
    }

    return redirect(url_for('admission_preview'))

@app.route('/download-receipt')
@login_required
def download_receipt():
    application_data = session.get('application_data')
    
    if not application_data:
        flash("No application data found!", "danger")
        return redirect(url_for('admission'))

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Add content to PDF
    pdf.cell(200, 10, txt="Admission Application Receipt", ln=True, align='C')
    pdf.cell(200, 10, txt=f"Full Name: {application_data['full_name']}", ln=True)
    pdf.cell(200, 10, txt=f"Email: {application_data['email']}", ln=True)
    pdf.cell(200, 10, txt=f"Phone Number: {application_data['phone_number']}", ln=True)
    pdf.cell(200, 10, txt=f"Board Name: {application_data['board_name']}", ln=True)
    pdf.cell(200, 10, txt=f"Class Name: {application_data['class_name']}", ln=True)
    pdf.cell(200, 10, txt=f"Percentage: {application_data['percentage']:.2f}%", ln=True)
    pdf.cell(200, 10, txt=f"Additional Details: {application_data['additional_details']}", ln=True)

    # Save PDF to a temporary file
    pdf_file_path = os.path.join('downloaded', f'receipt_{application_data["full_name"].replace(" ", "_")}.pdf')
    pdf.output(pdf_file_path)

    return send_file(pdf_file_path, as_attachment=True)

if __name__ == '__main__':
    create_database()  # Make sure the database is created at startup
    create_table()     # Ensure the required tables are created
    app.run(debug=True)
