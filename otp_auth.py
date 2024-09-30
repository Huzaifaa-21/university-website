import os
import random
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Function to generate a 6-digit OTP
def generate_otp():
    return str(random.randint(100000, 999999))

# Function to send OTP via email
def send_otp_via_email(receiver_email, otp):
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")
    
    if not sender_email or not sender_password:
        print("Email credentials are missing.")
        return False

    msg = MIMEText(f"Your OTP is: {otp}")
    msg['Subject'] = 'Your OTP Code'
    msg['From'] = sender_email
    msg['To'] = receiver_email
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print(f"OTP sent to {receiver_email}")
        return True
    except Exception as e:
        print(f"Failed to send OTP: {e}")
        return False

# Example usage
if __name__ == "__main__":
    otp = generate_otp()
    receiver = "user_email@example.com"
    if send_otp_via_email(receiver, otp):
        print(f"OTP {otp} has been sent.")