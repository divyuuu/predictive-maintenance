"""
FastAPI Backend — Predictive Maintenance System
- Subscribes to MQTT topic
- Runs ML inference on each reading
- Broadcasts enriched data to frontend via WebSocket
"""

import asyncio
import json
import os
import sys
from collections import deque
from datetime import datetime
from typing import Set

import paho.mqtt.client as mqtt
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from model import MaintenancePredictor

# ── Config ────────────────────────────────────────────────────────────────────
# MQTT_BROKER   = os.getenv("MQTT_BROKER", "localhost")
# MQTT_PORT     = int(os.getenv("MQTT_PORT", 1883))
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT     = int(os.getenv("MQTT_PORT", 1883))
FRONTEND_URL  = os.getenv("FRONTEND_URL", "*")
MQTT_TOPIC    = "motor/sensor_data"
HISTORY_LEN   = 120   # keep last 120 data points for charts

# ── App Setup ─────────────────────────────────────────────────────────────────
app = FastAPI(title="Predictive Maintenance API", version="1.0.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── State ─────────────────────────────────────────────────────────────────────
predictor = MaintenancePredictor()
history: deque = deque(maxlen=HISTORY_LEN)
latest_reading: dict = {}
connected_clients: Set[WebSocket] = set()

# Async queue to bridge MQTT (sync thread) → FastAPI (async event loop)
message_queue: asyncio.Queue = asyncio.Queue()


# ── WebSocket Manager ─────────────────────────────────────────────────────────
async def broadcast(payload: dict):
    dead = set()
    for ws in connected_clients:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.add(ws)
    connected_clients.difference_update(dead)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    print(f"[WS] Client connected. Total: {len(connected_clients)}")

    # Send existing history immediately on connect
    if history:
        await websocket.send_json({
            "type": "history",
            "data": list(history),
        })

    try:
        while True:
            await websocket.receive_text()   # keep connection alive
    except WebSocketDisconnect:
        connected_clients.discard(websocket)
        print(f"[WS] Client disconnected. Total: {len(connected_clients)}")


# ── MQTT Callbacks (sync, runs in MQTT thread) ────────────────────────────────
def on_mqtt_message(client, userdata, msg):
    try:
        raw = json.loads(msg.payload.decode())
        message_queue.put_nowait(raw)
    except Exception as e:
        print(f"[MQTT] Parse error: {e}")

def on_mqtt_connect(client, userdata, flags, rc):
    if rc == 0:
        client.subscribe(MQTT_TOPIC, qos=1)
        print(f"[MQTT] Connected and subscribed to '{MQTT_TOPIC}'")
    else:
        print(f"[MQTT] Connection failed: {rc}")


# ── Message Processor (async, runs in FastAPI event loop) ─────────────────────
async def process_messages():
    """Drain the async queue, run ML, broadcast to WebSocket clients."""
    while True:
        try:
            raw = await asyncio.wait_for(message_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            continue

        # ML inference
        prediction = predictor.predict(raw)

        # Merge sensor + prediction into one enriched record
        enriched = {
            **raw,
            **prediction,
            "received_at": datetime.utcnow().isoformat() + "Z",
        }

        history.append(enriched)
        latest_reading.update(enriched)

        await broadcast({
            "type": "update",
            "data": enriched,
        })


# ── REST Endpoints ────────────────────────────────────────────────────────────
@app.get("/api/status")
def get_status():
    return {"status": "ok", "clients": len(connected_clients)}

@app.get("/api/latest")
def get_latest():
    return latest_reading or {"message": "No data yet"}

@app.get("/api/history")
def get_history():
    return {"count": len(history), "data": list(history)}


# ── Startup / Shutdown ────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup():
    mqtt_client = mqtt.Client(client_id="backend_subscriber", clean_session=True)
    mqtt_client.on_connect = on_mqtt_connect
    mqtt_client.on_message = on_mqtt_message

    try:
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        mqtt_client.loop_start()
        print("[MQTT] Client started.")
    except Exception as e:
        print(f"[MQTT] Could not connect to broker: {e}")

    import threading
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from simulator.mqtt_simulator import MotorState, publish_loop
    sim_thread = threading.Thread(target=publish_loop, daemon=True)
    sim_thread.start()
    print("[Simulator] Started in background thread.")

    asyncio.create_task(process_messages())
    print("[API] Startup complete. Listening for MQTT messages...")

# ── Serve React frontend (after build) ───────────────────────────────────────
# frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
# if os.path.exists(frontend_dist):
#     app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="static")