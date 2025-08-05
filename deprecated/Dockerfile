# Use Python 3.8 slim image
FROM python:3.8-slim

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 5000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Run the application with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"] 