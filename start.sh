#!/bin/bash

echo "Starting AegisLM Backend API on port 8000..."
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "Waiting for backend to start..."
sleep 3

echo "Starting AegisLM Dashboard on port 7860..."
python -m dashboard.app --host 0.0.0.0 --port 7860 &
DASHBOARD_PID=$!

echo "Both services started!"
echo "Backend API: http://localhost:8000"
echo "Dashboard: http://localhost:7860"

# Wait for both processes
wait $BACKEND_PID $DASHBOARD_PID
