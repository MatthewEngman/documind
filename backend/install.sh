#!/bin/bash
set -e

echo "Installing Python dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Dependencies installed successfully!"
