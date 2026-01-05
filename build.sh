#!/bin/bash
# Build script for Render - installs FFmpeg, Opus, and Python dependencies

echo "📦 Installing system dependencies..."
apt-get update
apt-get install -y ffmpeg libopus0 libopus-dev

echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Build complete!"
