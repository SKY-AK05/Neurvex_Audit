// In production (single container), nginx proxies /api/* to the backend.
// In local dev, set VITE_API_BASE in frontend/.env to http://localhost:7071/api
const API_BASE = import.meta.env.VITE_API_BASE || "/api";

function getAuthHeaders() {
  const headers = {};
  const token = sessionStorage.getItem("nd_auth_token");
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse(res) {
  if (res.status === 401) {
    // Clear session and redirect to login if unauthorized
    sessionStorage.removeItem("nd_auth");
    sessionStorage.removeItem("nd_auth_token");
    sessionStorage.removeItem("nd_user_name");
    sessionStorage.removeItem("nd_role");
    window.location.href = "/portal";
    throw new Error("Session expired. Please log in again.");
  }
  
  if (!res.ok) {
    let errorMsg = "Request failed";
    try {
      const data = await res.clone().json();
      errorMsg = data.error || errorMsg;
    } catch (e) {
      // Ignore JSON parse errors for non-JSON error responses
    }
    throw new Error(errorMsg);
  }
  return res.json();
}

export async function getSubmissions() {
  const res = await fetch(`${API_BASE}/submissions`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function getSubmission(id) {
  const res = await fetch(`${API_BASE}/submissions/${id}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function submitAudit(data) {
  const headers = { "Content-Type": "application/json" };
  const token = localStorage.getItem("org_token");
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}/submit`, {
    method: "POST",
    headers,
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

export async function saveEmail(id, emailBody) {
  const res = await fetch(`${API_BASE}/submissions/${id}/email`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ email_body: emailBody }),
  });
  return handleResponse(res);
}

export async function sendEmail(id) {
  const res = await fetch(`${API_BASE}/submissions/${id}/send`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function regenerateEmail(id) {
  const res = await fetch(`${API_BASE}/submissions/${id}/regenerate-email`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function getSettings() {
  const res = await fetch(`${API_BASE}/settings`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function saveSettings(data) {
  const res = await fetch(`${API_BASE}/settings`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

export async function submitSupportRequest(data) {
  const res = await fetch(`${API_BASE}/support`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

export async function toggleNotifications() {
  const res = await fetch(`${API_BASE}/settings/notifications/toggle`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}
