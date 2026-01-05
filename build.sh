#!/bin/bash
# Build script for Render

echo "📦 Installing dependencies..."
apt-get update -qq
apt-get install -y --no-install-recommends ffmpeg 2>/dev/null || true
pip install --no-cache-dir -r requirements.txt
echo "✅ Build complete!"
