# 🔧 Predictive Maintenance System

A real-time motor health monitoring dashboard powered by MQTT, Isolation Forest ML, FastAPI, and React.

---

## 📁 Folder Structure

```
predictive-maintenance/
│
├── simulator/
│   └── mqtt_simulator.py       # Publishes motor sensor data via MQTT
│
├── backend/
│   ├── main.py                 # FastAPI app — MQTT subscriber + WebSocket broadcaster
│   ├── model.py                # Isolation Forest ML model (anomaly detection)
│   └── model/                  # Auto-created — stores trained model files
│       ├── isolation_forest.pkl
│       └── scaler.pkl
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx             # WebSocket connection + state management
│       ├── index.css           # Full dark industrial theme
│       └── components/
│           ├── Dashboard.jsx   # Main layout
│           ├── StatusHeader.jsx
│           ├── MetricCard.jsx
│           ├── HealthGauge.jsx # SVG arc gauge
│           ├── AlertBanner.jsx # Warning/critical alerts
│           ├── MaintenancePanel.jsx
│           └── SensorChart.jsx # Live time-series charts
│
├── mosquitto.conf              # Local MQTT broker config
├── requirements.txt            # Python dependencies
├── start.sh                    # One-command startup script
└── README.md
```

---

## 🚀 Setup Guide

### Prerequisites

| Tool | Install |
|------|---------|
| Python 3.10+ | https://python.org |
| Node.js 18+ | https://nodejs.org |
| Mosquitto MQTT | `brew install mosquitto` (macOS) / `sudo apt install mosquitto` (Ubuntu) |

---

### Step 1 — Install Python dependencies

```bash
cd predictive-maintenance
pip install -r requirements.txt
```

---

### Step 2 — Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

---

### Step 3 — Start the MQTT Broker

Open **Terminal 1**:

```bash
mosquitto -c mosquitto.conf
```

You should see: `Starting in local only mode`

---

### Step 4 — Start the FastAPI Backend

Open **Terminal 2**:

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

You should see: `[MQTT] Connected and subscribed to 'motor/sensor_data'`

---

### Step 5 — Start the Motor Simulator

Open **Terminal 3**:

```bash
cd simulator
python mqtt_simulator.py
```

You should see sensor readings being published every second.

---

### Step 6 — Start the Frontend

Open **Terminal 4**:

```bash
cd frontend
npm run dev
```

Then open **http://localhost:5173** in your browser.

---

## 🧠 How It Works

```
mqtt_simulator.py
  │  publishes JSON every 1s to topic: motor/sensor_data
  ▼
Mosquitto Broker (port 1883)
  │  routes messages to subscribers
  ▼
FastAPI Backend (port 8000)
  │  receives via paho-mqtt
  │  → runs Isolation Forest inference
  │  → enriches data with maintenance probability
  ▼
WebSocket /ws
  │  broadcasts enriched JSON to all connected browsers
  ▼
React Dashboard (port 5173)
  │  renders live sensor charts, health gauge, alert banner
```

---

## 📊 Sensor Channels

| Channel | Normal Range | Warning |
|---------|-------------|---------|
| Temperature | 45–60 °C | > 70 °C |
| Vibration | 0.5–1.5 mm/s | > 3.0 mm/s |
| Current Draw | 8–10 A | > 11 A |
| Motor Speed | 1450–1490 RPM | < 1400 RPM |

---

## ⚙️ ML Model Notes

- **Algorithm**: Isolation Forest (sklearn)
- **Trained on**: First 20 readings (healthy baseline)
- **Features**: raw sensor values + rolling mean/std + rate of change
- **Output**: Maintenance probability (0–100%), status (HEALTHY / CAUTION / WARNING / CRITICAL)
- **Model persisted** to `backend/model/` — delete those files to retrain from scratch