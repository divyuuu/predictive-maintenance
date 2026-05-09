import { useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from "recharts";

const METRICS = [
  { key: "health",          label: "Health",       unit: "%",     color: "#00e5a0", warnVal: 50  },
  { key: "maintenance_pct", label: "Maint. Prob",  unit: "%",     color: "#ff9a3c", warnVal: 50  },
  { key: "temperature",     label: "Temperature",  unit: "°C",    color: "#ff6b9d", warnVal: 70  },
  { key: "vibration",       label: "Vibration",    unit: "mm/s",  color: "#7ecfff", warnVal: 3.0 },
  { key: "current",         label: "Current",      unit: "A",     color: "#ffd166", warnVal: 11  },
  { key: "rpm",             label: "RPM",          unit: "RPM",   color: "#c77dff", warnVal: null },
];

const CustomTooltip = ({ active, payload, label, unit }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <div className="tooltip-time">{label}</div>
      <div className="tooltip-val">
        {payload[0].value?.toFixed(2)} <span className="tooltip-unit">{unit}</span>
      </div>
    </div>
  );
};

export default function SensorChart({ data }) {
  const [activeMetric, setActiveMetric] = useState("health");
  const metric = METRICS.find((m) => m.key === activeMetric);

  return (
    <div className="chart-card">
      <div className="chart-tabs">
        {METRICS.map((m) => (
          <button
            key={m.key}
            className={`chart-tab ${activeMetric === m.key ? "chart-tab-active" : ""}`}
            style={activeMetric === m.key ? { color: m.color, borderColor: m.color } : {}}
            onClick={() => setActiveMetric(m.key)}
          >
            {m.label}
          </button>
        ))}
      </div>

      <div className="chart-area">
        {data.length === 0 ? (
          <div className="chart-empty">Waiting for data...</div>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={data} margin={{ top: 8, right: 16, left: -16, bottom: 0 }}>
              <CartesianGrid stroke="rgba(255,255,255,0.05)" strokeDasharray="3 3" />
              <XAxis
                dataKey="time"
                tick={{ fill: "#556", fontSize: 10 }}
                interval={Math.max(1, Math.floor(data.length / 8))}
              />
              <YAxis tick={{ fill: "#556", fontSize: 10 }} />
              <Tooltip content={<CustomTooltip unit={metric.unit} />} />
              {metric.warnVal && (
                <ReferenceLine
                  y={metric.warnVal}
                  stroke="#ff4757"
                  strokeDasharray="4 2"
                  strokeOpacity={0.5}
                />
              )}
              <Line
                type="monotone"
                dataKey={metric.key}
                stroke={metric.color}
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
                style={{ filter: `drop-shadow(0 0 4px ${metric.color})` }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}   