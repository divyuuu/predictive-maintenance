#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# start.sh — Start the full Predictive Maintenance stack
# ─────────────────────────────────────────────────────────────────────────────
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║     PREDICTIVE MAINTENANCE SYSTEM — STARTUP     ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# ── 1. Start MQTT Broker (Mosquitto) ─────────────────────────────────────────
echo "[1/3] Starting MQTT broker (Mosquitto)..."
if ! command -v mosquitto &>/dev/null; then
  echo "      ✗ Mosquitto not found. Install with:"
  echo "        macOS:  brew install mosquitto"
  echo "        Ubuntu: sudo apt install mosquitto"
  exit 1
fi

mosquitto -c "$ROOT_DIR/mosquitto.conf" -d
echo "      ✓ Mosquitto running on port 1883"

# ── 2. Start FastAPI Backend ──────────────────────────────────────────────────
echo "[2/3] Starting FastAPI backend..."
cd "$ROOT_DIR/backend"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
echo "      ✓ Backend running at http://localhost:8000"

sleep 2   # give backend time to start

# ── 3. Start MQTT Simulator ───────────────────────────────────────────────────
echo "[3/3] Starting MQTT motor simulator..."
cd "$ROOT_DIR/simulator"
python mqtt_simulator.py &
SIM_PID=$!
echo "      ✓ Simulator publishing to motor/sensor_data"

echo ""
echo "────────────────────────────────────────────────────"
echo "  Dashboard:  http://localhost:8000"
echo "  API docs:   http://localhost:8000/docs"
echo "  WebSocket:  ws://localhost:8000/ws"
echo ""
echo "  For live dev frontend: cd frontend && npm run dev"
echo "  then open http://localhost:5173"
echo "────────────────────────────────────────────────────"
echo ""
echo "Press Ctrl+C to stop all services."

# Wait and clean up on exit
trap "echo ''; echo 'Stopping...'; kill $BACKEND_PID $SIM_PID 2>/dev/null; mosquitto_ctl stop 2>/dev/null || pkill mosquitto; exit 0" SIGINT SIGTERM

wait