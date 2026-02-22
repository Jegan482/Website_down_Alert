import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./DashboardPage.css";

import {
  fetchWebsites,
  createWebsite,
  deleteWebsite,
} from "../api/websites";

import { Pie } from "react-chartjs-2";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
} from "chart.js";

ChartJS.register(ArcElement, Tooltip, Legend);

export default function DashboardPage() {
  const navigate = useNavigate();   // ✅ correct place

  const [websites, setWebsites] = useState([]);
  const [loading, setLoading] = useState(false);
  const [ setLastRefresh] = useState(null);

  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [email, setEmail] = useState("");
  const [intervalSec, setIntervalSec] = useState("60");
  const [sslDaysBefore, setSslDaysBefore] = useState("");

  const [showConfirm, setShowConfirm] = useState(false);
  const [deleteId, setDeleteId] = useState(null);

  // ================= LOAD WEBSITES =================
  async function loadWebsites() {
    try {
      setLoading(true);
      const data = await fetchWebsites();
      setWebsites(data || []);
      setLastRefresh(new Date());
    } catch (err) {
      console.error("Refresh error:", err);
    } finally {
      setLoading(false);
    }
  }

  // ================= INIT + AUTO REFRESH =================
  useEffect(() => {
    loadWebsites();

    const timer = setInterval(() => {
      loadWebsites();
    }, 15000);

    return () => clearInterval(timer);
  }, []);

  // ================= ADD WEBSITE =================
  async function handleAddWebsite(e) {
    e.preventDefault();

    const payload = {
      name,
      url,
      email,
      check_interval: Number(intervalSec),
      ssl_alert_days_before: sslDaysBefore ? Number(sslDaysBefore) : null,
    };

    try {
      await createWebsite(payload);

      setName("");
      setUrl("");
      setEmail("");
      setIntervalSec("60");
      setSslDaysBefore("");

      loadWebsites();
    } catch (err) {
      console.error("Add error:", err);
    }
  }

  // ================= DELETE =================
  async function confirmDelete() {
    try {
      await deleteWebsite(deleteId);
      setShowConfirm(false);
      loadWebsites();
    } catch {
      console.log("Delete failed");
    }
  }

  // ================= LOGOUT =================
  function handleLogout() {
    localStorage.removeItem("token");
    navigate("/");
  }

  // ================= STATUS =================
  const totalCount = websites.length;
  const upCount = websites.filter((w) => w.last_status === "UP").length;
  const downCount = websites.filter((w) => w.last_status === "DOWN").length;

  const pieData = {
    labels: ["UP Websites", "DOWN Websites"],
    datasets: [
      {
        data: [upCount, downCount],
        backgroundColor: ["#22c55e", "#ef4444"],
        borderWidth: 0,
      },
    ],
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-container">

        {/* HEADER */}
        <header className="dashboard-header">
          <div className="brand">
            <div className="logo">WM</div>
            <div>
              <h1>Website Monitor</h1>
              <p>Live status • Uptime • SSL expiry</p>
            </div>
          </div>

          <div className="header-actions">
           <div className="refresh-info">
  <button
    onClick={loadWebsites}
    className="refresh-btn"
    disabled={loading}
  >
    {loading ? "Refreshing..." : "Refresh"}
  </button>
</div>


            <button onClick={handleLogout} className="logout-btn">
              Logout
            </button>
          </div>
        </header>

        <div className="dashboard-grid">

          {/* LEFT */}
          <div className="left-panel">

            {/* ADD FORM */}
            <div className="card add-card">
              <h2>Add Website</h2>

              <form onSubmit={handleAddWebsite}>
                <input placeholder="Website Name" value={name}
                  onChange={(e) => setName(e.target.value)} required />

                <input placeholder="https://example.com" value={url}
                  onChange={(e) => setUrl(e.target.value)} required />

                <input placeholder="Alert Email" value={email}
                  onChange={(e) => setEmail(e.target.value)} required />

                <div className="row">
                  <input placeholder="Interval (sec)" value={intervalSec}
                    onChange={(e) => setIntervalSec(e.target.value)} required />

                  <input placeholder="SSL days before" value={sslDaysBefore}
                    onChange={(e) => setSslDaysBefore(e.target.value)} />
                </div>

                <button className="primary-btn">Add Website</button>
              </form>
            </div>

            {/* TABLE */}
            <div className="card add-card">
              <h2>Monitored Websites</h2>

              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>URL</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>

                <tbody>
                  {websites.length === 0 ? (
                    <tr>
                      <td colSpan="4" style={{ textAlign: "center", color: "#94a3b8" }}>
                        No websites added yet
                      </td>
                    </tr>
                  ) : (
                    websites.map((w) => (
                      <tr
                        key={w.id}
                        style={{ cursor: "pointer" }}
                        onClick={() => navigate(`/charts/${w.id}`)}   // ✅ navigation
                      >
                        <td>{w.name}</td>
                        <td>{w.url}</td>
                        <td>{w.last_status}</td>
                        <td>
                          <button
                            className="delete-btn"
                            onClick={(e) => {
                              e.stopPropagation();   // ❗ row click prevent
                              setDeleteId(w.id);
                              setShowConfirm(true);
                            }}
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* RIGHT STATUS */}
          <div className="right-panel card status-panel">
            <h2>Websites Status</h2>
            <p className="status-subtitle">Live monitoring overview</p>

            <div className="status-grid">
              <div className="status-tile total">
                <span>Total Websites</span>
                <h1>{totalCount}</h1>
              </div>

              <div className="status-tile up">
                <span>UP Websites</span>
                <h1>{upCount}</h1>
              </div>

              <div className="status-tile down">
                <span>DOWN Websites</span>
                <h1>{downCount}</h1>
              </div>
            </div>

            <div className="chart-wrapper">
              <Pie data={pieData} />
            </div>
          </div>
        </div>
      </div>

      {/* CONFIRM DELETE MODAL */}
      {showConfirm && (
        <div className="confirm-overlay">
          <div className="confirm-box">
            <h3>Delete Website?</h3>
            <p>Are you sure you want to delete this website?</p>

            <div className="confirm-actions">
              <button className="cancel-btn" onClick={() => setShowConfirm(false)}>
                Cancel
              </button>

              <button className="confirm-btn" onClick={confirmDelete}>
                Yes, Delete
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
