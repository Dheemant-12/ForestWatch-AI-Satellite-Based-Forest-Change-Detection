import { useState } from "react";
import "./GeoJSONExport.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export default function GeoJSONExport() {
  const [minArea, setMinArea] = useState("0");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function downloadGeoJSON() {
    setLoading(true);
    setMessage("");
    setError("");

    try {
      const area = Number(minArea);

      if (!Number.isFinite(area) || area < 0) {
        throw new Error("Enter a valid area of 0 hectares or more.");
      }

      const url = new URL(
        `${API_URL}/api/v1/detections/export/geojson`
      );

      url.searchParams.set("min_area_ha", String(area));

      const response = await fetch(url);

      if (!response.ok) {
        let detail = `Export failed (${response.status}).`;

        try {
          const data = await response.json();
          if (data.detail) detail = data.detail;
        } catch {
          // Keep the default error message.
        }

        throw new Error(detail);
      }

      const blob = await response.blob();
      const objectUrl = window.URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = objectUrl;
      link.download = "forestwatch_detections.geojson";
      document.body.appendChild(link);
      link.click();
      link.remove();

      window.URL.revokeObjectURL(objectUrl);
      setMessage("GeoJSON download started.");
    } catch (err) {
      setError(err.message || "Could not download GeoJSON.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="geojson-export">
      <div className="geojson-export-copy">
        <h2>Export detection data</h2>
        <p>Download candidate detections as a GeoJSON file for GIS analysis.</p>
      </div>

      <div className="geojson-export-controls">
        <label htmlFor="geojson-min-area">
          Minimum area (hectares)
        </label>

        <input
          id="geojson-min-area"
          type="number"
          min="0"
          step="0.1"
          value={minArea}
          onChange={(event) => setMinArea(event.target.value)}
        />

        <button
          type="button"
          onClick={downloadGeoJSON}
          disabled={loading}
        >
          {loading ? "Preparing..." : "Download GeoJSON"}
        </button>
      </div>

      {message && <p className="geojson-export-success">{message}</p>}
      {error && <p className="geojson-export-error">{error}</p>}
    </section>
  );
}
