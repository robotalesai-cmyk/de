#!/bin/bash

# Setup script for the Automated Viral Video Bot

echo "🤖 Setting up Automated Viral Video Bot..."
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check FFmpeg
echo ""
echo "Checking FFmpeg installation..."
ffmpeg -version > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "⚠️  FFmpeg is not installed."
    echo "Please install FFmpeg:"
    echo "  Ubuntu/Debian: sudo apt-get install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo "  Windows: Download from https://ffmpeg.org/download.html"
    exit 1
fi

echo "✅ FFmpeg is installed"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment"
    exit 1
fi

echo "✅ Virtual environment created"

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"

# Create .env file if it doesn't exist
echo ""
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your API keys!"
else
    echo "ℹ️  .env file already exists"
fi

# Create output directory
echo ""
echo "Creating output directory..."
mkdir -p output
echo "✅ Output directory created"

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your API keys"
echo "2. For YouTube: Download client_secret.json from Google Cloud Console"
echo "3. Run: python main.py"
echo ""
echo "For more information, see README.md"
