// In production (single container), nginx proxies /api/* to the backend.
// In local dev, set VITE_API_BASE in frontend/.env to http://localhost:7071/api
const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export function getAuthHeaders() {
  const headers = {};
  const token = sessionStorage.getItem("nd_auth_token");
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse(res) {
  if (res.status === 401) {
    const detail = await res.clone().json().catch(() => ({}));
    sessionStorage.setItem(
      "nd_auth_error",
      detail.detail || "Session expired or token rejected. Sign in again."
    );
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
      // FastAPI returns {"detail": "..."}, custom errors use {"error": "..."}
      errorMsg = data.error || data.detail || errorMsg;
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

export async function getSubmissionStatus(id) {
  const headers = {};
  const token = localStorage.getItem("org_token");
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}/submissions/${id}/status`, {
    headers: { ...headers, ...getAuthHeaders() },
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

export async function getRateLimitSettings() {
  const res = await fetch(`${API_BASE}/manage/settings/rate-limits`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function updateRateLimitSettings(data) {
  const res = await fetch(`${API_BASE}/manage/settings/rate-limits`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

export async function resetRateLimitSettings() {
  const res = await fetch(`${API_BASE}/manage/settings/rate-limits/reset`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function deleteAllRecords(payload) {
  const body = typeof payload === "string"
    ? { confirmation: payload, password: payload }
    : { confirmation: "DELETE ALL SUBMISSIONS", ...payload };
  const res = await fetch(`${API_BASE}/settings/delete-all-records`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify(body),
  });
  return handleResponse(res);
}

export async function updateRespondent(id, data) {
  const res = await fetch(`${API_BASE}/submissions/${id}/respondent`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

export async function updateSubmissionScores(id, scores) {
  const res = await fetch(`${API_BASE}/submissions/${id}/scores`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify(scores),
  });
  return handleResponse(res);
}

export async function reassignSubmissionOrganisation(id, organizationId, reason = "") {
  const res = await fetch(`${API_BASE}/submissions/${id}/organisation`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ 
      organization_id: organizationId,
      reason: reason 
    }),
  });
  return handleResponse(res);
}

export async function filterSubmissions(payload) {
  const res = await fetch(`${API_BASE}/submissions/filter`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

export async function getSavedFilters() {
  const res = await fetch(`${API_BASE}/submissions/saved-filters`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function createSavedFilter(data) {
  const res = await fetch(`${API_BASE}/submissions/saved-filters`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeaders(),
    },
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

export async function deleteSavedFilter(filterId) {
  const res = await fetch(`${API_BASE}/submissions/saved-filters/${filterId}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

// ---------------------------------------------------------------------------
// Dual Assessment Entry & Organisation Management APIs
// ---------------------------------------------------------------------------

export async function validateOrganisationByName(name) {
  const res = await fetch(`${API_BASE}/public/organisations/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  return handleResponse(res);
}

export async function validateCorporateEmail(email) {
  const res = await fetch(`${API_BASE}/public/email/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  return handleResponse(res);
}

export async function resolveAssessmentLink(token) {
  const res = await fetch(`${API_BASE}/public/assessment/resolve-link`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  return handleResponse(res);
}

export async function resolveLegacyOrgLink(org) {
  const res = await fetch(`${API_BASE}/public/assessment/resolve-legacy-org`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ org }),
  });
  return handleResponse(res);
}

export async function validateInvitation(token) {
  const res = await fetch(`${API_BASE}/public/invitations/validate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
  return handleResponse(res);
}

export async function createOrganisation(name) {
  const res = await fetch(`${API_BASE}/manage/orgs`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ name }),
  });
  return handleResponse(res);
}

export async function updateOrganisation(id, name) {
  const res = await fetch(`${API_BASE}/manage/orgs/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ name }),
  });
  return handleResponse(res);
}

export async function toggleOrganisationStatus(id, isActive) {
  const res = await fetch(`${API_BASE}/manage/orgs/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ is_active: isActive }),
  });
  return handleResponse(res);
}

export async function deleteOrganisation(id) {
  const res = await fetch(`${API_BASE}/manage/orgs/${id}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function getOrgInvitations(orgId) {
  const res = await fetch(`${API_BASE}/manage/orgs/${orgId}/invitations`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function createOrgInvitation(orgId, data) {
  const res = await fetch(`${API_BASE}/manage/orgs/${orgId}/invitations`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(data),
  });
  return handleResponse(res);
}

export async function getOrgDefaultAssessmentLink(orgId) {
  const res = await fetch(`${API_BASE}/manage/orgs/${orgId}/assessment-links/default`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function revokeOrgInvitation(invId) {
  const res = await fetch(`${API_BASE}/manage/orgs/invitations/${invId}/revoke`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function regenerateOrgInvitation(invId) {
  const res = await fetch(`${API_BASE}/manage/orgs/invitations/${invId}/regenerate`, {
    method: "POST",
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}



export async function getOrganisations(includeDeleted = false) {
  const params = includeDeleted ? '?include_deleted=true' : '';
  const res = await fetch(`${API_BASE}/manage/orgs${params}`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}
