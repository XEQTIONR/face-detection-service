# Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libfontconfig1 \
    libgomp1 \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip, setuptools, and wheel first
RUN pip install --no-cache-dir --upgrade \
    pip==23.2.1 \
    setuptools==68.0.0 \
    wheel==0.41.0

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app.py .

# Set environment variables to avoid OpenCV issues
ENV OPENCV_IO_ENABLE_OPENEXR=1
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "app:app"]