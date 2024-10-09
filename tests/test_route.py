import unittest
import logging
from app import app  # Import app from app.py
from werkzeug.security import generate_password_hash
from db import create_db_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestRoutes(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

        # Set up a test user in the database
        db = create_db_connection("university")
        cursor = db.cursor()
        hashed_password = generate_password_hash('password', method='pbkdf2:sha256')
        
        try:
            cursor.execute(
                "INSERT INTO users (email, password, role) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE password=%s", 
                ('test@example.com', hashed_password, 'user', hashed_password)
            )
            db.commit()
            logger.info("Test user 'test@example.com' created or updated successfully.")
        except Exception as e:
            logger.error(f"Failed to create test user: {e}")
        finally:
            cursor.close()
            db.close()

    def test_home_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to University', response.data)

    def test_login_route(self):
        response = self.app.post('/login', data=dict(email='test@example.com', password='password'), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Verify OTP', response.data)  # Check for OTP verification page content

if __name__ == '__main__':
    unittest.main()
