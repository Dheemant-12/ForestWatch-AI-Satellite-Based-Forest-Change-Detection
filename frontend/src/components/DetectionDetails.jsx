import "./DetectionDetails.css";

export default function DetectionDetails({ detection, onClose }) {
  if (!detection) return null;

  const properties = detection.properties || {};
  const geometry = detection.geometry;

  const excluded = ["geometry", "geometry_wkt"];

  const readableProperties = Object.entries(properties).filter(
    ([key, value]) =>
      !excluded.includes(key) &&
      value !== null &&
      value !== undefined &&
      typeof value !== "object"
  );

  return (
    <aside className="detection-details">
      <div className="detection-details-header">
        <div>
          <span className="detection-eyebrow">DETECTION RECORD</span>
          <h2>
            {properties.detection_id || "Selected detection"}
          </h2>
        </div>

        <button
          className="detection-close"
          onClick={onClose}
          aria-label="Close detection details"
        >
          ×
        </button>
      </div>

      <div className="detection-status">
        {properties.status || "Potential vegetation loss"}
      </div>

      <div className="detection-primary">
        <span>Candidate area</span>
        <strong>
          {properties.area_ha != null
            ? `${Number(properties.area_ha).toFixed(2)} ha`
            : "Not available"}
        </strong>
      </div>

      <h3>Detection attributes</h3>

      <div className="detection-property-list">
        {readableProperties.map(([key, value]) => (
          <div className="detection-property" key={key}>
            <span>{key.replaceAll("_", " ")}</span>
            <strong>{String(value)}</strong>
          </div>
        ))}
      </div>

      <div className="detection-geometry">
        <h3>Spatial information</h3>
        <p>
          Geometry type: <strong>{geometry?.type || "Unavailable"}</strong>
        </p>
        <p>
          Coordinates:{" "}
          <strong>
            {geometry?.coordinates ? "Available" : "Unavailable"}
          </strong>
        </p>
      </div>

      <p className="detection-disclaimer">
        This is a potential vegetation-loss candidate, not proof of
        illegal deforestation.
      </p>
    </aside>
  );
}
