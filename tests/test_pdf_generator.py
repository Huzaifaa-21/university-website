import unittest
from pdf_generator import generate_pdf
import os

class TestPDFGenerator(unittest.TestCase):

    def test_generate_pdf_with_valid_data(self):
        application_data = {
            'Full Name': 'John Doe',
            'Course': 'Computer Science'
        }
        pdf_path = generate_pdf(application_data)
        self.assertTrue(os.path.exists(pdf_path))
        os.remove(pdf_path)  # Clean up after test

    def test_generate_pdf_with_empty_data(self):
        pdf_path = generate_pdf({})
        self.assertIsNone(pdf_path)

if __name__ == '__main__':
    unittest.main()
