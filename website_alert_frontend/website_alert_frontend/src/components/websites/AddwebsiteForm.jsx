import { useState } from "react";
import { createWebsite } from "../../api/websites";

export default function AddWebsiteForm({ onAdded }) {
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [email, setEmail] = useState("");
  const [checkInterval, setCheckInterval] = useState("60");
  const [sslAlertDays, setSslAlertDays] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const payload = {
        name,
        url,
        email,
        check_interval: checkInterval,
      };

      if (sslAlertDays) {
        payload.ssl_alert_days_before = sslAlertDays;
      }

      await createWebsite(payload);

      // clear form
      setName("");
      setUrl("");
      setEmail("");
      setCheckInterval("60");
      setSslAlertDays("");

      if (onAdded) onAdded(); // dashboard-ku "reload" signal
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail || "Failed to add website."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <h3>Add Website</h3>

      <input
        type="text"
        placeholder="Website Name"
        value={name}
        onChange={(e) => setName(e.target.value)}
        style={styles.input}
        required
      />

      <input
        type="url"
        placeholder="https://example.com"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        style={styles.input}
        required
      />

      <input
        type="email"
        placeholder="Alert Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        style={styles.input}
        required
      />

      <input
        type="number"
        placeholder="Check interval (seconds)"
        value={checkInterval}
        onChange={(e) => setCheckInterval(e.target.value)}
        style={styles.input}
        min="10"
      />

      <input
        type="number"
        placeholder="SSL alert days before (optional)"
        value={sslAlertDays}
        onChange={(e) => setSslAlertDays(e.target.value)}
        style={styles.input}
        min="1"
      />

      {error && <p style={styles.error}>{error}</p>}

      <button type="submit" style={styles.button} disabled={loading}>
        {loading ? "Adding..." : "Add Website"}
      </button>
    </form>
  );
}

const styles = {
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
    padding: "16px",
    background: "white",
    borderRadius: "8px",
    boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
    maxWidth: "420px",
  },
  input: {
    padding: "8px 10px",
    fontSize: "14px",
  },
  button: {
    padding: "10px",
    fontSize: "14px",
    border: "none",
    borderRadius: "6px",
    background: "#1a73e8",
    color: "white",
    cursor: "pointer",
  },
  error: {
    color: "red",
    fontSize: "13px",
  },
};
