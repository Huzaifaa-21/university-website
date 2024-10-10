# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Install netcat and MySQL client
RUN apt-get update && \
    apt-get install -y --no-install-recommends apt-utils && \
    apt-get install -y netcat-openbsd default-mysql-client && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5002

# Define environment variables
ENV FLASK_APP=app.py
ENV PYTHONPATH=/app  

# Copy the start_app.sh script to the working directory
COPY start_app.sh /app/start_app.sh
COPY wait-for-it.sh /app/wait-for-it.sh

# Make the scripts executable
RUN chmod +x /app/start_app.sh /app/wait-for-it.sh

# Run the start_app.sh script
CMD ["./start_app.sh"]
