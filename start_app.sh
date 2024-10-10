#!/bin/bash

# Wait for the database to be ready
./wait-for-it.sh db 3306 -- echo "MySQL is up - running tests"

# Run tests
echo "Running tests..."
pytest tests/

# Check if tests passed
if [ $? -eq 0 ]; then
    echo "All tests passed. Starting the application..."
    ./wait-for-it.sh db 3306 -- python3 app.py
else
    echo "Tests failed. Application will not start."
fi