# This image comes with OpenCV and NumPy pre-installed and optimized
FROM gocv/opencv:4.10.0

# Set working directory
WORKDIR /app

# Install only the web-related dependencies
# We skip opencv-python-headless here because it's already in the base image
RUN pip install --no-cache-dir fastapi uvicorn python-multipart

# Copy your application code
COPY app.py .

# Digital Ocean App Platform typically uses port 8080 by default
EXPOSE 8080

# Run the app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]