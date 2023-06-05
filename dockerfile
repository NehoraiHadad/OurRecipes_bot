# Use an official Python runtime as the base image
FROM python:3.11

# Set working directory to /app
WORKDIR /app

# Copy the requirements file and install the dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy all the files in the current directory to the working directory
COPY . .

# Set the entry point for the Lambda function
CMD ["python", "bot.py"]
