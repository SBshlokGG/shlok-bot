#!/bin/bash

# ╔══════════════════════════════════════════════════════════════╗
# ║         🎵 Shlok Music Bot - Startup Script 🎵               ║
# ╚══════════════════════════════════════════════════════════════╝

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Navigate to script directory
cd "$(dirname "$0")"

echo -e "${PURPLE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                              ║"
echo "║   🎵  S H L O K   M U S I C   B O T  🎵                       ║"
echo "║                                                              ║"
echo "║   High-Quality Discord Music Streaming                       ║"
echo "║   24/7 Mode Enabled                                          ║"
echo "║                                                              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if Python is installed
echo -e "${CYAN}[1/4]${NC} Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 is not installed!${NC}"
    echo "Please install Python 3.10 or higher from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"

# Check if FFmpeg is installed
echo -e "${CYAN}[2/4]${NC} Checking FFmpeg installation..."
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${YELLOW}⚠️  FFmpeg is not installed!${NC}"
    echo -e "${YELLOW}   Installing FFmpeg...${NC}"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install ffmpeg
        else
            echo -e "${RED}❌ Homebrew not found. Please install FFmpeg manually.${NC}"
            echo "   Run: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            echo "   Then: brew install ffmpeg"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo apt-get update && sudo apt-get install -y ffmpeg
    fi
else
    echo -e "${GREEN}✅ FFmpeg is installed${NC}"
fi

# Check/Install dependencies
echo -e "${CYAN}[3/4]${NC} Checking dependencies..."
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ requirements.txt not found!${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}   Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null

# Install/upgrade dependencies
echo -e "${YELLOW}   Installing dependencies...${NC}"
pip install -r requirements.txt --quiet --upgrade

echo -e "${GREEN}✅ Dependencies installed${NC}"

# Create data directories
echo -e "${CYAN}[4/4]${NC} Setting up data directories..."
mkdir -p data/cache data/playlists data/logs
echo -e "${GREEN}✅ Directories ready${NC}"

# Start the bot
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🚀 Starting Shlok Music Bot...${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

python3 run.py
