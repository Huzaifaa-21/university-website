# pdf_generator.py
import os
from fpdf import FPDF
from flask import send_file

def generate_pdf(application_data):
    if not application_data:
        return None

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
    pdf_file_path = f"downloaded/{application_data['Full Name'].replace(' ', '_')}_application.pdf"
    pdf.output(pdf_file_path)

    return pdf_file_path