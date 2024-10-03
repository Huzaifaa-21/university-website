# app.py
from routes import app
from db import create_database, create_table
from routes import student_bp, admin_routes  # Import the student blueprint

if __name__ == '__main__':
    
    create_database()  # Ensure database is created
    create_table()     # Ensure table is created
    
    # app.register_blueprint(student_bp)  # Registering the student blueprint
    # app.register_blueprint(admin_routes)  # Registering the admin routes
    
    app.run(debug=True)  # Run the Flask application
