#!/bin/bash

# ACL Anthology Search - Start Script
# This script starts both the backend API server and frontend application

echo "🚀 Starting ACL Anthology Search..."

# Check if we're in the right directory
if [ ! -f "api_server.py" ] || [ ! -d "acl-search-frontend" ]; then
    echo "❌ Error: Please run this script from the ACL-Anthology-Search directory"
    exit 1
fi

# Activate Python virtual environment
VENV_NAME="acl-search"
if command -v pyenv &> /dev/null && [ -d "$HOME/.pyenv/versions/$VENV_NAME" ]; then
    echo "🐍 Activating pyenv virtual environment: $VENV_NAME"
    export PYENV_VERSION=$VENV_NAME
elif [ -d "venv" ]; then
    echo "🐍 Activating virtual environment: venv"
    source venv/bin/activate
else
    echo "⚠️  No virtual environment found. Using system Python."
    echo "💡 Run ./setup.sh first to create a virtual environment."
fi

# Function to cleanup processes on exit
cleanup() {
    echo -e "\n🛑 Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo "✅ Servers stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Start backend API server
echo "📡 Starting backend API server..."
python api_server.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start frontend Next.js application
echo "🌐 Starting frontend application..."
cd acl-search-frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait a moment for frontend to start
sleep 5

echo ""
echo "✅ ACL Anthology Search is now running!"
echo ""
echo "📡 Backend API: http://127.0.0.1:8000"
echo "🌐 Frontend:    http://localhost:3000"
echo ""
echo "💡 Tip: Set OPENAI_API_KEY environment variable for AI query conversion"
echo ""
echo "Press Ctrl+C to stop all servers"

# Keep script running and wait for processes
wait $BACKEND_PID $FRONTEND_PID