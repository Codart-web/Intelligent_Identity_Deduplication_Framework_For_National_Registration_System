#!/bin/bash
# =============================================
# Start all NRC Deduplication Framework services
# Run from project root with: ./start.sh
# =============================================

source venv/bin/activate

echo "Starting PostgreSQL..."
sudo systemctl start postgresql

echo "Starting central server (port 5000)..."
cd tier2_central && python api_gateway/app.py &
CENTRAL_PID=$!
cd ..

sleep 2

echo "Starting Lusaka terminal (port 5001)..."
cd tier1_terminals
TERMINAL_ID=LUSAKA PORT=5001 python app.py &
LUSAKA_PID=$!

echo "Starting Kitwe terminal (port 5002)..."
TERMINAL_ID=KITWE PORT=5002 python app.py &
KITWE_PID=$!

echo "Starting Ndola terminal (port 5003)..."
TERMINAL_ID=NDOLA PORT=5003 python app.py &
NDOLA_PID=$!
cd ..

echo "Starting Tier 3 API stub (port 5004)..."
cd tier3_api && python app.py &
TIER3_PID=$!
cd ..

echo ""
echo "============================================"
echo "All services running. Access at:"
echo "  Admin dashboard : http://localhost:5000"
echo "  Lusaka terminal : http://localhost:5001"
echo "  Kitwe terminal  : http://localhost:5002"
echo "  Ndola terminal  : http://localhost:5003"
echo "  Tier 3 API      : http://localhost:5004"
echo "============================================"
echo "Press Ctrl+C to stop all services."
echo ""

trap "echo 'Stopping all services...'; kill 0" EXIT
wait
