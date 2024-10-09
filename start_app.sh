#!/bin/bash

# Run tests
echo "Running tests..."
pytest tests/

# Check if tests passed
if [ $? -eq 0 ]; then
    echo "All tests passed. Starting the application..."
    # Start the application
    python3 app.py
else
    echo "Tests failed. Application will not start."
    exit 1
fi
