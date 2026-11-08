import { useEffect, useState } from "react";
import "./DetectionTimeline.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export default function DetectionTimeline() {
  const [timeline, setTimeline] = useState([]);
  const [message, setMessage] = useState("Loading timeline...");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadTimeline() {
      try {
        const response = await fetch(
          `${API_URL}/api/v1/detections/timeline`
        );

        if (!response.ok) {
          throw new Error(`Timeline request failed (${response.status}).`);
        }

        const data = await response.json();

        if (!active) return;

        setTimeline(Array.isArray(data.timeline) ? data.timeline : []);
        setMessage(data.message || "Timeline loaded.");
      } catch (err) {
        if (active) {
          setError(err.message || "Could not load the timeline.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    loadTimeline();

    return () => {
      active = false;
    };
  }, []);

  const maxDetections = Math.max(
    1,
    ...timeline.map((item) => Number(item.detections) || 0)
  );

  return (
    <section className="detection-timeline">
      <div className="timeline-heading">
        <div>
          <h2>Detection Timeline</h2>
          <p>Candidate detections grouped by available observation dates.</p>
        </div>
        <span className="timeline-count">
          {timeline.length} date records
        </span>
      </div>

      {loading && <p className="timeline-message">Loading timeline...</p>}

      {!loading && error && (
        <p className="timeline-error">{error}</p>
      )}

      {!loading && !error && timeline.length === 0 && (
        <div className="timeline-empty">
          <p>{message}</p>
          <small>
            The source GeoJSON needs valid observation-date properties
            before a date-based timeline can be displayed.
          </small>
        </div>
      )}

      {!loading && !error && timeline.length > 0 && (
        <div className="timeline-list">
          {timeline.map((item, index) => {
            const count = Number(item.detections) || 0;
            const width = (count / maxDetections) * 100;

            return (
              <div
                className="timeline-row"
                key={`${item.date}-${item.date_field}-${index}`}
              >
                <div className="timeline-date">
                  {item.date}
                  <small>{item.date_field}</small>
                </div>

                <div className="timeline-bar-track">
                  <div
                    className="timeline-bar"
                    style={{ width: `${width}%` }}
                  />
                </div>

                <strong className="timeline-value">
                  {count}
                </strong>
              </div>
            );
          })}
        </div>
      )}

      {!loading && !error && timeline.length > 0 && (
        <p className="timeline-footnote">
          Counts are grouped by date field. Different date fields may
          describe different stages of the same observation.
        </p>
      )}
    </section>
  );
}
