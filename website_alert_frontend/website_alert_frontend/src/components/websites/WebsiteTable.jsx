export default function WebsiteTable({ websites, onDelete }) {
  if (!websites || websites.length === 0) {
    return <p>No websites added yet.</p>;
  }

  return (
    <table style={styles.table}>
      <thead>
        <tr>
          <th>Name</th>
          <th>URL</th>
          <th>Status</th>
          <th>Uptime %</th>
          <th>Last Checked</th>
          <th>SSL Days Left</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {websites.map((site) => (
          <tr key={site.id}>
            <td>{site.name}</td>
            <td>{site.url}</td>
            <td>{site.status}</td>
            <td>
              {typeof site.uptime === "number"
                ? site.uptime.toFixed(1)
                : site.uptime ?? "-"}
            </td>
            <td>
              {site.last_checked
                ? new Date(site.last_checked).toLocaleString()
                : "-"}
            </td>
            <td>{site.ssl_days_left ?? "-"}</td>
            <td>
              <button
                style={styles.deleteBtn}
                onClick={() => onDelete && onDelete(site.id)}
              >
                Delete
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

const styles = {
  table: {
    width: "100%",
    borderCollapse: "collapse",
    background: "white",
    borderRadius: "8px",
    overflow: "hidden",
    boxShadow: "0 2px 8px rgba(0,0,0,0.08)",
  },
  deleteBtn: {
    padding: "6px 10px",
    border: "none",
    borderRadius: "4px",
    background: "#e53935",
    color: "white",
    cursor: "pointer",
    fontSize: "12px",
  },
};
