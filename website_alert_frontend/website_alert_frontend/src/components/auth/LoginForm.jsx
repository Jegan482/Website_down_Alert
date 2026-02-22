import { useState } from "react";
import { loginUser } from "../../api/auth";

export default function LoginForm({ onSuccess }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const data = await loginUser(username, password);

      // expect: { access_token, token_type }
      if (data.access_token) {
        localStorage.setItem("token", data.access_token);
        onSuccess && onSuccess(data);
      } else {
        setError("Login failed. Invalid response.");
      }
    } catch (err) {
      console.error(err);
      setError("Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} style={styles.form}>
      <h2>Login</h2>

      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        style={styles.input}
        required
      />

      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        style={styles.input}
        required
      />

      {error && <p style={styles.error}>{error}</p>}

      <button type="submit" style={styles.button} disabled={loading}>
        {loading ? "Logging in..." : "Login"}
      </button>
    </form>
  );
}

const styles = {
  form: {
    width: "320px",
    margin: "100px auto",
    display: "flex",
    flexDirection: "column",
    gap: "10px",
    padding: "24px 28px",
    borderRadius: "12px",
    background: "white",
    boxShadow: "0 10px 30px rgba(0,0,0,0.1)",
  },
  input: {
    padding: "10px",
    fontSize: "15px",
  },
  button: {
    padding: "10px",
    fontSize: "15px",
    border: "none",
    cursor: "pointer",
    background: "#1a73e8",
    color: "white",
    borderRadius: "6px",
  },
  error: {
    color: "red",
    fontSize: "14px",
  },
};
