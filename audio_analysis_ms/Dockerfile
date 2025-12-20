FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create debug output directory
RUN mkdir -p /app/debug_output

# Expose port
EXPOSE 8004

# Run migrations and start server
CMD python manage.py migrate && \
    python manage.py runserver 0.0.0.0:8004
