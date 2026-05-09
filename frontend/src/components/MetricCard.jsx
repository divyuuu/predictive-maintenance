export default function MetricCard({ label, value, unit, icon, warn, critical }) {
  const state = critical ? "critical" : warn ? "warn" : "normal";
  return (
    <div className={`metric-card metric-${state}`}>
      <div className="metric-icon">{icon}</div>
      <div className="metric-body">
        <div className="metric-label">{label}</div>
        <div className="metric-value">
          {value ?? "—"}
          <span className="metric-unit">{unit}</span>
        </div>
      </div>
      {(warn || critical) && (
        <div className="metric-flag">{critical ? "!" : "↑"}</div>
      )}
    </div>
  );
}