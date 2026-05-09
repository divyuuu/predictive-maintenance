export default function HealthGauge({ health = 100, status = "HEALTHY" }) {
  const pct = Math.max(0, Math.min(100, health));

  // Arc geometry
  const cx = 110, cy = 110, r = 85;
  const startAngle = 220;
  const sweepAngle = 280; // degrees
  const endAngle = startAngle + sweepAngle;

  function polar(deg, radius = r) {
    const rad = (deg * Math.PI) / 180;
    return {
      x: cx + radius * Math.cos(rad),
      y: cy + radius * Math.sin(rad),
    };
  }

  function arcPath(from, to, radius = r) {
    const s = polar(from, radius);
    const e = polar(to, radius);
    const large = to - from > 180 ? 1 : 0;
    return `M ${s.x} ${s.y} A ${radius} ${radius} 0 ${large} 1 ${e.x} ${e.y}`;
  }

  const progressAngle = startAngle + (sweepAngle * pct) / 100;

  const color =
    pct > 70 ? "#00e5a0" :
    pct > 50 ? "#ffd166" :
    pct > 30 ? "#ff9a3c" : "#ff4757";

  const needle = polar(progressAngle, 68);

  return (
    <div className="gauge-card">
      <div className="gauge-label-top">MOTOR HEALTH</div>
      <svg viewBox="0 0 220 175" className="gauge-svg">
        {/* Background arc */}
        <path
          d={arcPath(startAngle, endAngle)}
          fill="none"
          stroke="rgba(255,255,255,0.07)"
          strokeWidth="14"
          strokeLinecap="round"
        />
        {/* Tick marks */}
        {[0, 25, 50, 75, 100].map((tick) => {
          const a = startAngle + (sweepAngle * tick) / 100;
          const outer = polar(a, r + 6);
          const inner = polar(a, r - 6);
          return (
            <line
              key={tick}
              x1={outer.x} y1={outer.y}
              x2={inner.x} y2={inner.y}
              stroke="rgba(255,255,255,0.2)"
              strokeWidth="1.5"
            />
          );
        })}
        {/* Progress arc */}
        {pct > 0 && (
          <path
            d={arcPath(startAngle, progressAngle)}
            fill="none"
            stroke={color}
            strokeWidth="14"
            strokeLinecap="round"
            style={{ filter: `drop-shadow(0 0 8px ${color})` }}
          />
        )}
        {/* Center dot */}
        <circle cx={cx} cy={cy} r={5} fill={color} />
        {/* Needle line */}
        <line
          x1={cx} y1={cy}
          x2={needle.x} y2={needle.y}
          stroke={color}
          strokeWidth="2.5"
          strokeLinecap="round"
          style={{ filter: `drop-shadow(0 0 4px ${color})` }}
        />
        {/* Center value */}
        <text x={cx} y={cy + 28} textAnchor="middle" className="gauge-pct" fill={color}>
          {Math.round(pct)}%
        </text>
        {/* Min/Max labels */}
        <text x={polar(startAngle, r + 20).x} y={polar(startAngle, r + 20).y + 4}
          textAnchor="middle" className="gauge-tick-label">0</text>
        <text x={polar(endAngle, r + 20).x} y={polar(endAngle, r + 20).y + 4}
          textAnchor="middle" className="gauge-tick-label">100</text>
      </svg>
      <div className="gauge-status" style={{ color }}>
        {status}
      </div>
    </div>
  );
}