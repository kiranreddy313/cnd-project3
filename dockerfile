# Use the official Python base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application into the container
COPY . .

# Expose the port that the app runs on
EXPOSE 8080

# Command to run the application
CMD ["python", "project1.py"]
