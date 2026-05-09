"""
MQTT Motor Simulator
Publishes realistic motor sensor data with gradual degradation simulation.
Topic: motor/sensor_data
"""

import json
import time
import math
import random
import threading
from datetime import datetime
import paho.mqtt.client as mqtt

# ── MQTT Config ──────────────────────────────────────────────────────────────
BROKER_HOST = "broker.hivemq.com"
BROKER_PORT = 1883
TOPIC = "motor/sensor_data"
PUBLISH_INTERVAL = 1.0  # seconds

# ── Motor State ───────────────────────────────────────────────────────────────
class MotorState:
    def __init__(self):
        self.degradation = 0.0        # 0.0 (healthy) → 1.0 (critical)
        self.running_time = 0         # seconds
        self.fault_event = False
        self.fault_timer = 0

    def tick(self):
        self.running_time += 1

        # Gradual degradation over ~10 minutes of simulated time
        self.degradation = min(1.0, self.running_time / 600.0)

        # Random fault spikes (10% chance after 50% degradation)
        if self.degradation > 0.5 and random.random() < 0.10:
            self.fault_event = True
            self.fault_timer = random.randint(3, 8)

        if self.fault_timer > 0:
            self.fault_timer -= 1
        else:
            self.fault_event = False

    def get_temperature(self):
        """Base: 45°C, rises with degradation, spikes on fault."""
        base = 45.0
        drift = self.degradation * 35.0           # up to +35°C
        noise = random.gauss(0, 0.8)
        spike = 12.0 if self.fault_event else 0.0
        return round(base + drift + noise + spike, 2)

    def get_vibration(self):
        """Base: 0.5 mm/s, increases with bearing wear."""
        base = 0.5
        wear = self.degradation * 4.5
        noise = random.gauss(0, 0.1)
        spike = 2.0 if self.fault_event else 0.0
        # Add rotational frequency component
        freq = 0.3 * math.sin(self.running_time * 0.2) * (1 + self.degradation)
        return round(max(0.0, base + wear + noise + spike + freq), 3)

    def get_current(self):
        """Base: 8.5 A, rises with load and degradation."""
        base = 8.5
        load_variation = 1.5 * math.sin(self.running_time * 0.05)
        degradation_load = self.degradation * 4.0
        noise = random.gauss(0, 0.2)
        spike = 3.5 if self.fault_event else 0.0
        return round(max(0.0, base + load_variation + degradation_load + noise + spike), 2)

    def get_rpm(self):
        """Base: 1480 RPM, drops slightly with degradation."""
        base = 1480
        drop = self.degradation * 80
        noise = random.gauss(0, 5)
        fault_drop = -60 if self.fault_event else 0
        return round(max(0, base - drop + noise + fault_drop))

    def get_health_score(self):
        """Health from 100 (perfect) → 0 (critical)."""
        return round(max(0.0, (1.0 - self.degradation) * 100), 1)


# ── MQTT Client ───────────────────────────────────────────────────────────────
motor = MotorState()
client = mqtt.Client(client_id="motor_simulator")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[Simulator] Connected to MQTT broker at {BROKER_HOST}:{BROKER_PORT}")
    else:
        print(f"[Simulator] Connection failed with code {rc}")

def on_disconnect(client, userdata, rc):
    print("[Simulator] Disconnected from broker")

client.on_connect = on_connect
client.on_disconnect = on_disconnect


def publish_loop():
    while True:
        motor.tick()

        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "motor_id": "MOTOR-001",
            "temperature": motor.get_temperature(),
            "vibration": motor.get_vibration(),
            "current": motor.get_current(),
            "rpm": motor.get_rpm(),
            "health_score": motor.get_health_score(),
            "running_time_s": motor.running_time,
            "fault_event": motor.fault_event,
        }

        client.publish(TOPIC, json.dumps(payload), qos=1)
        print(f"[Simulator] Published → Temp:{payload['temperature']}°C  "
              f"Vib:{payload['vibration']}mm/s  "
              f"Health:{payload['health_score']}%  "
              f"{'⚠ FAULT' if payload['fault_event'] else ''}")

        time.sleep(PUBLISH_INTERVAL)


if __name__ == "__main__":
    print("[Simulator] Starting motor sensor simulator...")
    try:
        client.connect(BROKER_HOST, BROKER_PORT, keepalive=60)
        client.loop_start()
        publish_loop()
    except KeyboardInterrupt:
        print("\n[Simulator] Shutting down.")
        client.loop_stop()
        client.disconnect()