
import { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  ScaleControl,
} from "react-leaflet";

import "leaflet/dist/leaflet.css";
import "./App.css";

const API_URL =
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function App() {
  const [detections, setDetections] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
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
            `Detections API returned ${detectionResponse.status}`
          );
        }

        if (!summaryResponse.ok) {
          throw new Error(
            `Summary API returned ${summaryResponse.status}`
          );
        }

        const detectionData = await detectionResponse.json();
        const summaryData = await summaryResponse.json();

        setDetections(detectionData);
        setSummary(summaryData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchDashboardData();
  }, []);

  const detectionCount =
    summary?.total_detections ?? 0;

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
            <p className="eyebrow">ENVIRONMENTAL INTELLIGENCE</p>
            <h2>Forest Monitoring Dashboard</h2>
            <p>
              Monitor satellite-derived potential vegetation
              loss across the selected study region.
            </p>
          </div>

          <div className="source-label">
            <span>DATA SOURCE</span>
            <strong>Sentinel-2</strong>
          </div>
        </section>

        <section className="stats">
          <div className="stat-card">
            <span className="stat-label">
              Potential Loss Detections
            </span>

            <strong className="stat-number">
              {loading ? "..." : detectionCount}
            </strong>

            <span className="stat-description">
              Detected polygon regions
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
              India
            </span>
          </div>

          <div className="stat-card">
            <span className="stat-label">
              Detection Method
            </span>

            <strong className="stat-number">
              NDVI
            </strong>

            <span className="stat-description">
              Satellite vegetation analysis
            </span>
          </div>
        </section>

        <section className="map-section">
          <div className="section-heading">
            <div>
              <h3>Detection Map</h3>
              <p>
                Spatial distribution of potential vegetation loss
              </p>
            </div>

            <span className="map-badge">
              ● Live API data
            </span>
          </div>

          {loading && (
            <div className="message">
              Loading satellite detection data...
            </div>
          )}

          {error && (
            <div className="message error">
              <strong>Unable to load dashboard data</strong>
              <p>{error}</p>
              <p>
                Check whether the FastAPI backend is running
                and the Day 9 GeoJSON file exists.
              </p>
            </div>
          )}

          {!loading && !error && (
            <MapContainer
              center={[17.9, 79.5]}
              zoom={7}
              scrollWheelZoom={true}
              className="map"
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              {detections && (
                <GeoJSON
                  key={JSON.stringify(detections)}
                  data={detections}
                  style={{
                    color: "#ff4d4d",
                    weight: 2,
                    fillColor: "#ff3333",
                    fillOpacity: 0.45,
                  }}
                  onEachFeature={(feature, layer) => {
                    const properties =
                      feature.properties || {};

                    layer.bindPopup(`
                      <strong>Potential Vegetation Loss</strong>
                      <br />
                      Detection ID: ${
                        properties.id ?? "N/A"
                      }
                    `);
                  }}
                />
              )}

              <ScaleControl position="bottomleft" />
            </MapContainer>
          )}
        </section>

        <footer>
          <p>
            ForestWatch AI · Research Prototype ·
            Satellite-derived candidate detections
          </p>
          <p>
            Detection results require independent validation.
          </p>
        </footer>
      </main>
    </div>
  );
}

export default App;
