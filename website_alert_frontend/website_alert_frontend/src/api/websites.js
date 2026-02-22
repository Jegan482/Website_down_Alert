// src/api/websites.js
import axios from "axios";

const API_BASE_URL = "http://localhost:8000"; // backend URL

// 🔐 Auth header helper
function authHeaders() {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ================= GET all websites (current user) =================
export async function fetchWebsites() {
  const resp = await axios.get(
    `${API_BASE_URL}/websites/user_get`,
    {
      headers: authHeaders(),
    }
  );

  console.log("🌐 fetchWebsites resp:", resp.data);
  return resp.data;
}

// ================= CREATE website =================
export async function createWebsite(payload) {
  console.log("➕ createWebsite payload:", payload);

  const resp = await axios.post(
    `${API_BASE_URL}/websites/user_post`,
    payload,
    {
      headers: {
        ...authHeaders(),
        "Content-Type": "application/json",
      },
    }
  );

  console.log("✅ createWebsite resp:", resp.data);
  return resp.data;
}

// ================= DELETE website =================
export async function deleteWebsite(id) {
  const resp = await axios.delete(
    `${API_BASE_URL}/websites/${id}`,
    {
      headers: authHeaders(),
    }
  );

  console.log("🗑 deleteWebsite resp:", resp.data);
  return resp.data;
}

// ================= WEBSITE HISTORY =================
export async function fetchWebsiteHistory(id) {
  const resp = await axios.get(
    `${API_BASE_URL}/websites/${id}/history`,
    {
      headers: authHeaders(),
    }
  );

  return resp.data;
}
