#!/bin/bash
echo "Installing dependencies..."
pip install -r requirements.txt
echo "Starting application..."
python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
