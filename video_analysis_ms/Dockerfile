FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including ffmpeg for audio extraction
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create debug output directory
RUN mkdir -p /app/debug_output

# Expose port
EXPOSE 8001

# Run migrations and start server
CMD python manage.py migrate && \
    python manage.py runserver 0.0.0.0:8001
