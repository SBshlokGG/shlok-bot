#!/bin/bash
# Build script for Render - installs FFmpeg and Python dependencies

echo "📦 Installing system dependencies..."
apt-get update -qq
apt-get install -y --no-install-recommends ffmpeg libopus0 2>/dev/null

echo "📦 Installing Python dependencies..."
pip install --no-cache-dir -r requirements.txt

echo "✅ Build complete!"
