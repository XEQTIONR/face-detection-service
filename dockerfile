FROM python:3.10-slim

WORKDIR /app

# Install the essential system libraries for OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app
COPY app.py .

# Standard DigitalOcean Port
EXPOSE 8080

# Explicitly call uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]