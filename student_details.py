from flask import Blueprint, render_template
from db import get_student_by_id_from_db

def student_details_by_id(student_id):
    student = get_student_by_id_from_db(student_id)  # Fetch student from the database
    if student:
        return student
    else:
        return "Student not found", 404

    