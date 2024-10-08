from flask import Blueprint, render_template
from db import get_student_by_id_from_db
import os
import base64

def student_details_by_id(student_id):
    student = get_student_by_id_from_db(student_id)
    if student:
        print(f"Fetching details")
        return student
    else:
        return "Student not found", 404


