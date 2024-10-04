from flask import Blueprint, render_template
from db import get_student_by_id_from_db
import os
import base64

def student_details_by_id(student_id):
    student = get_student_by_id_from_db(student_id)  # Fetch student from the database
    if student:
        print(f"Fetching details : {student}")
        photo_path = os.path.join('static', 'photos', student['photo'].decode('utf-8'))  # Decode the bytes object to a string
        if os.path.exists(photo_path):
            with open(photo_path, 'rb') as photo_file:
                student['photo'] = base64.b64encode(photo_file.read()).decode('utf-8')
        return student
    else:
        return "Student not found", 404

    