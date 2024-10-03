from flask import Flask, render_template, request, redirect, session, url_for, flash, send_file
from db import create_db_connection, create_database, create_table, get_user_from_db, get_all_students

def admin_dashboard_view():
    # Check if the user has admin access
    if session.get('role') != 'admin':
        flash("You do not have access to this page.", "danger")
        return redirect(url_for('home'))

    # Get all students' details using the defined function
    students = get_all_students()

    # Handle the case where no students are retrieved
    if not students:
        flash("No students found.", "warning")

    return render_template('admin_dashboard.html', students=students)