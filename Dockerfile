# Use an official Python runtime as a parent image
FROM python:3.11

# Install SQLite3 >= 3.35.0
RUN apt-get update && apt-get install -y sqlite3

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy requirements.txt and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Run your app
CMD ["streamlit", "run", "app.py"]
