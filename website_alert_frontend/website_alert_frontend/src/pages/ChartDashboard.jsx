import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { fetchWebsiteHistory } from "../api/websites";
import "./ChartDashboard.css";

import { Line, Doughnut } from "react-chartjs-2";
import {
  Chart as ChartJS,
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
  ArcElement,
} from "chart.js";

/* REGISTER */
ChartJS.register(
  LineElement,
  PointElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
  ArcElement
);

export default function ChartDashboard() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [history, setHistory] = useState([]);
  const [website, setWebsite] = useState(null);
  const [loading, setLoading] = useState(true);

  /* ================= INITIAL LOAD ================= */
  async function loadWebsite() {
    try {
      setLoading(true);
      const data = await fetchWebsiteHistory(id);
      setWebsite(data.website);
      setHistory(data.history || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadWebsite();
  }, [id]);

  /* ================= REAL-TIME CHART UPDATE ================= */
  useEffect(() => {
    if (!website?.check_interval) return;

    const t = setInterval(async () => {
      try {
        const data = await fetchWebsiteHistory(id);
        if (!data.history?.length) return;

        const latest = data.history[data.history.length - 1];

        setHistory(prev => {
          if (!prev.length) return [latest];

          const last = prev[prev.length - 1];
          if (last.checked_at === latest.checked_at) {
            return prev; // 🔒 duplicate prevent
          }

          return [...prev, latest];
        });
      } catch (e) {
        console.error(e);
      }
    }, website.check_interval * 1000);

    return () => clearInterval(t);
  }, [website?.check_interval, id]);

  /* ================= METRICS ================= */
  const total = history.length;
  const success = history.filter(h => h.status === "UP").length;
  const uptime = total ? Math.round((success / total) * 100) : 0;

  const lastCheck = history.at(-1);
  const isDown = lastCheck?.status === "DOWN";

  /* ================= ALERT DATE ================= */
  let nextAlertDate = "Not scheduled";
  if (website?.ssl_expiry_date && website?.ssl_alert_days_before != null) {
    const d = new Date(website.ssl_expiry_date);
    d.setDate(d.getDate() - website.ssl_alert_days_before);
    nextAlertDate = d.toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });
  }

  /* ================= LINE CHART DATA ================= */
  const lastTen = history
    .filter(h => h.response_time !== null)
    .slice(-10);
const nowTime = new Date();

const lineData = {
  labels: lastTen.map((_, i) => {
    const d = new Date(nowTime);

    // 🔥 force last label = CURRENT SYSTEM TIME
    d.setMinutes(
      nowTime.getMinutes() - (lastTen.length - 1 - i)
    );

    return d.toLocaleTimeString("en-IN", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: false, // ✅ railway time
    });
  }),

  datasets: [
    {
      label: "Response Time (ms)",
      data: lastTen.map(h => Math.round(h.response_time)),
      borderColor: isDown ? "#ef4444" : "#22c55e",
backgroundColor: isDown
  ? "rgba(239,68,68,0.15)"
  : "rgba(34,197,94,0.15)",
      borderWidth: 3,
      tension: 0.4,
      pointRadius: 5,
      pointHoverRadius: 7,
      fill: false,
    },
  ],
};

  const lineOptions = {
    responsive: true,
    maintainAspectRatio: false,
    animation: false, // 🔥 no page refresh feel
    plugins: {
      legend: { labels: { color: "#e5e7eb" } },
      tooltip: {
        callbacks: {
          label: ctx => `${ctx.raw} ms`,
        },
      },
    },
    scales: {
      x: {
        ticks: { color: "#94a3b8" },
        grid: { display: false },
      },
      y: {
        beginAtZero: true,
        ticks: {
          color: "#94a3b8",
          callback: v => `${v} ms`,
        },
        grid: {
          color: "rgba(148,163,184,0.15)",
        },
      },
    },
  };

  /* ================= DONUTS ================= */
  const uptimeDonut = {
    datasets: [
      {
        data: [uptime, 100 - uptime],
        backgroundColor: ["#22c55e", "#1e293b"],
        borderWidth: 0,
        cutout: "75%",
      },
    ],
  };

  const sslPercent = website?.ssl_days_left
    ? Math.min(100, Math.round((website.ssl_days_left / 365) * 100))
    : 0;

  const sslDonut = {
    datasets: [
      {
        data: [sslPercent, 100 - sslPercent],
        backgroundColor: [
          website?.ssl_days_left < 30 ? "#ef4444" : "#38bdf8",
          "#1e293b",
        ],
        borderWidth: 0,
        cutout: "75%",
      },
    ],
  };

  /* ================= UI ================= */
  return (
    <div className="chart-page">
      <div className="chart-container">
        <div className="chart-header">
          <h1>Website Monitoring</h1>
          <button className="back-btn" onClick={() => navigate("/dashboard")}>
            ⬅ BACK
          </button>
        </div>

        {loading ? (
          <p className="loading-text">Loading...</p>
        ) : !website ? (
          <p className="loading-text">Website not found</p>
        ) : (
          <>
            {/* STATUS CARD */}
            <div className={`chart-card status-card ${isDown ? "down" : "up"}`}>
              <div className="status-row">
                <h2>{website.name}</h2>
                <span className={`status-badge ${isDown ? "down" : "up"}`}>
                  {isDown ? "DOWN" : "UP"}
                </span>
              </div>

              <div className="info-grid">
                <div>
                  <span>Website URL</span>
                  <a href={website.url}>{website.url}</a>
                </div>
                <div><span>Alert Email</span>{website.email}</div>
                <div><span>Interval</span>{website.check_interval} sec</div>
                <div><span>Next Alert Mail</span>{nextAlertDate}</div>
                <div><span>Alert Before</span>{website.ssl_alert_days_before} days</div>
                <div>
                  <span>SSL Expiry</span>
                  {new Date(website.ssl_expiry_date).toLocaleDateString("en-IN")}
                </div>
              </div>
            </div>

            {/* LINE CHART */}
            <div className="chart-card">
              <h3>Response Time (Last 10 Checks)</h3>
              <p className="chart-subtitle">Real-time backend monitoring (1 seconds = 1000 millisecond)</p>

              <div style={{ height: "320px" }}>
                <Line data={lineData} options={lineOptions} />
              </div>
            </div>

            {/* DONUT STATS */}
           <div className="stats-grid">
  {/* ===== UPTIME ===== */}
  <div className="stat-box donut-wrap">
    <Doughnut data={uptimeDonut} />
    <div className="donut-center">
      <span className="donut-value green">{uptime}%</span>
      <span className="donut-label">Uptime</span>
    </div>
  </div>

  {/* ===== SSL ===== */}
  <div className="stat-box donut-wrap">
    <Doughnut data={sslDonut} />
    <div className="donut-center">
      <span
        className={`donut-value ${
          website.ssl_days_left < 30 ? "red" : "blue"
        }`}
      >
        {website.ssl_days_left}
      </span>
      <span className="donut-label">SSL Days</span>
    </div>
  </div>
</div>

          </>
        )}
      </div>
    </div>
  );
}
