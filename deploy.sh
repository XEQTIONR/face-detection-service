#!/bin/bash
set -e

echo "Updating system packages..."
apt-get update
apt-get install -y python3-pip python3-venv ffmpeg
apt-get install -y libglib2.0-0 libsm6 libxext6 libxrender1 libfontconfig1 libgomp1

echo "Setting up Python environment..."
cd /opt/face-detection
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Starting service..."
pkill -f "gunicorn.*app:app" || true
nohup venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 app:app > /var/log/face-detection.log 2>&1 &

echo "Deployment complete!"
