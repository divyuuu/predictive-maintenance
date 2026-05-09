import { useState, useEffect, useRef, useCallback } from "react";
import Dashboard from "./components/Dashboard";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws";
const RECONNECT_DELAY = 3000;

export default function App() {
  const [history, setHistory] = useState([]);
  const [latest, setLatest] = useState(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      console.log("[WS] Connected");
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === "history") {
        setHistory(msg.data);
        if (msg.data.length > 0) setLatest(msg.data[msg.data.length - 1]);
      } else if (msg.type === "update") {
        setLatest(msg.data);
        setHistory((prev) => {
          const updated = [...prev, msg.data];
          return updated.slice(-120); // keep last 120 points
        });
      }
    };

    ws.onclose = () => {
      setConnected(false);
      console.log("[WS] Disconnected, retrying...");
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY);
    };

    ws.onerror = () => ws.close();
  }, []);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return <Dashboard latest={latest} history={history} connected={connected} />;
}