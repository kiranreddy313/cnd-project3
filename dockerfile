# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Set the environment variable for Python to avoid buffering output
ENV PYTHONUNBUFFERED=1

# Expose the port that the app will run on (Cloud Run expects your app to listen on this port)
EXPOSE 8080

# Set the default command to run your app (Cloud Run uses the $PORT environment variable)
CMD ["python", "project1.py"]
