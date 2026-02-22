import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import "./LoginPage.css";

const API_BASE_URL = "http://localhost:8000";

function extractToken(data) {
  return data?.access_token || data?.token || null;
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export default function LoginPage() {
  const navigate = useNavigate();

  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState(null);
  const [noticeType, setNoticeType] = useState("");

  // 🔥 clear old message on screen change
  useEffect(() => {
    setNotice(null);
    setNoticeType("");
  }, [mode]);

  // ================= LOGIN =================
  async function handleLogin(e) {
    e.preventDefault();

    if (!username || !password) {
      setNotice("Please fill all fields");
      setNoticeType("error");
      return;
    }

    try {
      setLoading(true);
      const res = await axios.post(`${API_BASE_URL}/auth/login`, {
        username,
        password,
      });

      const token = extractToken(res.data);
      if (!token) throw new Error();

      localStorage.setItem("token", token);
      navigate("/dashboard");
    } catch (err) {
      const msg = err?.response?.data?.detail?.toLowerCase() || "";

      if (msg.includes("username")) {
        setNotice("Username incorrect");
      } else if (msg.includes("password")) {
        setNotice("Password incorrect");
      } else {
        setNotice("Invalid username or password");
      }

      setNoticeType("error");
    } finally {
      setLoading(false);
    }
  }

  // ================= REGISTER =================
  async function handleRegister(e) {
  e.preventDefault();

  if (!username || !password || !email) {
    setNotice("Please fill all fields");
    setNoticeType("error");
    return;
  }

  if (!isValidEmail(email)) {
    setNotice("Enter valid email address");
    setNoticeType("error");
    return;
  }

  try {
    setLoading(true);
    const res = await axios.post(`${API_BASE_URL}/auth/create`, {
      username,
      password,
      email,
    });

    const token = extractToken(res.data);
    localStorage.setItem("token", token);
    navigate("/dashboard");
  } catch (err) {
    const msg = err?.response?.data?.detail?.toLowerCase() || "";

    if (msg.includes("username")) {
      setNotice("Username already exists. Please choose another username.");
    } 
    else if (msg.includes("email")) {
      setNotice("Email already registered. Please use a different email.");
    } 
    else {
      setNotice("Account creation failed. Please try again.");
    }

    setNoticeType("error");
  } finally {
    setLoading(false);
  }
}


  // ================= FORGOT PASSWORD =================
  async function handleSendOtp(e) {
  e.preventDefault();

  if (!email) {
    setNotice("Please enter registered email");
    setNoticeType("error");
    return;
  }

  if (!isValidEmail(email)) {
    setNotice("Enter valid email address");
    setNoticeType("error");
    return;
  }

  try {
    setLoading(true);

    await axios.post(`${API_BASE_URL}/auth/forgot-password`, { email });

    // ✅ SUCCESS CONFIRMATION
    setNotice("OTP sent successfully. Please check your email.");
    setNoticeType("success");

    // small delay so user can SEE message
    setTimeout(() => {
      setMode("reset");
    }, 800);

  } catch (err) {
    const msg = err?.response?.data?.detail?.toLowerCase() || "";

    if (msg.includes("email")) {
      setNotice("Email not registered. Please enter a valid email.");
    } else {
      setNotice("OTP send failed. Please try again.");
    }

    setNoticeType("error");
  } finally {
    setLoading(false);
  }
}


  // ================= RESET PASSWORD =================
  async function handleResetPassword(e) {
    e.preventDefault();

    if (!otp || !newPassword || !confirmPassword) {
      setNotice("Please fill all fields");
      setNoticeType("error");
      return;
    }

    if (newPassword !== confirmPassword) {
      setNotice("Passwords do not match");
      setNoticeType("error");
      return;
    }

    try {
      setLoading(true);
      await axios.post(`${API_BASE_URL}/auth/reset-password`, {
        email,
        otp,
        new_password: newPassword,
        confirm_password: confirmPassword,
      });

      setNotice("Password reset successful. Please login.");
      setNoticeType("success");
      setMode("login");
    } catch {
      setNotice("Invalid OTP");
      setNoticeType("error");
    } finally {
      setLoading(false);
    }
  }

  // ================= UI =================
  return (
    <div className="auth-bg">
      <div className="auth-card card-center">
        <h2 className="projectName">
          Website Monitor And SSL Alert System
        </h2>

        <h1 className="title">
          {mode === "login" && "Login"}
          {mode === "register" && "Create Account"}
          {mode === "forgot" && "Forgot Password"}
          {mode === "reset" && "Reset Password"}
        </h1>

        {notice && <div className={`notice ${noticeType}`}>{notice}</div>}

        <form>
          {(mode === "login" || mode === "register") && (
            <>
              <input
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
              <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </>
          )}

          {mode === "register" && (
            <input
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          )}

          {mode === "forgot" && (
            <input
              placeholder="Registered Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          )}

          {mode === "reset" && (
            <>
              <input
                placeholder="OTP"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
              />
              <input
                type="password"
                placeholder="New Password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
              <input
                type="password"
                placeholder="Confirm Password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </>
          )}

          {mode === "login" && (
            <button onClick={handleLogin} disabled={loading}>
              {loading ? "Logging in..." : "Login"}
            </button>
          )}

          {mode === "register" && (
            <button onClick={handleRegister} disabled={loading}>
              {loading ? "Creating..." : "Create Account"}
            </button>
          )}

          {mode === "forgot" && (
            <button onClick={handleSendOtp} disabled={loading}>
              {loading ? "Sending..." : "Send OTP"}
            </button>
          )}

          {mode === "reset" && (
            <button onClick={handleResetPassword} disabled={loading}>
              {loading ? "Resetting..." : "Reset Password"}
            </button>
          )}

          {mode === "login" && (
            <>
              <p onClick={() => setMode("register")}>Create Account</p>
              <p onClick={() => setMode("forgot")}>Forgot Password?</p>
            </>
          )}

          {mode !== "login" && (
            <p onClick={() => setMode("login")}>Back to Login</p>
          )}
        </form>
      </div>
    </div>
  );
}
