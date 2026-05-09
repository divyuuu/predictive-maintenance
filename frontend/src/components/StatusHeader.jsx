export default function StatusHeader({ latest, connected }) {
  const statusColor = {
    HEALTHY: "#00e5a0",
    CAUTION: "#ffd166",
    WARNING: "#ff9a3c",
    CRITICAL: "#ff4757",
    CALIBRATING: "#7ecfff",
  };

  const status = latest?.status || "—";
  const color = statusColor[status] || "#888";

  return (
    <header className="status-header">
      <div className="header-left">
        <div className="logo-mark">⚙</div>
        <div>
          <h1 className="header-title">MOTOR HEALTH MONITOR</h1>
          <p className="header-sub">Predictive Maintenance System · {latest?.motor_id || "MOTOR-001"}</p>
        </div>
      </div>

      <div className="header-center">
        <div className="live-badge" style={{ borderColor: color, color }}>
          <span className="pulse-dot" style={{ background: color }} />
          {status}
        </div>
      </div>

      <div className="header-right">
        <div className={`conn-indicator ${connected ? "conn-ok" : "conn-off"}`}>
          <span className="conn-dot" />
          {connected ? "LIVE" : "RECONNECTING"}
        </div>
        <div className="header-time">
          {latest?.timestamp
            ? new Date(latest.timestamp).toLocaleTimeString()
            : "--:--:--"}
        </div>
      </div>
    </header>
  );
}