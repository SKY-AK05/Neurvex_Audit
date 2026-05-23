// In production (single container), nginx proxies /api/* to the backend.
// In local dev, set VITE_API_BASE in frontend/.env to http://localhost:7071/api
const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export async function getSubmissions() {
  const res = await fetch(`${API_BASE}/submissions`);
  if (!res.ok) throw new Error("Failed to fetch submissions");
  return res.json();
}

export async function getSubmission(id) {
  const res = await fetch(`${API_BASE}/submissions/${id}`);
  if (!res.ok) throw new Error("Failed to fetch submission");
  return res.json();
}

export async function submitAudit(data) {
  const res = await fetch(`${API_BASE}/submit`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || "Submission failed");
  return json;
}

export async function saveEmail(id, emailBody) {
  const res = await fetch(`${API_BASE}/submissions/${id}/email`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email_body: emailBody }),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || "Save failed");
  return json;
}

export async function sendEmail(id) {
  const res = await fetch(`${API_BASE}/submissions/${id}/send`, {
    method: "POST",
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || "Send failed");
  return json;
}

export async function regenerateEmail(id) {
  const res = await fetch(`${API_BASE}/submissions/${id}/regenerate-email`, {
    method: "POST",
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || "Regeneration failed");
  return json;
}

export async function getSettings() {
  const res = await fetch(`${API_BASE}/settings`);
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || "Failed to load settings");
  return json;
}

export async function saveSettings(data) {
  const res = await fetch(`${API_BASE}/settings`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || "Failed to save settings");
  return json;
}

export async function submitSupportRequest(data) {
  const res = await fetch(`${API_BASE}/support`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || "Failed to send support request");
  return json;
}

export async function toggleNotifications() {
  const res = await fetch(`${API_BASE}/settings/notifications/toggle`, {
    method: "POST",
  });
  const json = await res.json();
  if (!res.ok) throw new Error(json.error || "Failed to toggle notifications");
  return json;
}
