import { useMemo } from "react";
import StatusHeader from "./StatusHeader";
import MetricCard from "./MetricCard";
import HealthGauge from "./HealthGauge";
import SensorChart from "./SensorChart";
import AlertBanner from "./AlertBanner";
import MaintenancePanel from "./MaintenancePanel";

export default function Dashboard({ latest, history, connected }) {
  const chartData = useMemo(() =>
    history.map((d, i) => ({
      index: i,
      time: d.timestamp ? new Date(d.timestamp).toLocaleTimeString() : `T${i}`,
      temperature: d.temperature,
      vibration: d.vibration,
      current: d.current,
      rpm: d.rpm,
      health: d.health_score,
      maintenance_pct: d.maintenance_probability_pct,
    })),
    [history]
  );

  const showAlert = latest && (latest.status === "CRITICAL" || latest.status === "WARNING");

  return (
    <div className="dashboard">
      <StatusHeader latest={latest} connected={connected} />
      {showAlert && <AlertBanner status={latest.status} prob={latest.maintenance_probability_pct} />}

      <div className="metrics-row">
        <MetricCard label="Temperature" value={latest?.temperature?.toFixed(1)} unit="°C" icon="🌡" warn={latest?.temperature > 70} critical={latest?.temperature > 80} />
        <MetricCard label="Vibration" value={latest?.vibration?.toFixed(3)} unit="mm/s" icon="📳" warn={latest?.vibration > 3.0} critical={latest?.vibration > 4.5} />
        <MetricCard label="Current Draw" value={latest?.current?.toFixed(1)} unit="A" icon="⚡" warn={latest?.current > 11} critical={latest?.current > 13} />
        <MetricCard label="Motor Speed" value={latest?.rpm} unit="RPM" icon="⚙" warn={latest?.rpm < 1400} critical={latest?.rpm < 1350} />
      </div>

      <div className="main-grid">
        <div className="left-col">
          <HealthGauge health={latest?.health_score} status={latest?.status} />
          <MaintenancePanel latest={latest} />
        </div>
        <div className="right-col">
          <SensorChart data={chartData} />
        </div>
      </div>
    </div>
  );
}