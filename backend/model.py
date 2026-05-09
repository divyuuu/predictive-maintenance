"""
Predictive Maintenance ML Model
Uses Isolation Forest for anomaly detection on motor sensor data.
Outputs: anomaly score, maintenance probability, status label.
"""

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from collections import deque
import joblib
import os

# ── Config ────────────────────────────────────────────────────────────────────
MODEL_PATH = "model/isolation_forest.pkl"
SCALER_PATH = "model/scaler.pkl"
WINDOW_SIZE = 30          # rolling window for feature engineering
MIN_SAMPLES_TO_TRAIN = 20

FEATURES = ["temperature", "vibration", "current", "rpm"]

# Thresholds for maintenance status
THRESHOLDS = {
    "critical":  0.80,   # maintenance_prob >= 80%
    "warning":   0.50,   # maintenance_prob >= 50%
    "caution":   0.30,   # maintenance_prob >= 30%
}


class MaintenancePredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.history = deque(maxlen=WINDOW_SIZE * 3)   # keep last N readings
        self.training_buffer = []                       # accumulate healthy baseline
        self._load_or_init()

    # ── Persistence ──────────────────────────────────────────────────────────

    def _load_or_init(self):
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                self.scaler = joblib.load(SCALER_PATH)
                self.is_trained = True
                print("[Model] Loaded existing model from disk.")
            except Exception as e:
                print(f"[Model] Could not load model: {e}. Will train fresh.")
        else:
            print("[Model] No saved model found. Collecting baseline data...")

    def _save(self):
        os.makedirs("model", exist_ok=True)
        joblib.dump(self.model, MODEL_PATH)
        joblib.dump(self.scaler, SCALER_PATH)

    # ── Feature Engineering ──────────────────────────────────────────────────

    def _extract_features(self, reading: dict) -> np.ndarray:
        """
        Raw features + rolling stats (mean, std) over recent window.
        Returns a 1D feature vector.
        """
        raw = np.array([reading[f] for f in FEATURES], dtype=float)

        if len(self.history) >= WINDOW_SIZE:
            window = np.array([[r[f] for f in FEATURES] for r in list(self.history)[-WINDOW_SIZE:]])
            roll_mean = window.mean(axis=0)
            roll_std  = window.std(axis=0) + 1e-6
        else:
            roll_mean = raw.copy()
            roll_std  = np.ones_like(raw)

        # Rate of change (delta from last reading)
        if len(self.history) > 0:
            prev = np.array([list(self.history)[-1][f] for f in FEATURES], dtype=float)
            delta = raw - prev
        else:
            delta = np.zeros_like(raw)

        return np.concatenate([raw, roll_mean, roll_std, delta])

    # ── Training ─────────────────────────────────────────────────────────────

    def train(self, samples: list):
        """Train Isolation Forest on healthy baseline samples."""
        X = np.array(samples)
        self.scaler.fit(X)
        X_scaled = self.scaler.transform(X)

        self.model = IsolationForest(
            n_estimators=200,
            contamination=0.05,   # assume 5% of training data may have anomalies
            max_samples="auto",
            random_state=42,
            n_jobs=-1,
        )
        self.model.fit(X_scaled)
        self.is_trained = True
        self._save()
        print(f"[Model] Trained on {len(samples)} samples. Model saved.")

    # ── Inference ─────────────────────────────────────────────────────────────

    def predict(self, reading: dict) -> dict:
        """
        Ingest a new sensor reading and return maintenance prediction.
        """
        self.history.append(reading)
        features = self._extract_features(reading)

        # Accumulate training buffer from first readings (assumed healthy at start)
        if not self.is_trained:
            self.training_buffer.append(features)
            if len(self.training_buffer) >= MIN_SAMPLES_TO_TRAIN:
                self.train(self.training_buffer)
            return self._default_result(reading, training=True)

        # Scale + score
        X = self.scaler.transform(features.reshape(1, -1))
        raw_score = self.model.score_samples(X)[0]   # more negative = more anomalous

        # Isolation Forest scores roughly in [-0.5, 0.0] range for inliers
        # Map to [0, 1] maintenance probability
        maintenance_prob = self._score_to_probability(raw_score)

        # Override with health score from simulator for smoother UX
        health_weight = (100 - reading.get("health_score", 100)) / 100.0
        blended_prob = 0.6 * maintenance_prob + 0.4 * health_weight
        blended_prob = round(min(1.0, max(0.0, blended_prob)), 4)

        status = self._get_status(blended_prob)
        rul_days = self._estimate_rul(blended_prob)

        return {
            "maintenance_probability": blended_prob,
            "maintenance_probability_pct": round(blended_prob * 100, 1),
            "anomaly_score": round(raw_score, 4),
            "status": status,
            "rul_days": rul_days,
            "is_anomaly": bool(self.model.predict(X)[0] == -1),
            "model_ready": True,
        }

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _score_to_probability(self, raw_score: float) -> float:
        """Convert IF score (negative = bad) to [0,1] probability."""
        # Typical healthy range: [-0.15, 0.0], anomaly: [-0.5, -0.15]
        clipped = max(-0.6, min(0.0, raw_score))
        prob = (clipped / -0.6)   # 0 = healthy, 1 = critical
        return round(prob, 4)

    def _get_status(self, prob: float) -> str:
        if prob >= THRESHOLDS["critical"]:
            return "CRITICAL"
        elif prob >= THRESHOLDS["warning"]:
            return "WARNING"
        elif prob >= THRESHOLDS["caution"]:
            return "CAUTION"
        else:
            return "HEALTHY"

    def _estimate_rul(self, prob: float) -> float:
        """Rough RUL estimate in days based on maintenance probability."""
        if prob >= 0.95:
            return 0.0
        max_rul = 30.0
        return round(max_rul * (1 - prob), 1)

    def _default_result(self, reading: dict, training: bool = False) -> dict:
        return {
            "maintenance_probability": 0.0,
            "maintenance_probability_pct": 0.0,
            "anomaly_score": 0.0,
            "status": "CALIBRATING" if training else "HEALTHY",
            "rul_days": 30.0,
            "is_anomaly": False,
            "model_ready": False,
        }