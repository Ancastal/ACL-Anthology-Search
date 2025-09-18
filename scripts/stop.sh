#!/bin/bash
# Stop both backend and frontend processes

echo "🛑 Stopping ACL Anthology Search services..."

# Kill uvicorn processes
pkill -f "uvicorn.*api_server" && echo "✅ Backend stopped"

# Kill Next.js dev processes
pkill -f "next.*dev" && echo "✅ Frontend stopped"

echo "🏁 All services stopped"