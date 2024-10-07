from flask import Blueprint, render_template
from db import get_student_by_id_from_db
import os
import base64

def student_details_by_id(student_id):
    student = get_student_by_id_from_db(student_id)
    if student:
        print(f"Fetching details : {student}")
        photo_filename = student['photo'].decode('utf-8')
        if photo_filename:  # Ensure the filename is not empty
            photo_path = os.path.join('static', 'photos', photo_filename)
            if os.path.isfile(photo_path):  # Check if it's a file
                with open(photo_path, 'rb') as photo_file:
                    student['photo'] = base64.b64encode(photo_file.read()).decode('utf-8')
            else:
                print(f"Photo file does not exist: {photo_path}")
        else:
            print("No photo filename provided.")
        return student
    else:
        return "Student not found", 404


