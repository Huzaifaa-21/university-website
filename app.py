# app.py
from routes import app
from db import create_database, create_table

if __name__ == '__main__':
    create_database()  # Ensure database is created
    create_table()     # Ensure table is created
    app.run(debug=True)  # Run the Flask application
