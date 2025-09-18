#!/bin/bash

# ACL Anthology Search - Setup Script
echo "🔧 Setting up ACL Anthology Search..."

# Check system requirements
echo "🔍 Checking system requirements..."
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Error: Python is not installed"
    echo "💡 Please install Python 3.8+ and try again"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ Error: Node.js/npm is not installed"
    echo "💡 Please install Node.js 16+ and try again"
    exit 1
fi

echo "✅ System requirements satisfied"

# Check if pyenv is available
VENV_NAME="acl-search"
VENV_PATH="$HOME/.pyenv/versions/$VENV_NAME"

if command -v pyenv &> /dev/null; then
    echo "🐍 Using pyenv for Python environment management..."
    
    # Get Python version (use latest available or fallback to system)
    PYTHON_VERSION=$(pyenv versions --bare | grep -E '^3\.(8|9|10|11|12)' | tail -1)
    if [ -z "$PYTHON_VERSION" ]; then
        echo "⚠️  No suitable Python version found in pyenv. Installing Python 3.11..."
        pyenv install 3.11.7
        PYTHON_VERSION="3.11.7"
    fi
    
    echo "📦 Creating virtual environment with Python $PYTHON_VERSION..."
    
    # Remove existing venv if it exists
    if [ -d "$VENV_PATH" ]; then
        echo "🗑️  Removing existing virtual environment..."
        pyenv uninstall -f $VENV_NAME
    fi
    
    # Create new virtual environment
    pyenv virtualenv $PYTHON_VERSION $VENV_NAME
    
    # Set local Python version for this project
    pyenv local $VENV_NAME
    
    echo "✅ Virtual environment '$VENV_NAME' created and activated"
else
    echo "🐍 pyenv not found, using system Python with venv..."
    
    # Fallback to standard venv
    if [ -d "venv" ]; then
        echo "🗑️  Removing existing virtual environment..."
        rm -rf venv
    fi
    
    # Create venv
    if command -v python3 &> /dev/null; then
        python3 -m venv venv
    else
        python -m venv venv
    fi
    
    # Activate venv
    source venv/bin/activate
    echo "✅ Virtual environment created and activated"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install --upgrade pip
    pip3 install -r requirements.txt
else
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Setup frontend dependencies
echo "📦 Installing Node.js dependencies..."
cd acl-search-frontend
npm install
cd ..

# Create activation instructions
if command -v pyenv &> /dev/null; then
    ACTIVATION_CMD="pyenv local $VENV_NAME"
else
    ACTIVATION_CMD="source venv/bin/activate"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🐍 Python virtual environment: $VENV_NAME"
echo "🔧 To activate manually: $ACTIVATION_CMD"
echo ""
echo "🚀 To start the application:"
echo "   ./start.sh"
echo ""
echo "💡 Optional: Set environment variable for AI features:"
echo "   export OPENAI_API_KEY=your_api_key_here"
echo "   ./start.sh"