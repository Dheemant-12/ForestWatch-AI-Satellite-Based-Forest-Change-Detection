import { useEffect, useState } from "react";
import "./AnalyticsDashboard.css";

const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function StatCard({ title, value, unit }) {
  return (
    <div className="analytics-card">
      <p className="analytics-card-title">{title}</p>
      <h2>{value ?? "—"}<span className="analytics-unit"> {unit}</span></h2>
    </div>
  );
}

export default function AnalyticsDashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function fetchAnalytics() {
      try {
        const response = await fetch(`${API_URL}/api/v1/analytics`);

        if (!response.ok) {
          throw new Error(`API returned status ${response.status}`);
        }

        const data = await response.json();

        if (active) setAnalytics(data);
      } catch (err) {
        if (active) setError(err.message);
      } finally {
        if (active) setLoading(false);
      }
    }

    fetchAnalytics();

    return () => {
      active = false;
    };
  }, []);

  if (loading) return <p>Loading analytics...</p>;

  if (error) {
    return (
      <div className="analytics-error">
        Unable to load analytics: {error}
      </div>
    );
  }

  if (!analytics) return <p>No analytics available.</p>;

  const distribution = analytics.area_distribution || {};

  const chartItems = [
    { label: "Under 1 ha", value: distribution.under_1_ha ?? 0 },
    { label: "1–5 ha", value: distribution["1_to_5_ha"] ?? 0 },
    { label: "5–10 ha", value: distribution["5_to_10_ha"] ?? 0 },
    { label: "Over 10 ha", value: distribution.over_10_ha ?? 0 },
  ];

  const maxValue = Math.max(1, ...chartItems.map(item => item.value));

  return (
    <section className="analytics-dashboard">
      <div className="analytics-heading">
        <div>
          <h2>Detection Analytics</h2>
          <p>Statistics from potential vegetation-loss detections</p>
        </div>
        <span className="analytics-live">API DATA</span>
      </div>

      <div className="analytics-grid">
        <StatCard title="Total detections" value={analytics.total_detections} />
        <StatCard title="Total candidate area" value={analytics.total_candidate_area_ha} unit="ha" />
        <StatCard title="Average candidate area" value={analytics.average_area_ha} unit="ha" />
        <StatCard title="Largest candidate" value={analytics.largest_detection_ha} unit="ha" />
      </div>

      <div className="analytics-chart">
        <h3>Candidate Area Distribution</h3>
        <p>Number of detections in each area range</p>

        {chartItems.map(item => (
          <div className="chart-row" key={item.label}>
            <div className="chart-label">
              <span>{item.label}</span>
              <strong>{item.value}</strong>
            </div>
            <div className="chart-track">
              <div
                className="chart-fill"
                style={{ width: `${item.value / maxValue * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      <p className="analytics-note">
        These statistics represent candidate vegetation loss, not confirmed
        illegal deforestation. Valid area measurements:
        {" "}{analytics.detections_with_valid_area ?? "Unavailable"}
        {" "}/ {analytics.total_detections}
      </p>
    </section>
  );
}
