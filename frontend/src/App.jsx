
import { useEffect, useMemo, useState } from "react";
import AnalyticsDashboard from "./components/AnalyticsDashboard";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  ScaleControl,
  useMap,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";
import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";


function FitDetections({ data }) {
  const map = useMap();

  useEffect(() => {
    if (!data?.features?.length) return;

    const layer = window.L.geoJSON(data);
    const bounds = layer.getBounds();

    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [30, 30] });
    }
  }, [data, map]);

  return null;
}


function App() {

  const [detections, setDetections] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");
  const [selected, setSelected] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);


  async function fetchDashboardData() {

    try {
      setLoading(true);
      setError("");

      const [detectionResponse, summaryResponse] =
        await Promise.all([
          fetch(`${API_URL}/api/v1/detections`),
          fetch(`${API_URL}/api/v1/detections/summary`),
        ]);

      if (!detectionResponse.ok) {
        throw new Error(
          `Detection API error: ${detectionResponse.status}`
        );
      }

      if (!summaryResponse.ok) {
        throw new Error(
          `Summary API error: ${summaryResponse.status}`
        );
      }

      const detectionData = await detectionResponse.json();
      const summaryData = await summaryResponse.json();

      setDetections(detectionData);
      setSummary(summaryData);
      setLastUpdated(new Date());

    } catch (err) {

      setError(err.message);

    } finally {

      setLoading(false);

    }
  }


  useEffect(() => {
    fetchDashboardData();
  }, []);


  const features = useMemo(
    () => detections?.features || [],
    [detections]
  );


  const filteredFeatures = useMemo(() => {

    if (filter === "all") {
      return features;
    }

    if (filter === "area") {
      return features.filter(
        feature =>
          Number(feature.properties?.area_ha || 0) >= 1
      );
    }

    return features.filter(
      feature =>
        feature.properties?.status ===
        "Potential vegetation loss"
    );

  }, [features, filter]);


  const filteredGeoJSON = useMemo(
    () => ({
      type: "FeatureCollection",
      features: filteredFeatures,
    }),
    [filteredFeatures]
  );


  function openDetection(feature) {
    setSelected(feature);
  }


  function getProperties(feature) {
    return feature?.properties || {};
  }


  const selectedProperties = getProperties(selected);


  return (
    <div className="app">

      <header className="topbar">

        <div className="brand">
          <div className="brand-icon">🌳</div>

          <div>
            <h1>ForestWatch AI</h1>
            <p>Satellite-Based Forest Change Monitoring</p>
          </div>
        </div>

        <div className="region">
          <span className="status-dot"></span>
          Telangana, India
        </div>

      </header>


      <main className="dashboard">

        <section className="intro">

          <div>
            <p className="eyebrow">
              ENVIRONMENTAL INTELLIGENCE
            </p>

            <h2>Forest Monitoring Dashboard</h2>

            <p>
              Explore satellite-derived potential vegetation
              loss detections.
            </p>
          </div>

          <button
            className="refresh-button"
            onClick={fetchDashboardData}
            disabled={loading}
          >
            {loading ? "Loading..." : "↻ Refresh Data"}
          </button>

        </section>


        <section className="stats">

          <div className="stat-card">
            <span className="stat-label">
              Total Detections
            </span>

            <strong className="stat-number">
              {loading ? "..." : features.length}
            </strong>

            <span className="stat-description">
              Candidate regions
            </span>
          </div>


          <div className="stat-card">
            <span className="stat-label">
              Filtered Detections
            </span>

            <strong className="stat-number">
              {loading ? "..." : filteredFeatures.length}
            </strong>

            <span className="stat-description">
              Matching current filter
            </span>
          </div>


          <div className="stat-card">
            <span className="stat-label">
              Study Region
            </span>

            <strong className="stat-number">
              Telangana
            </strong>

            <span className="stat-description">
              Sentinel-2 monitoring
            </span>
          </div>

        </section>


        {error && (
          <div className="message error">
            <strong>Unable to load detection data</strong>
            <p>{error}</p>
            <p>
              Check the backend and the Day 9 GeoJSON output.
            </p>
          </div>
        )}


        <section className="map-section">

          <div className="section-heading">

            <div>
              <h3>Detection Map</h3>
              <p>
                Spatial distribution of candidate regions
              </p>
            </div>

            <span className="map-badge">
              ● API-connected
            </span>

          </div>


          <div className="filter-bar">

            <label htmlFor="detection-filter">
              Filter detections:
            </label>

            <select
              id="detection-filter"
              value={filter}
              onChange={event => setFilter(event.target.value)}
            >
              <option value="all">All detections</option>
              <option value="area">Area ≥ 1 hectare</option>
              <option value="candidate">Potential loss candidates</option>
            </select>

          </div>


          {!loading && !error && (

            <MapContainer
              center={[17.9, 79.5]}
              zoom={7}
              scrollWheelZoom={true}
              className="map"
            >

              <TileLayer
                attribution='&copy; OpenStreetMap contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              <FitDetections data={filteredGeoJSON} />

              <GeoJSON
                key={`${filter}-${filteredFeatures.length}`}
                data={filteredGeoJSON}
                style={{
                  color: "#e34c4c",
                  weight: 2,
                  fillColor: "#e34c4c",
                  fillOpacity: 0.4,
                }}
                onEachFeature={(feature, layer) => {

                  const properties =
                    feature.properties || {};

                  layer.bindPopup(`
                    <strong>${properties.detection_id || "Detection"}</strong>
                    <br/>
                    ${properties.status || "Potential vegetation loss"}
                    <br/>
                    Area: ${properties.area_ha ?? "Not available"} ha
                  `);

                  layer.on("click", () => {
                    openDetection(feature);
                  });

                }}
              />

              <ScaleControl position="bottomleft" />

            </MapContainer>

          )}

          {!loading && !error && filteredFeatures.length === 0 && (
            <p className="empty-state">
              No detections match this filter.
            </p>
          )}

        </section>


        <section className="table-section">

          <div className="section-heading">
            <div>
              <h3>Detection Records</h3>
              <p>
                Select a record to inspect its properties.
              </p>
            </div>
          </div>


          {loading ? (

            <p className="message">
              Loading detection records...
            </p>

          ) : !error && (

            <div className="table-wrapper">

              <table>

                <thead>
                  <tr>
                    <th>Detection ID</th>
                    <th>Status</th>
                    <th>Area (ha)</th>
                    <th>Action</th>
                  </tr>
                </thead>

                <tbody>

                  {filteredFeatures.map((feature, index) => {

                    const properties =
                      feature.properties || {};

                    return (

                      <tr key={properties.detection_id || index}>

                        <td>
                          {properties.detection_id || `FW-${index + 1}`}
                        </td>

                        <td>
                          <span className="candidate-label">
                            {properties.status || "Potential loss"}
                          </span>
                        </td>

                        <td>
                          {properties.area_ha != null
                            ? Number(properties.area_ha).toFixed(2)
                            : "N/A"}
                        </td>

                        <td>
                          <button
                            className="view-button"
                            onClick={() => openDetection(feature)}
                          >
                            View details
                          </button>
                        </td>

                      </tr>

                    );

                  })}


                  {filteredFeatures.length === 0 && (
                    <tr>
                      <td colSpan="4">
                        No matching detections found.
                      </td>
                    </tr>
                  )}

                </tbody>

              </table>

            </div>

          )}

        </section>


        {selected && (

          <section className="details-panel">

            <div className="section-heading">

              <div>
                <h3>Detection Details</h3>
                <p>
                  {selectedProperties.detection_id || "Selected detection"}
                </p>
              </div>

              <button
                className="view-button"
                onClick={() => setSelected(null)}
              >
                Close
              </button>

            </div>

            <div className="details-grid">

              <div>
                <span>Detection ID</span>
                <strong>
                  {selectedProperties.detection_id || "N/A"}
                </strong>
              </div>

              <div>
                <span>Status</span>
                <strong>
                  {selectedProperties.status || "Potential loss"}
                </strong>
              </div>

              <div>
                <span>Area</span>
                <strong>
                  {selectedProperties.area_ha != null
                    ? `${selectedProperties.area_ha} ha`
                    : "Not available"}
                </strong>
              </div>

            </div>

          </section>

        )}


        <footer>

          <p>
            ForestWatch AI · Research Prototype
          </p>

          <p>
            Last updated:{" "}
            {lastUpdated
              ? lastUpdated.toLocaleTimeString()
              : "Not available"}
          </p>

          <p>
            Potential vegetation loss requires independent validation.
          </p>

        </footer>

      </main>

    </div>
  );
}

export default App;
