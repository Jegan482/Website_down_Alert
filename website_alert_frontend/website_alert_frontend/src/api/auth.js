// src/api/auth.js
import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

// ================= LOGIN =================
export async function loginUser(username, password) {
  const resp = await axios.post(`${API_BASE_URL}/auth/login`, {
    username,
    password,
  });

  console.log("🔁 Raw login response from backend:", resp.data);
  return resp.data; // { message, user, token }
}

// ================= REGISTER =================
export async function registerUser(payload) {
  const resp = await axios.post(
    `${API_BASE_URL}/auth/create`,
    payload,
    {
      headers: {
        "Content-Type": "application/json",
      },
    }
  );

  return resp.data;
}