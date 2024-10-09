import unittest
from unittest.mock import patch, MagicMock
from student_details import student_details_by_id
from db import get_student_by_id_from_db

class TestStudentDetails(unittest.TestCase):

    @patch('student_details.get_student_by_id_from_db')
    def test_student_found(self, mock_get_student):
        # Mock the database response
        mock_get_student.return_value = {
            'id': 1,
            'first_name': 'John',
            'last_name': 'Doe'
        }
        
        student = student_details_by_id(1)
        self.assertEqual(student['first_name'], 'John')
        self.assertEqual(student['last_name'], 'Doe')

    @patch('student_details.get_student_by_id_from_db')
    def test_student_not_found(self, mock_get_student):
        # Mock the database response
        mock_get_student.return_value = None
        
        response, status_code = student_details_by_id(999)
        self.assertEqual(response, "Student not found")
        self.assertEqual(status_code, 404)

    @patch('student_details.get_student_by_id_from_db')
    def test_student_not_found(self, mock_get_student):
        # Mock the database response
        mock_get_student.return_value = None
        
        response, status_code = student_details_by_id(999)
        self.assertEqual(response, "Student not found")
        self.assertEqual(status_code, 404)

    @patch('student_details.get_student_by_id_from_db')
    def test_database_error(self, mock_get_student):
        # Simulate a database error
        mock_get_student.side_effect = Exception("Database error")
        
        with self.assertRaises(Exception) as context:
            student_details_by_id(1)
        
        self.assertTrue("Database error" in str(context.exception))

    @patch('student_details.get_student_by_id_from_db')
    def test_empty_student_id(self, mock_get_student):
        # Test with an empty student ID
        mock_get_student.return_value = None
        
        response, status_code = student_details_by_id('')
        self.assertEqual(response, "Student not found")
        self.assertEqual(status_code, 404)

if __name__ == '__main__':
    unittest.main()
