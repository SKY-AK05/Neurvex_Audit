# Vue 3 Single Page Application & User Interface

> Unit `09-frontend` · kind: feature

## Summary

Interactive 40-question survey workflow, auto-save drafts, executive radar dashboards, and admin management console.

## Context & goal

The Frontend unit delivers the client-side experience of NIWI. Built with Vue 3 (Composition API), Vite, Pinia, and Vue Router, it features a progressive multi-step assessment form, auto-save to local storage and server drafts, dynamic organization lookups, 8-pillar radar visualizations, and an administrative control panel.

## User stories

- As an Audit Respondent, I complete the survey through an accessible, step-by-step form that saves my progress automatically.
- As an HR Executive, I view interactive radar charts comparing our department scores to industry benchmarks.
- As an Orchvate Administrator, I manage client organizations, inspect individual submissions, and monitor system queues.

## Functional requirements

- 1. Progressive Multi-Step Survey [confirmed]: Guide respondents through 8 pillar sections with clear progress indicators.
- 2. Auto-Save Drafts [confirmed]: Debounce form changes (2 seconds) and persist partial progress to server drafts and browser storage.
- 3. Dynamic Organization Validation [confirmed]: Auto-complete and validate employer organizations against public API.
- 4. Interactive Radar & Bar Charts [confirmed]: Render 8-pillar inclusion profiles using SVG/Chart.js visualizations.
- 5. Design System Conformance [confirmed]: Adhere strictly to color tokens, typography, and WCAG 2.1 AA accessibility guidelines.


## Interfaces & data

Communicates with backend via Axios API client (`frontend/src/api.js`).
Consumes design tokens from `frontend/src/style.css` (see [DESIGN-SYSTEM.md](../../architecture/DESIGN-SYSTEM.md)).

## Acceptance criteria

- Given a respondent filling out questions, When they pause for 2 seconds, Then a draft save request is automatically dispatched in the background.
- Given a respondent navigating using keyboard only, When pressing Tab and Arrow keys, Then all Likert options are selectable without mouse interaction.
- Given a submission completion, When acknowledged by backend, Then the view transitions to a celebration and instant score summary screen.

## Edge cases & failure modes

- **Browser offline during audit:** Form data persists in localStorage; banner alerts user and prompts re-sync once internet connectivity returns.

## Definition of done

- All functional requirements implemented and verified against code.
- All acceptance scenarios verified with passing unit or integration tests.
- Zero unresolved callouts, placeholders, or ambiguous specifications.
- Security and authorization policies strictly enforced.
- Performance and error recovery verified under edge conditions.

## Improvements & enhancements

- Migrate JavaScript components to TypeScript with strict prop checking.
- Implement PWA service worker for offline assessment caching.


## Source material

Key source for this unit (37 file(s) total, showing up to 15):

#### `frontend/src/App.vue`

```vue
<template>
  <div id="app-shell">
    <div v-if="isAdmin" class="admin-layout">
      <!-- High-End Sticky Top Navbar matching Reference Image -->
      <header class="top-navbar">
        <div class="topbar-inner">
          <!-- Logo & Brand on Left -->
          <router-link to="/admin/dashboard" class="topbar-brand" title="NIWI Admin Dashboard">
            <img src="/logonew.png" alt="NIWI" class="topbar-logo" />
            <span class="topbar-brand-title">NIWI</span>
          </router-link>

          <!-- Centered Primary Navigation Links -->
          <nav class="topbar-nav" aria-label="Main Navigation">
            <router-link to="/admin/dashboard" class="top-nav-link" :class="{ active: route.path === '/admin/dashboard' }" @mouseenter="prefetchDashboard">
              Dashboard
            </router-link>
            <router-link to="/admin/submissions" class="top-nav-link" :class="{ active: route.path.includes('submissions') }" @mouseenter="prefetchSubmissions">
              Submissions
            </router-link>
            <router-link to="/admin/analytics" class="top-nav-link" :class="{ active: route.path === '/admin/analytics' }">
              Analytics
            </router-link>
            <router-link to="/admin/organisations" class="top-nav-link" :class="{ active: route.path === '/admin/organisations' }" @mouseenter="prefetchOrganisations">
              Organisations
            </router-link>
            <router-link to="/admin/form-builder" class="top-nav-link" :class="{ active: route.path === '/admin/form-builder' }">
              Form Builder
            </router-link>
            <router-link v-if="isSuper" to="/admin/super-dashboard" class="top-nav-link" :class="{ active: route.path === '/admin/super-dashboard' }">
              Engine
            </router-link>
          </nav>

          <!-- Right Controls: Powered by, Notification Alerts, User Profile, Mobile Menu -->
          <div class="topbar-right">
            <div class="header-powered">
              <span class="powered-label">Powered by</span>
              <img src="/logo_orchvate.png" alt="Orchvate" class="powered-logo" />
            </div>

            <!-- Bell Alert -->
            <div class="bell-wrap" ref="bellWrap">
              <button
                type="button"
                class="icon-btn bell-btn"
                :class="{ 'bell-on': notificationsEnabled }"
                title="Submission email alerts"
                @click.stop="onBellClick"
                aria-label="Submission notifications"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
                <span v-if="notificationsEnabled" class="bell-badge"></span>
              </button>
              <div v-if="bellOpen" class="bell-popover">
                <p class="bell-pop-title">Submission alerts</p>
                <p class="bell-pop-text">
                  {{ notificationsEnabled
                    ? 'You will receive an email when a new audit is submitted.'
                    : 'Turn on to get emailed when someone submits an audit.' }}
                </p>
                <p v-if="notificationEmail" class="bell-pop-email">→ {{ notificationEmail }}</p>
                <p v-else class="bell-pop-warn">Add a notification email in Settings first.</p>
                <router-link to="/admin/settings" class="bell-pop-link" @click="bellOpen = false">
                  Email settings →
                </router-link>
                <p v-if="bellMsg" :class="['bell-pop-msg', bellMsgType]">{{ bellMsg }}</p>
              </div>
            </div>

            <!-- Profile Avatar & Popover -->
            <div class="profile-wrap" ref="profileWrap">
              <div
                class="avatar"
                @click.stop="profileOpen = !profileOpen"
                role="button"
                tabindex="0"
                aria-label="User profile menu"
                :aria-expanded="profileOpen"
              >
                {{ userInitials }}
              </div>
              <div v-if="profileOpen" class="profile-popover">
                <div class="profile-header">
                  <div class="profile-name">{{ userName }}</div>
                  <div class="profile-role">{{ isSuper ? 'Super Admin' : 'Admin' }}</div>
                </div>
                <router-link to="/admin/settings" class="profile-item" @click="profileOpen = false">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
                  Settings
                </router-link>
                <router-link v-if="isSuper" to="/admin/super-dashboard" class="profile-item" @click="profileOpen = false">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect><rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect><line x1="6" y1="6" x2="6.01" y2="6"></line><line x1="6" y1="18" x2="6.01" y2="18"></line></svg>
                  Platform Engine
                </router-link>
                <router-link v-if="isSuper" to="/admin/users" class="profile-item" @click="profileOpen = false">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                  User Management
                </router-link>
                <router-link to="/admin/support" class="profile-item" @click="profileOpen = false">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                  Support
                </router-link>
                <a href="#" class="profile-item logout-item" @click.prevent="logout(); profileOpen = false;">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
                  Sign Out
                </a>
              </div>
            </div>

            <!-- Hamburger Button for Mobile -->
            <button
              class="mobile-nav-toggle"
              @click="mobileNavOpen = !mobileNavOpen"
              aria-label="Toggle navigation menu"
              :aria-expanded="mobileNavOpen"
            >
              <svg v-if="!mobileNavOpen" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>
              <svg v-else width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            </button>
          </div>
        </div>

        <!-- Mobile Nav Menu Drawer -->
        <div v-if="mobileNavOpen" class="mobile-nav-menu">
          <router-link to="/admin/dashboard" class="mobile-nav-link" :class="{ active: route.path === '/admin/dashboard' }" @click="mobileNavOpen = false">
            Dashboard
          </router-link>
          <router-link to="/admin/submissions" class="mobile-nav-link" :class="{ active: route.path.includes('submissions') }" @click="mobileNavOpen = false">
            Submissions
          </router-link>
          <router-link to="/admin/analytics" class="mobile-nav-link" :class="{ active: route.path === '/admin/analytics' }" @click="mobileNavOpen = false">
            Analytics
          </router-link>
          <router-link to="/admin/organisations" class="mobile-nav-link" :class="{ active: route.path === '/admin/organisations' }" @click="mobileNavOpen = false">
            Organisations
          </router-link>
          <router-link to="/admin/form-builder" class="mobile-nav-link" :class="{ active: route.path === '/admin/form-builder' }" @click="mobileNavOpen = false">
            Form Builder
          </router-link>
          <router-link v-if="isSuper" to="/admin/super-dashboard" class="mobile-nav-link" :class="{ active: route.path === '/admin/super-dashboard' }" @click="mobileNavOpen = false">
            Engine
          </router-link>
          <div class="mobile-nav-divider"></div>
          <router-link to="/admin/settings" class="mobile-nav-link" @click="mobileNavOpen = false">
            Settings
          </router-link>
          <router-link v-if="isSuper" to="/admin/users" class="mobile-nav-link" @click="mobileNavOpen = false">
            User Management
          </router-link>
          <router-link to="/admin/support" class="mobile-nav-link" @click="mobileNavOpen = false">
            Support
          </router-link>
          <a href="#" class="mobile-nav-link mobile-logout" @click.prevent="logout(); mobileNavOpen = false;">
            Sign Out
          </a>
        </div>
      </header>

      <!-- Main Admin Content Area -->
      <main class="page-content">
        <router-view />
      </main>
    </div>

    <!-- Public / Non-Admin views -->
    <div v-else class="public-shell">
      <router-view />
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted, onBeforeUnmount } from "vue";
import { useRouter, useRoute } from "vue-router";
import { getSettings, toggleNotifications, getSubmissions, filterSubmissions, getOrganisations } from "./api";
import { getMsalInstance, clearMsalCache } from "./authConfig";

const prefetchCache = {};

function prefetchDashboard() {
  const now = Date.now();
  if (!prefetchCache['dash'] || now - prefetchCache['dash'] > 30000) {
    prefetchCache['dash'] = now;
    getSubmissions().catch(() => {});
  }
}

function prefetchSubmissions() {
  const now = Date.now();
  if (!prefetchCache['subs'] || now - prefetchCache['subs'] > 30000) {
    prefetchCache['subs'] = now;
    filterSubmissions({ page: 1, per_page: 10 }).catch(() => {});
  }
}

function prefetchOrganisations() {
  const now = Date.now();
  if (!prefetchCache['orgs'] || now - prefetchCache['orgs'] > 30000) {
    prefetchCache['orgs'] = now;
    getOrganisations().catch(() => {});
  }
}

const router = useRouter();
const route  = useRoute();

const isAdmin = computed(() =>
  sessionStorage.getItem("nd_auth") === "1" && route.path.startsWith("/admin") && route.path !== "/admin"
);

const isSuper = computed(() => sessionStorage.getItem("nd_role") === "super");

const userName = ref(sessionStorage.getItem("nd_user_name") || "Admin User");
const userInitials = computed(() => {
  const name = userName.value;
  if (!name) return "AD";
  const parts = name.trim().split(" ");
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
  return name.substring(0, 2).toUpperCase();
});

const pageTitles = {
  "/admin/dashboard":  "Overview",
  "/admin/submissions": "Submissions",
  "/admin/analytics":  "Analytics",
  "/admin/settings":   "Settings",
  "/admin/support":       "Support",
  "/admin/organisations": "Organisations",
};
const pageTitle = computed(() => pageTitles[route.path] || "NIWI – Neuro-Inclusive Workplace Index");

const notificationsEnabled = ref(false);
const notificationEmail = ref("");
const bellOpen = ref(false);
const bellWrap = ref(null);
const bellMsg = ref("");
const bellMsgType = ref("success");
const bellToggling = ref(false);

const profileOpen = ref(false);
const profileWrap = ref(null);
const mobileNavOpen = ref(false);

// Share audit link
const shareCopied = ref(false);
function copyAuditLink() {
  const url = import.meta.env.VITE_APP_URL || "https://NIWI.orchvate.in/";
  navigator.clipboard.writeText(url).then(() => {
    shareCopied.value = true;
    setTimeout(() => { shareCopied.value = false; }, 2000);
  });
}

async function loadNotificationSettings() {
  if (!isAdmin.value) return;
  try {
    const s = await getSettings();
    notificationsEnabled.value = !!s.notifications_enabled;
    notificationEmail.value = s.notification_email || "";
  } catch {
    /* settings table may not exist yet */
  }
}

watch(isAdmin, (v) => { if (v) loadNotificationSettings(); }, { immediate: true });

watch(() => route.path, () => {
  if (isAdmin.value && route.path === "/admin/settings") {
    loadNotificationSettings();
  }
});

function onDocumentClick(e) {
  if (bellWrap.value && !bellWrap.value.contains(e.target)) {
    bellOpen.value = false;
  }
  if (profileWrap.value && !profileWrap.value.contains(e.target)) {
    profileOpen.value = false;
  }
}

function onSettingsUpdated(e) {
  notificationsEnabled.value = !!e.detail?.notifications_enabled;
  notificationEmail.value = e.detail?.notification_email || "";
}

onMounted(() => {
  document.addEventListener("click", onDocumentClick);
  window.addEventListener("settings-updated", onSettingsUpdated);
});
onBeforeUnmount(() => {
  document.removeEventListener("click", onDocumentClick);
  window.removeEventListener("settings-updated", onSettingsUpdated);
});

async function onBellClick() {
  bellMsg.value = "";
  if (bellToggling.value) return;

  bellToggling.value = true;
  try {
    const s = await toggleNotifications();
    notificationsEnabled.value = !!s.notifications_enabled;
    notificationEmail.value = s.notification_email || "";
    window.dispatchEvent(new CustomEvent("settings-updated", { detail: s }));
    bellOpen.value = true;
    bellMsgType.value = "success";
    bellMsg.value = notificationsEnabled.value
      ? "Alerts turned on — you will be emailed for new audits."
      : "Alerts turned off.";
  } catch (e) {
    bellOpen.value = true;
    bellMsgType.value = "error";
    bellMsg.value = e.message;
    if (e.message.includes("Settings")) {
      router.push("/admin/settings");
      bellOpen.value = false;
    }
  } finally {
    bellToggling.value = false;
  }
}

async function logout() {
  // Clear app session
  sessionStorage.removeItem("nd_auth");
  sessionStorage.removeItem("nd_user_name");
  sessionStorage.removeItem("nd_role");

  // Clear MSAL cache locally only — do NOT call logoutRedirect/logoutPopup
  // as that signs the user out of ALL Microsoft apps in the browser
  try {
    const msalInstance = await getMsalInstance();
    const account = msalInstance.getAllAccounts()[0];
    if (account) {
      msalInstance.getTokenCache().clear();
      clearMsalCache();
    }
  } catch (err) {
    console.error("Logout error:", err);
  }

  router.push("/portal");
}
</script>

<style>
:root {
  /* Updated Palette as Semantic Tokens based on Reference Pages */
  --c-primary-dark: #161057;
  --primary: #161057;
  --primary-hover: #0F0A42;
  --text-main: #1E293B;
  --text-muted: #64748B;
  --text
```
> _Truncated to 16000 bytes — see full file in the source repo._

#### `frontend/src/api.js`

```js
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


export async function getDeadLetteredSubmissions() {
  const res = await fetch(`${API_BASE}/admin/submissions/dead-lettered`, {
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function replaySubmission(submissionId) {
  const res = await fetch(`${API_BASE}/admin/submissions/${submissionId}/replay`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

export async function replayAllDeadLetteredSubmissions() {
  const res = await fetch(`${API_BASE}/admin/submissions/dead-lettered/replay-all`, {
    method: 'POST',
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}


export async function getSuperAdminDashboard(forceRefresh = false) {
  const url = `${API_BASE}/admin/dashboard${forceRefresh ? '?refresh=true' : ''}`;
  const res = await fetch(url, {
    headers: getAuthHeaders(),
  });
  return handleResponse(res);
}

```

#### `frontend/src/authConfig.js`

```js
import { PublicClientApplication } from "@azure/msal-browser";

export const loginRequest = {
    scopes: ["openid", "profile", "email", "User.Read"],
};

let msalInstancePromise = null;

async function resolveAuthConfig() {
    const clientId = import.meta.env.VITE_MSAL_CLIENT_ID;
    const tenantId = import.meta.env.VITE_MSAL_TENANT_ID;
    if (clientId && tenantId && clientId !== "your-azure-ad-application-client-id") {
        return { clientId, tenantId };
    }

    try {
        const res = await fetch("/api/auth/config");
        if (res.ok) {
            const data = await res.json();
            if (data.clientId && data.tenantId) {
                return { clientId: data.clientId, tenantId: data.tenantId };
            }
        }
    } catch (e) {
        // Backend not running locally
    }

    // Default Entra credentials from root .env fallback
    return {
        clientId: "2f900af5-c166-4fdb-90f1-1eaee09eeff2",
        tenantId: "ea77fe37-fd2c-4294-87c3-8746bce6625a",
    };
}

/** Lazy MSAL instance — loads client ID from build env or /api/auth/config at runtime. */
export async function getMsalInstance() {
    if (!msalInstancePromise) {
        msalInstancePromise = (async () => {
            const { clientId, tenantId } = await resolveAuthConfig();
            const instance = new PublicClientApplication({
                auth: {
                    clientId,
                    authority: `https://login.microsoftonline.com/${tenantId}`,
                    redirectUri: window.location.origin,
                    postLogoutRedirectUri: `${window.location.origin}/portal`,
                },
                cache: {
                    cacheLocation: "sessionStorage",
                    storeAuthStateInCookie: false,
                },
            });
            await instance.initialize();
            return instance;
        })();
    }
    return msalInstancePromise;
}

/** Finish login after MSAL redirect: verify email with backend and store session. */
export async function completeAdminLogin(msalResponse) {
    if (!msalResponse?.account) {
        return { ok: false, reason: "no_account" };
    }

    const idToken = msalResponse.idToken;
    if (!idToken) {
        throw new Error("Microsoft did not return an ID token. Check Entra app registration.");
    }

    const email = (msalResponse.account.username || "").trim().toLowerCase();
    const res = await fetch("/api/auth/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
    });
    if (!res.ok) {
        throw new Error(`Sign-in verification failed (${res.status}). Is the API running?`);
    }
    const data = await res.json();
    if (!data.authorized) {
        return { ok: false, reason: "denied", email };
    }

    sessionStorage.setItem("nd_auth", "1");
    sessionStorage.setItem("nd_user_name", msalResponse.account.name || email);
    sessionStorage.setItem("nd_role", data.role || "admin");
    sessionStorage.setItem("nd_auth_token", idToken);
    sessionStorage.removeItem("nd_auth_error");
    return { ok: true };
}

export function clearMsalCache() {
    Object.keys(sessionStorage)
        .filter((k) => k.startsWith("msal.") || k.includes("login.windows"))
        .forEach((k) => sessionStorage.removeItem(k));
}

```

#### `frontend/src/components/AnimatedSelect.vue`

```vue
<template>
  <div class="animated-select" ref="containerRef" :class="{ 'is-open': isOpen, 'has-error': error }">
    <div
      class="select-trigger"
      :class="{ error: error, active: isOpen }"
      tabindex="0"
      role="combobox"
      :aria-expanded="isOpen"
      :aria-haspopup="'listbox'"
      @click="toggleDropdown"
      @keydown.down.prevent="onKeyDown"
      @keydown.up.prevent="onKeyUp"
      @keydown.enter.prevent="onKeyEnter"
      @keydown.esc.prevent="closeDropdown"
    >
      <span v-if="modelValue" class="selected-text">{{ modelValue }}</span>
      <span v-else class="placeholder-text">{{ placeholder || 'Select an option' }}</span>
      <svg class="chevron-icon" :class="{ rotated: isOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="6 9 12 15 18 9"></polyline>
      </svg>
    </div>

    <Transition name="dropdown-fade">
      <div v-if="isOpen" class="dropdown-menu" role="listbox">
        <div class="options-list" ref="optionsListRef">
          <div
            v-for="(opt, idx) in options"
            :key="opt"
            class="option-item"
            :class="{
              'is-selected': opt === modelValue,
              'is-highlighted': idx === highlightIndex
            }"
            role="option"
            :aria-selected="opt === modelValue"
            @click="selectOption(opt)"
            @mouseenter="highlightIndex = idx"
          >
            <span>{{ opt }}</span>
            <span v-if="opt === modelValue" class="check-mark">✓</span>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue';

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  options: {
    type: Array,
    default: () => []
  },
  placeholder: {
    type: String,
    default: 'Select an option'
  },
  error: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:modelValue', 'change']);

const isOpen = ref(false);
const highlightIndex = ref(0);
const containerRef = ref(null);
const optionsListRef = ref(null);

function toggleDropdown() {
  if (isOpen.value) {
    closeDropdown();
  } else {
    openDropdown();
  }
}

function openDropdown() {
  isOpen.value = true;
  highlightIndex.value = Math.max(0, props.options.indexOf(props.modelValue));
  nextTick(() => {
    scrollHighlightedIntoView();
    // Scroll dropdown into view if cut off
    scrollDropdownIntoView();
  });
}

function scrollDropdownIntoView() {
  nextTick(() => {
    if (!containerRef.value) return;
    const dropdownMenu = containerRef.value.querySelector('.dropdown-menu');
    if (!dropdownMenu) return;
    
    const rect = dropdownMenu.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    
    // Check if dropdown is cut off at bottom
    if (rect.bottom > viewportHeight) {
      const scrollAmount = rect.bottom - viewportHeight + 20; // 20px padding
      window.scrollBy({ top: scrollAmount, behavior: 'smooth' });
    }
  });
}

function closeDropdown() {
  isOpen.value = false;
}

function selectOption(opt) {
  emit('update:modelValue', opt);
  emit('change', opt);
  closeDropdown();
}

function onKeyDown() {
  if (!isOpen.value) {
    openDropdown();
    return;
  }
  if (highlightIndex.value < props.options.length - 1) {
    highlightIndex.value++;
    scrollHighlightedIntoView();
  }
}

function onKeyUp() {
  if (highlightIndex.value > 0) {
    highlightIndex.value--;
    scrollHighlightedIntoView();
  }
}

function onKeyEnter() {
  if (isOpen.value && props.options.length > 0) {
    const selected = props.options[highlightIndex.value];
    if (selected) {
      selectOption(selected);
    }
  } else {
    openDropdown();
  }
}

function scrollHighlightedIntoView() {
  nextTick(() => {
    if (!optionsListRef.value) return;
    const highlightedEl = optionsListRef.value.querySelector('.is-highlighted');
    if (highlightedEl) {
      highlightedEl.scrollIntoView({ block: 'nearest' });
    }
  });
}

function handleClickOutside(e) {
  if (containerRef.value && !containerRef.value.contains(e.target)) {
    closeDropdown();
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped>
.animated-select {
  position: relative;
  width: 100%;
}

.select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  max-width: 420px;
  padding: 0.55rem 0.75rem;
  background-color: #FFFFFF;
  border: 1.5px solid #3B82F6;
  border-radius: 8px;
  font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 0.85rem;
  color: #120050;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
  min-height: 38px;
  box-sizing: border-box;
}

.select-trigger:hover {
  border-color: #2563EB;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.1);
}

.select-trigger:focus-visible,
.select-trigger.active {
  outline: none;
  border-color: #2563EB;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.select-trigger.error {
  border-color: #E53E3E;
  background-color: #FFF5F5;
}

.placeholder-text {
  color: #8C827A;
}

.selected-text {
  color: #120050;
  font-weight: 500;
}

.chevron-icon {
  color: #555;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
  margin-left: 0.4rem;
  width: 16px;
  height: 16px;
}

.chevron-icon.rotated {
  transform: rotate(180deg);
  color: #2563EB;
}

/* Enhanced Dropdown Animations */
.dropdown-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  max-width: 420px;
  background: #FFFFFF;
  border: 1.5px solid #3B82F6;
  border-radius: 8px;
  box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.2), 0 8px 10px -6px rgba(59, 130, 246, 0.15);
  z-index: 100;
  overflow: hidden;
  transform-origin: top center;
}

/* Smooth Dropdown Transition */
.dropdown-fade-enter-active {
  animation: dropdownSlideIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.dropdown-fade-leave-active {
  animation: dropdownSlideOut 0.2s cubic-bezier(0.4, 0, 1, 1);
}

@keyframes dropdownSlideIn {
  from {
    opacity: 0;
    transform: translateY(-8px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes dropdownSlideOut {
  from {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
  to {
    opacity: 0;
    transform: translateY(-8px) scale(0.96);
  }
}

.options-list {
  max-height: 280px;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0.35rem 0;
  scrollbar-width: thin;
  scrollbar-color: rgba(59, 130, 246, 0.3) rgba(59, 130, 246, 0.08);
}

.options-list::-webkit-scrollbar {
  width: 8px;
}

.options-list::-webkit-scrollbar-track {
  background: rgba(59, 130, 246, 0.05);
  border-radius: 4px;
  margin: 4px 0;
}

.options-list::-webkit-scrollbar-thumb {
  background: rgba(59, 130, 246, 0.3);
  border-radius: 4px;
  transition: background 0.2s;
}

.options-list::-webkit-scrollbar-thumb:hover {
  background: rgba(59, 130, 246, 0.5);
}

.option-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.55rem 0.85rem;
  font-size: 0.85rem;
  color: #120050;
  cursor: pointer;
  transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.option-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2.5px;
  background: #3B82F6;
  transform: scaleY(0);
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.option-item:hover::before,
.option-item.is-highlighted::before {
  transform: scaleY(1);
}

.option-item:hover,
.option-item.is-highlighted {
  background-color: #EFF6FF;
  color: #2563EB;
  padding-left: 1rem;
}

.option-item.is-selected {
  background-color: #EFF6FF;
  color: #2563EB;
  font-weight: 600;
}

.check-mark {
  color: #3B82F6;
  font-weight: bold;
  font-size: 1rem;
}

.no-results {
  padding: 1rem 0.85rem;
  text-align: center;
  color: #8C827A;
  font-size: 0.82rem;
}
</style>

```

#### `frontend/src/components/RichEditor.vue`

```vue
<template>
  <div class="rich-editor" :class="{ readonly: readonly }">
    <div class="toolbar">
      <div class="toolbar-tools">
        <!-- Text formatting tools for the live preview -->
        <template v-if="mode === 'visual' && !readonly">
          <button type="button" @click="format('bold')" title="Bold"><b>B</b></button>
          <button type="button" @click="format('italic')" title="Italic"><i>I</i></button>
          <button type="button" @click="format('underline')" title="Underline"><u>U</u></button>
          <span class="toolbar-divider"></span>
          <button type="button" @click="format('insertUnorderedList')" title="Bullet list">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="9" y1="6" x2="20" y2="6"/><line x1="9" y1="12" x2="20" y2="12"/><line x1="9" y1="18" x2="20" y2="18"/><circle cx="4" cy="6" r="1" fill="currentColor"/><circle cx="4" cy="12" r="1" fill="currentColor"/><circle cx="4" cy="18" r="1" fill="currentColor"/></svg>
          </button>
        </template>
        <span class="preview-label" v-else-if="mode === 'visual' && readonly">Read-only Email Preview</span>
        <span class="preview-label" v-else>HTML Source Editor</span>
      </div>

      <!-- Visual / HTML toggle -->
      <div class="mode-toggle">
        <button
          type="button"
          :class="['mode-btn', mode === 'visual' ? 'mode-active' : '']"
          @click="setMode('visual')"
        >Preview / Edit</button>
        <button
          v-if="!readonly"
          type="button"
          :class="['mode-btn', mode === 'html' ? 'mode-active' : '']"
          @click="setMode('html')"
        >HTML</button>
      </div>
    </div>

    <!-- Live Preview Iframe -->
    <iframe
      v-show="mode === 'visual'"
      class="preview-iframe"
      ref="iframeRef"
      @load="onIframeLoad"
      frameborder="0"
      title="Email Preview"
    ></iframe>

    <!-- HTML Source Textarea -->
    <textarea
      v-show="mode === 'html' && !readonly"
      v-model="htmlSource"
      class="html-source"
      spellcheck="false"
      @input="onHtmlInput"
    ></textarea>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";

const props = defineProps({
  modelValue: { type: String, default: "" },
  readonly:   { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue"]);

const mode = ref("visual");
const htmlSource = ref(props.modelValue || "");
const iframeRef = ref(null);
let isInternalUpdate = false;

function setMode(next) {
  mode.value = next;
  if (next === 'visual') {
    renderIframe(htmlSource.value);
  }
}

function onHtmlInput() {
  isInternalUpdate = true;
  emit("update:modelValue", htmlSource.value);
  setTimeout(() => { isInternalUpdate = false; }, 50);
}

function format(command) {
  if (iframeRef.value?.contentDocument) {
    iframeRef.value.contentDocument.execCommand(command, false, null);
    iframeRef.value.contentWindow.focus();
    syncFromIframe();
  }
}

function syncFromIframe() {
  const doc = iframeRef.value?.contentDocument;
  if (!doc) return;
  isInternalUpdate = true;
  const updatedHtml = "<!DOCTYPE html>\n" + doc.documentElement.outerHTML;
  htmlSource.value = updatedHtml;
  emit("update:modelValue", updatedHtml);
  setTimeout(() => { isInternalUpdate = false; }, 50);
}

function onIframeLoad() {
  // If we just loaded, it might be the initial blank state. We handle rendering manually in renderIframe.
}

function renderIframe(html) {
  if (!iframeRef.value) return;
  const doc = iframeRef.value.contentDocument;
  if (!doc) return;

  doc.open();
  doc.write(html || " ");
  doc.close();

  if (!props.readonly) {
    // Make body editable
    doc.body.contentEditable = "true";
    
    // Hide outline when focused
    const style = doc.createElement('style');
    style.textContent = `
      body[contenteditable] { outline: none; }
      body[contenteditable]:focus { outline: none; }
    `;
    doc.head.appendChild(style);

    // Listen for edits
    doc.body.addEventListener("input", syncFromIframe);
    doc.body.addEventListener("keyup", syncFromIframe);
  }
}

watch(() => props.modelValue, (val) => {
  if (!isInternalUpdate && val !== htmlSource.value) {
    htmlSource.value = val || "";
    if (mode.value === 'visual') {
      renderIframe(htmlSource.value);
    }
  }
});

onMounted(() => {
  if (mode.value === 'visual') {
    setTimeout(() => renderIframe(htmlSource.value), 50);
  }
});
</script>

<style scoped>
.rich-editor {
  border: 2px solid var(--c-primary-dark);
  border-radius: 16px;
  overflow: hidden;
  background: var(--c-white);
  display: flex;
  flex-direction: column;
  height: 600px; /* Fixed height for email preview */
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.5rem 0.65rem;
  background: var(--c-primary-dark);
  flex-wrap: wrap;
  flex-shrink: 0;
}

.toolbar-tools {
  display: flex;
  align-items: center;
  gap: 0.15rem;
  padding: 0.35rem 0.5rem;
}

.toolbar-tools button {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  border: none;
  background: transparent;
  color: rgba(255,255,255,0.75);
  cursor: pointer;
  display: grid;
  place-items: center;
  font-size: 0.85rem;
  transition: all 0.12s;
  font-family: 'Geist', sans-serif;
}
.toolbar-tools button:hover:not(:disabled) {
  background: rgba(255,255,255,0.12);
  color: var(--c-white);
}
.toolbar-tools button:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.toolbar-divider {
  width: 1px;
  height: 18px;
  background: rgba(255,255,255,0.2);
  margin: 0 0.2rem;
}

.preview-label {
  color: var(--c-white);
  font-family: 'Geist', sans-serif;
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.mode-toggle {
  display: flex;
  gap: 0;
  flex-shrink: 0;
}

.mode-btn {
  padding: 0.45rem 0.85rem;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  border: 1px solid rgba(255,255,255,0.35);
  background: transparent;
  color: rgba(255,255,255,0.7);
  cursor: pointer;
  font-family: 'Geist', sans-serif;
  transition: all 0.15s;
}
.mode-btn:first-child { border-radius: 4px 0 0 4px; }
.mode-btn:last-child { border-radius: 0 4px 4px 0; border-left: none; }
.mode-btn.mode-active {
  background: var(--c-accent);
  color: var(--c-primary-dark);
  border-color: var(--c-accent);
}
.mode-btn:hover:not(.mode-active) {
  color: var(--c-white);
  background: rgba(255,255,255,0.08);
}

.preview-iframe {
  width: 100%;
  flex-grow: 1;
  border: none;
  background: #F4F2F0; /* Match email bg */
}

.html-source {
  display: block;
  width: 100%;
  flex-grow: 1;
  padding: 1rem 1.25rem;
  border: none;
  resize: none;
  font-family: 'Courier New', Consolas, monospace;
  font-size: 0.8rem;
  line-height: 1.55;
  color: var(--c-primary-dark);
  background: #faf9f6;
  box-sizing: border-box;
}
.html-source:focus { outline: none; background: var(--c-white); }
</style>

```

#### `frontend/src/components/SaveContinueButton.vue`

```vue
<template>
  <div class="save-continue-container">
    <button type="button" class="btn btn-green" @click="handleSave" :disabled="loading">
      <span v-if="loading">Saving...</span>
      <span v-else>
        <span class="btn-text-desktop">Save and Continue Later</span>
        <span class="btn-text-mobile">Save Draft</span>
      </span>
    </button>

    <!-- Modal dialog for resume url -->
    <div v-if="showModal" class="save-modal-overlay" @click="showModal = false">
      <div class="save-modal-card" @click.stop>
        <h3>Audit Saved!</h3>
        <p>You can close this tab and resume your audit anytime within the next 7 days using the link below:</p>
        
        <div class="link-box">
          <input type="text" readonly :value="url" ref="linkInput" />
          <button @click="copyLink" class="btn btn-primary">
            {{ copied ? "Copied!" : "Copy Link" }}
          </button>
        </div>

        <button @click="showModal = false" class="btn btn-secondary close-btn">Done</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

const props = defineProps({
  onSave: { type: Function, required: true }
});

const loading = ref(false);
const showModal = ref(false);
const url = ref("");
const copied = ref(false);
const linkInput = ref(null);

async function handleSave() {
  loading.value = true;
  try {
    const resumeUrl = await props.onSave();
    url.value = resumeUrl;
    showModal.value = true;
  } catch (e) {
    alert("Could not save progress. Please ensure you filled in your name and email on step 1.");
  } finally {
    loading.value = false;
  }
}

function copyLink() {
  if (linkInput.value) {
    linkInput.value.select();
    navigator.clipboard.writeText(url.value).then(() => {
      copied.value = true;
      setTimeout(() => { copied.value = false; }, 2000);
    });
  }
}
</script>

<style scoped>
.save-continue-container { display: inline-block; }
.save-continue-container .btn-green {
  background: var(--c-white); color: var(--c-primary-dark); border: 2px solid var(--c-primary-dark); border-radius: 99px;
  padding: 0.65rem 1.4rem; font-size: 0.875rem; font-weight: 700; cursor: pointer; transition: all 0.15s;
  font-family: 'Fraunces', serif; box-shadow: 3px 3px 0 var(--c-primary-dark);
  display: inline-flex; align-items: center; gap: 0.4rem;
}
.save-continue-container .btn-green:hover:not(:disabled) { transform: translate(-2px,-2px); box-shadow: 5px 5px 0 var(--c-primary-dark); }
.save-continue-container .btn-green:disabled { opacity: 0.5; cursor: not-allowed; box-shadow: none; }
.btn-text-mobile { display: none; }
@media (max-width: 600px) {
  .btn-text-desktop { display: none; }
  .btn-text-mobile { display: inline; }
}
.save-modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.6); display: flex; justify-content: center; align-items: center; z-index: 1000;
}
.save-modal-card {
  background: white; padding: 2rem; border-radius: 16px; border: 2px solid var(--c-primary-dark);
  box-shadow: 4px 4px 0 var(--c-primary-dark); max-width: 500px; width: 90%; text-align: center;
}
.save-modal-card h3 { font-family: 'Playfair Display', serif; font-size: 1.5rem; margin-bottom: 0.75rem; color: var(--c-primary-dark); }
.save-modal-card p { font-size: 0.9rem; color: #666; margin-bottom: 1.5rem; line-height: 1.5; }
.link-box { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
.link-box input {
  flex: 1; padding: 0.6rem 0.8rem; border: 2px solid var(--c-primary-dark); border-radius: 8px; font-size: 0.85rem; background: #fff; color: #333;
}
.close-btn { margin-top: 1rem; width: 100%; }
</style>

```

#### `frontend/src/components/ScoreTable.vue`

```vue
<template>
  <div class="score-breakdown-wrapper">
    <!-- Optional Respondent Meta Header -->
    <div v-if="data?.name || data?.email || data?.designation" class="respondent-meta-header">
      <div class="rmh-left">
        <div class="rmh-avatar">{{ getInitials(data.name || data.email) }}</div>
        <div>
          <div class="rmh-name-row">
            <span class="rmh-name">{{ data.name || 'Anonymous Respondent' }}</span>
            <span v-if="data.submission_source" class="rmh-method-tag" :class="data.submission_source.toLowerCase()">
              {{ data.submission_source === 'INVITATION' ? '🔗 Invitation Link' : '🌐 Direct Website' }}
            </span>
            <span v-if="data.weight != null" class="rmh-weight-tag">
              Weight: {{ data.weight }}×
            </span>
          </div>
          <div class="rmh-details">
            <span v-if="data.designation" class="rmh-detail-item"><strong>Role:</strong> {{ data.designation }}</span>
            <span v-if="data.function || data.answers?.function" class="rmh-detail-item"><strong>Function:</strong> {{ data.function || data.answers?.function }}</span>
            <span v-if="data.email" class="rmh-detail-item"><strong>Email:</strong> {{ data.email }}</span>
          </div>
        </div>
      </div>
      <div class="rmh-right">
        <div class="rmh-score-box">
          <span class="rmh-score-num">{{ data.overall_avg != null ? data.overall_avg : '—' }}</span>
          <span class="rmh-score-denom">/ 20</span>
        </div>
        <span class="maturity-badge" :class="getMaturityClass(data.overall_avg)">
          {{ data.overall_level || 'Pending' }}
        </span>
      </div>
    </div>

    <!-- Explanatory Header -->
    <div class="scoring-explanation-note">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="16" x2="12" y2="12"></line>
        <line x1="12" y1="8" x2="12.01" y2="8"></line>
      </svg>
      <span>
        <strong>Transparent Score Breakdown:</strong> Each pillar consists of 5 questions.
        Response marks: <strong>Yes = 4 marks</strong>, <strong>Partially = 2 marks</strong>, <strong>No / Not Sure = 0 marks</strong> (max 20 per pillar).
        The overall index is the average across all 8 core pillars.
      </span>
    </div>

    <table class="scores-table">
      <thead>
        <tr>
          <th style="width: 32%">Pillar &amp; Dimension</th>
          <th style="width: 33%">Score &amp; Progress</th>
          <th style="width: 25%">Maturity Level</th>
          <th style="width: 10%; text-align: center">Breakdown</th>
        </tr>
      </thead>
      <template v-for="s in sections" :key="s.key">
        <tbody>
          <tr
            class="section-row"
            :class="{ 'is-expanded': expandedSection === s.key }"
            @click="toggleSection(s.key)"
          >
            <td class="section-name">
              <span class="bullet-dot"></span>
              <div>
                <strong class="sec-title">{{ s.label }}</strong>
                <span class="sec-dim-code">Dimension {{ s.key.toUpperCase() }}</span>
              </div>
            </td>
            <td>
              <div class="score-progress-wrap">
                <span class="score-num">
                  {{ data[`${s.key}_score`] != null ? data[`${s.key}_score`] : 0 }} / 20
                </span>
                <div class="progress-bar-bg">
                  <div
                    class="progress-bar-fill"
                    :style="{ width: `${Math.min(100, ((data[`${s.key}_score`] || 0) / 20) * 100)}%` }"
                  ></div>
                </div>
              </div>
            </td>
            <td>
              <span class="maturity-badge" :class="getMaturityClass(data[`${s.key}_score`])">
                {{ data[`${s.key}_level`] || getCalculatedLevel(data[`${s.key}_score`]) }}
              </span>
            </td>
            <td class="chevron-cell">
              <span class="inspect-text">{{ expandedSection === s.key ? 'Hide ▲' : 'Inspect ▼' }}</span>
            </td>
          </tr>
          
          <!-- Expanded Transparent Q&A Row -->
          <tr v-if="expandedSection === s.key" class="details-row">
            <td colspan="4">
              <div class="qa-details-container">
                <!-- Section Calculation Summary Banner -->
                <div class="section-calc-summary">
                  <span class="scs-title">Calculation for {{ s.label }}:</span>
                  <span class="scs-formula">
                    {{ getSectionCalcFormula(s) }}
                  </span>
                </div>

                <!-- Questions List -->
                <div v-for="(q, qi) in s.questions" :key="q.field" class="qa-item">
                  <div class="qa-top-row">
                    <div class="qa-q-text">
                      <span class="qa-index">{{ q.field.toUpperCase() }}</span>
                      {{ q.text }}
                    </div>
                  </div>

                  <div class="qa-scoring-breakdown">
                    <div class="qa-response-group">
                      <span class="qa-label">Response:</span>
                      <span class="badge" :class="getAnswerBadgeClass(getAnswerValue(q.field))">
                        {{ getAnswerValue(q.field) || 'Not answered' }}
                      </span>
                    </div>

                    <div class="qa-marks-group">
                      <span class="qa-label">Marks Awarded:</span>
                      <span class="marks-pill" :class="getMarksPillClass(getAnswerValue(q.field))">
                        <strong>{{ getMarksAwarded(getAnswerValue(q.field)) }}</strong> / 4 max marks
                      </span>
                      <span class="qa-marks-calc">
                        ({{ getAnswerValue(q.field) || 'None' }} = {{ getMarksAwarded(getAnswerValue(q.field)) }} pts · weight 1.0)
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </template>
      
      <!-- Overall Average Reconciliation Row -->
      <tbody>
        <tr class="overall-row">
          <td>
            <div class="overall-title-wrap">
              <strong>Overall Weighted NIWI Index</strong>
              <span class="overall-subtitle">Reconciled average of 8 pillars</span>
            </div>
          </td>
          <td>
            <div class="score-progress-wrap">
              <span class="score-num">
                <strong>{{ data.overall_avg != null ? data.overall_avg : 0 }}</strong>
                <span class="score-denom"> / 20</span>
                <span class="score-avg">({{ Math.round(((data.overall_avg || 0) / 20) * 100) }}%)</span>
              </span>
              <div class="progress-bar-bg">
                <div
                  class="progress-bar-fill overall-fill"
                  :style="{ width: `${Math.min(100, ((data.overall_avg || 0) / 20) * 100)}%` }"
                ></div>
              </div>
            </div>
          </td>
          <td>
            <span class="maturity-badge overall-badge" :class="getMaturityClass(data.overall_avg)">
              {{ data.overall_level || getCalculatedLevel(data.overall_avg) }}
            </span>
          </td>
          <td></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
  dbSections: {
    type: Array,
    default: null,
  },
});

const expandedSection = ref(null);

function toggleSection(key) {
  expandedSection.value = expandedSection.value === key ? null : key;
}

function getInitials(name) {
  if (!name) return 'EMP';
  const clean = name.replace(/[^a-zA-Z0-9\s]/g, '').trim();
  const words = clean.split(/\s+/);
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase();
  }
  return clean.slice(0, 2).toUpperCase() || 'EMP';
}

function getAnswerBadgeClass(val) {
  if (!val) return 'badge-notsure';
  const v = String(val).toLowerCase().trim();
  if (v === 'yes') return 'badge-yes';
  if (v === 'partially') return 'badge-partially';
  if (v === 'no') return 'badge-no';
  return 'badge-notsure';
}

function getMaturityClass(score) {
  if (score === undefined || score === null || score === 'NA') return 'badge-notsure';
  const s = parseFloat(score);
  if (s <= 6) return 'badge-no';
  if (s <= 14) return 'badge-partially';
  return 'badge-yes';
}

function getCalculatedLevel(score) {
  if (score === undefined || score === null || score === 'NA') return 'Not applicable';
  const s = parseFloat(score);
  if (s <= 6) return 'Level 1 — Foundational';
  if (s <= 14) return 'Level 2 — Early Progress';
  return 'Level 3 — Developing';
}

function getMarksAwarded(val) {
  if (!val) return 0;
  const v = String(val).toLowerCase().trim();
  if (v === 'yes') return 4;
  if (v === 'partially') return 2;
  return 0; // No, Not Sure, NA
}

function getMarksPillClass(val) {
  const marks = getMarksAwarded(val);
  if (marks === 4) return 'marks-full';
  if (marks === 2) return 'marks-partial';
  return 'marks-zero';
}

function getAnswerValue(field) {
  if (!props.data) return null;
  if (props.data[field] != null && props.data[field] !== '') return props.data[field];
  if (props.data.answers && typeof props.data.answers === 'object' && props.data.answers[field] != null) {
    return props.data.answers[field];
  }
  return null;
}

function getSectionCalcFormula(sec) {
  let total = 0;
  const items = sec.questions.map(q => {
    const ans = getAnswerValue(q.field);
    const marks = getMarksAwarded(ans);
    total += marks;
    return `${q.field.toUpperCase()}: ${marks}pts (${ans || 'Unanswered'})`;
  });
  return `${items.join(' + ')} = ${total} / 20 marks earned (${Math.round((total / 20) * 100)}%)`;
}

// ─── Canonical NIWI Standard Sections (Q5–Q44) ─────────
const FALLBACK_SECTIONS = [
  {
    key: "lc",
    label: "Leadership & Culture",
    questions: [
      { field: "q5",  text: "Does your organisation have a clearly defined neurodiversity inclusion strategy with specific, time-bound objectives?" },
      { field: "q6",  text: "Is a senior leader (C-suite or equivalent) explicitly accountable for neurodiversity inclusion?" },
      { field: "q7",  text: "Do senior leaders receive training on neuro-inclusion and actively model inclusive behaviors?" },
      { field: "q8",  text: "Do you have an active neurodiversity-focused employee resource group (ERG) or network that is supported and heard?" },
      { field: "q9",  text: "Does your organisation publicly communicate its commitment to neuro-inclusion through actions and reporting?" }
    ]
  },
  {
    key: "ro",
    label: "Recruitment & Onboarding",
    questions: [
      { field: "q10", text: "Are job descriptions clear, concise, and aligned with the actual role, minimising jargon?" },
      { field: "q11", text: "Is the application process transparent and supportive, with multiple contact options to reduce anxiety?" },
      { field: "q12", text: "Do selection processes include practical or skills-based assessments rather than relying solely on interviews?" },
      { field: "q13", text: "Are interviews flexible and inclusive, with options like sharing questions in advance or alternative formats?" },
      { field: "q14", text: "Are new hires supported before starting with structured communication and early adjustment conversations?" }
    ]
  },
  {
    key: "we",
    label: "Work Environment & Adjustments",
    questions: [
      { field: "q15", text: "Is there a clear, accessible process for employees to request reasonable adjustments without stigma?" },
      { field: "q16", text: "Are flexible working arrangements (hours, locations, patterns) actively available and supported?" },
      { field: "q17", text: "Are managers trained and empowered to understand, implement, and maintain reasonable adjustments?" },
      { field: "q18", text: "Are assistive technologies, ergonomic equipment, and productivity software easily accessible?" },
      { field: "q19", text: "Are adjustment requests handled promptly with periodic reviews to ensure ongoing effectiveness?" }
    ]
  },
  {
    key: "be",
    label: "Built Environment & Sensory",
    questions: [
      { field: "q20", text: "Are quiet, low-stimulation focus areas or decompression spaces accessible to all employees?" },
      { field: "q21", text: "Has the organisation addressed lighting, acoustic control, and sensory triggers across physical workspaces?" },
      { field: "q22", text: "Is clear, consistent signage and intuitive wayfinding implemented throughout physical facilities?" },
      { field: "q23", text: "Are employees allowed to personalise workstation sensory aspects (lighting levels, noise controls, seating)?" },
      { field: "q24", text: "Has a structured sensory or physical accessibility audit been conducted within the past two years?" }
    ]
  },
  {
    key: "tm",
    label: "Talent Management & Development",
    questions: [
      { field: "q25", text: "Are performance management and appraisal criteria designed to reward objective outcomes rather than conformity?" },
      { field: "q26", text: "Do neurodivergent employees have equitable access to learning, skill development, and career advancement?" },
      { field: "q27", text: "Are strengths-based career pathways and coaching models integrated into talent progression?" },
      { field: "q28", text: "Are dedicated mentorship or sponsorship opportunities available for neurodivergent professionals?" },
      { field: "q29", text: "Is employee retention and progression data tracked across diverse demographic groups to identify disparities?" }
    ]
  },
  {
    key: "ca",
    label: "Communication & Accessibility",
    questions: [
      { field: "q30", text: "Are corporate communications written in plain, unambiguous language free from unnecessary jargon?" },
      { field: "q31", text: "Is critical company information and training delivered in multiple accessible formats (written, video, visual)?" },
      { field: "q32", text: "Are meeting agendas, materials, and expectations distributed in advance to enable cognitive preparation?" },
      { field: "q33", text: "Are digital tools, intranet systems, and software platforms audited for digital accessibility standards?" },
      { field: "q34", text: "Can employees easily specify their preferred communication channels and collaborative styles?" }
    ]
  },
  {
    key: "pc",
    label: "Products & Customer Experience",
    questions: [
      { field: "q35", text: "Are client-facing products, digital portals, and services designed with neuro-inclusive user experience in mind?" },
      { field: "q36", text: "Are neurodivergent customers or community advocates included in product feedback, testing, and co-design?" },
      { field: "q37", text: "Are frontline and customer support teams trained to assist neurodivergent clients respectfully and effectively?" },
      { field: "q38", text: "Do digital customer touchpoints comply with international accessibility standards (such as WCAG AA)?" },
      { field: "q39", text: "Is there a transparent, low-friction pathway for customers to request adjustments or alternative communication formats?" }
    ]
  },
  {
    key: "sp",
    label: "Suppliers & Procurement",
    questions: [
      { field: "q40", text: "Does your procurement process incorporate neurodiversity and inclusive employment criteria for vendors?" },
      { field: "q41", text: "Are external contractors and suppliers expected to uphold basic workplace inclusion standards?" },
      { field: "q42", 
```
> _Truncated to 16000 bytes — see full file in the source repo._

#### `frontend/src/components/SearchableSelect.vue`

```vue
<template>
  <div class="searchable-select" ref="containerRef" :class="{ 'is-open': isOpen, 'has-error': error }">
    <div
      class="select-trigger"
      :class="{ error: error, active: isOpen }"
      tabindex="0"
      role="combobox"
      :aria-expanded="isOpen"
      :aria-haspopup="'listbox'"
      @click="toggleDropdown"
      @keydown.down.prevent="onKeyDown"
      @keydown.up.prevent="onKeyUp"
      @keydown.enter.prevent="onKeyEnter"
      @keydown.esc.prevent="closeDropdown"
    >
      <span v-if="modelValue" class="selected-text">{{ modelValue }}</span>
      <span v-else class="placeholder-text">{{ placeholder || 'Select an option' }}</span>
      <svg class="chevron-icon" :class="{ rotated: isOpen }" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="6 9 12 15 18 9"></polyline>
      </svg>
    </div>

    <Transition name="dropdown-fade">
      <div v-if="isOpen" class="dropdown-menu" role="listbox">
        <div class="search-box">
          <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>
          <input
            ref="searchInputRef"
            v-model="searchQuery"
            type="text"
            placeholder="Search country..."
            class="search-input"
            @input="highlightIndex = 0"
            @keydown.down.prevent="onKeyDown"
            @keydown.up.prevent="onKeyUp"
            @keydown.enter.prevent="onKeyEnter"
            @keydown.esc.prevent="closeDropdown"
          />
          <button v-if="searchQuery" type="button" class="clear-btn" @click="searchQuery = ''" aria-label="Clear search">×</button>
        </div>

        <div class="options-list" ref="optionsListRef">
          <div
            v-for="(opt, idx) in filteredOptions"
            :key="opt"
            class="option-item"
            :class="{
              'is-selected': opt === modelValue,
              'is-highlighted': idx === highlightIndex
            }"
            role="option"
            :aria-selected="opt === modelValue"
            @click="selectOption(opt)"
            @mouseenter="highlightIndex = idx"
          >
            <span>{{ opt }}</span>
            <span v-if="opt === modelValue" class="check-mark">✓</span>
          </div>
          <div v-if="filteredOptions.length === 0" class="no-results">
            No matches found for "{{ searchQuery }}"
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue';

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  options: {
    type: Array,
    default: () => []
  },
  placeholder: {
    type: String,
    default: 'Select country'
  },
  error: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:modelValue', 'change']);

const isOpen = ref(false);
const searchQuery = ref('');
const highlightIndex = ref(0);
const containerRef = ref(null);
const searchInputRef = ref(null);
const optionsListRef = ref(null);

const filteredOptions = computed(() => {
  if (!searchQuery.value.trim()) return props.options;
  const q = searchQuery.value.toLowerCase().trim();
  return props.options.filter(opt => opt.toLowerCase().includes(q));
});

function toggleDropdown() {
  if (isOpen.value) {
    closeDropdown();
  } else {
    openDropdown();
  }
}

function openDropdown() {
  isOpen.value = true;
  searchQuery.value = '';
  highlightIndex.value = Math.max(0, filteredOptions.value.indexOf(props.modelValue));
  nextTick(() => {
    searchInputRef.value?.focus();
    scrollHighlightedIntoView();
    // Scroll dropdown into view if cut off
    scrollDropdownIntoView();
  });
}

function scrollDropdownIntoView() {
  nextTick(() => {
    if (!containerRef.value) return;
    const dropdownMenu = containerRef.value.querySelector('.dropdown-menu');
    if (!dropdownMenu) return;
    
    const rect = dropdownMenu.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    
    // Check if dropdown is cut off at bottom
    if (rect.bottom > viewportHeight) {
      const scrollAmount = rect.bottom - viewportHeight + 20; // 20px padding
      window.scrollBy({ top: scrollAmount, behavior: 'smooth' });
    }
  });
}

function closeDropdown() {
  isOpen.value = false;
  searchQuery.value = '';
}

function selectOption(opt) {
  emit('update:modelValue', opt);
  emit('change', opt);
  closeDropdown();
}

function onKeyDown() {
  if (!isOpen.value) {
    openDropdown();
    return;
  }
  if (highlightIndex.value < filteredOptions.value.length - 1) {
    highlightIndex.value++;
    scrollHighlightedIntoView();
  }
}

function onKeyUp() {
  if (highlightIndex.value > 0) {
    highlightIndex.value--;
    scrollHighlightedIntoView();
  }
}

function onKeyEnter() {
  if (isOpen.value && filteredOptions.value.length > 0) {
    const selected = filteredOptions.value[highlightIndex.value];
    if (selected) {
      selectOption(selected);
    }
  } else {
    openDropdown();
  }
}

function scrollHighlightedIntoView() {
  nextTick(() => {
    if (!optionsListRef.value) return;
    const highlightedEl = optionsListRef.value.querySelector('.is-highlighted');
    if (highlightedEl) {
      highlightedEl.scrollIntoView({ block: 'nearest' });
    }
  });
}

function handleClickOutside(e) {
  if (containerRef.value && !containerRef.value.contains(e.target)) {
    closeDropdown();
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped>
.searchable-select {
  position: relative;
  width: 100%;
}

.select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  max-width: 420px;
  padding: 0.55rem 0.75rem;
  background-color: #FFFFFF;
  border: 1.5px solid #3B82F6;
  border-radius: 8px;
  font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 0.85rem;
  color: #120050;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
  min-height: 38px;
  box-sizing: border-box;
}

.select-trigger:hover {
  border-color: #2563EB;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.1);
}

.select-trigger:focus-visible,
.select-trigger.active {
  outline: none;
  border-color: #2563EB;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.select-trigger.error {
  border-color: #E53E3E;
  background-color: #FFF5F5;
}

.placeholder-text {
  color: #8C827A;
}

.selected-text {
  color: #120050;
  font-weight: 500;
}

.chevron-icon {
  color: #555;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
  margin-left: 0.4rem;
  width: 16px;
  height: 16px;
}

.chevron-icon.rotated {
  transform: rotate(180deg);
  color: #2563EB;
}

/* Enhanced Dropdown Animations */
.dropdown-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  max-width: 420px;
  background: #FFFFFF;
  border: 1.5px solid #3B82F6;
  border-radius: 8px;
  box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.2), 0 8px 10px -6px rgba(59, 130, 246, 0.15);
  z-index: 100;
  overflow: hidden;
  transform-origin: top center;
}

/* Smooth Dropdown Transition */
.dropdown-fade-enter-active {
  animation: dropdownSlideIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.dropdown-fade-leave-active {
  animation: dropdownSlideOut 0.2s cubic-bezier(0.4, 0, 1, 1);
}

@keyframes dropdownSlideIn {
  from {
    opacity: 0;
    transform: translateY(-8px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes dropdownSlideOut {
  from {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
  to {
    opacity: 0;
    transform: translateY(-8px) scale(0.96);
  }
}

.search-box {
  display: flex;
  align-items: center;
  padding: 0.6rem 0.8rem;
  border-bottom: 1px solid #E2DDD4;
  background: #FAF8F5;
  gap: 0.5rem;
}

.search-icon {
  color: #3B82F6;
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 0.9rem;
  color: #120050;
  padding: 0.25rem 0;
}

.search-input::placeholder {
  color: #A8A29E;
}

.clear-btn {
  background: none;
  border: none;
  font-size: 1.2rem;
  line-height: 1;
  color: #8C827A;
  cursor: pointer;
  padding: 0 0.25rem;
}

.clear-btn:hover {
  color: #120050;
}

.options-list {
  max-height: 280px;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0.35rem 0;
  scrollbar-width: thin;
  scrollbar-color: rgba(59, 130, 246, 0.3) rgba(59, 130, 246, 0.08);
}

.options-list::-webkit-scrollbar {
  width: 8px;
}

.options-list::-webkit-scrollbar-track {
  background: rgba(59, 130, 246, 0.05);
  border-radius: 4px;
  margin: 4px 0;
}

.options-list::-webkit-scrollbar-thumb {
  background: rgba(59, 130, 246, 0.3);
  border-radius: 4px;
  transition: background 0.2s;
}

.options-list::-webkit-scrollbar-thumb:hover {
  background: rgba(59, 130, 246, 0.5);
}

.option-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.55rem 0.85rem;
  font-size: 0.85rem;
  color: #120050;
  cursor: pointer;
  transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.option-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2.5px;
  background: #3B82F6;
  transform: scaleY(0);
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.option-item:hover::before,
.option-item.is-highlighted::before {
  transform: scaleY(1);
}

.option-item:hover,
.option-item.is-highlighted {
  background-color: #EFF6FF;
  color: #2563EB;
  padding-left: 1rem;
}

.option-item.is-selected {
  background-color: #EFF6FF;
  color: #2563EB;
  font-weight: 600;
}

.check-mark {
  color: #3B82F6;
  font-weight: bold;
}

.no-results {
  padding: 1.25rem 1rem;
  text-align: center;
  color: #8C827A;
  font-size: 0.88rem;
}
</style>

```

#### `frontend/src/components/ServiceNowFilterBuilder.vue`

```vue
<template>
  <div class="sn-filter-wrapper">
    <!-- Top Action Bar -->
    <div class="sn-topbar">
      <div class="sn-topbar-left">
        <button
          type="button"
          class="sn-icon-btn sn-funnel-toggle"
          :class="{ active: isOpen }"
          @click="toggleOpen"
          title="Toggle Filter Builder"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
          </svg>
          <span class="sn-toggle-label">Filters</span>
        </button>

        <button type="button" class="sn-btn sn-btn-primary" @click="applyFilter" title="Execute query">
          Run
        </button>

        <button type="button" class="sn-btn sn-btn-outline" @click="openSaveModal" title="Save current filter">
          Save Filters
        </button>

        <div class="sn-saved-dropdown-wrap">
          <button type="button" class="sn-btn sn-btn-outline" @click="showSavedDropdown = !showSavedDropdown">
            <span>{{ activeSavedFilterName || 'Presets' }}</span>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </button>
          <div v-if="showSavedDropdown" class="sn-dropdown-menu">
            <div class="sn-dropdown-header">Saved &amp; Preset Filters</div>
            <div
              v-for="sf in savedFilters"
              :key="sf.id"
              class="sn-dropdown-item"
              :class="{ selected: sf.name === activeSavedFilterName }"
              @click="loadSavedFilter(sf)"
            >
              <div class="sn-dropdown-item-text">
                <strong>{{ sf.name }}</strong>
                <span v-if="sf.description" class="sn-dropdown-item-desc">{{ sf.description }}</span>
              </div>
              <button
                v-if="sf.created_by !== 'system'"
                type="button"
                class="sn-dropdown-delete-btn"
                @click.stop="removeSavedFilter(sf.id)"
                title="Delete saved filter"
              >
                &times;
              </button>
            </div>
          </div>
        </div>

        <button type="button" class="sn-btn sn-btn-secondary" @click="addTopCondition('AND')">
          AND
        </button>

        <button type="button" class="sn-btn sn-btn-secondary" @click="addTopCondition('OR')">
          OR
        </button>

        <button type="button" class="sn-btn sn-btn-secondary" @click="addSortRule">
          *Add Sort
        </button>

        <button
          type="button"
          class="sn-icon-btn sn-pin-btn"
          :class="{ pinned: isPinned }"
          @click="isPinned = !isPinned"
          title="Pin filter open"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="17" x2="12" y2="22"></line>
            <path d="M5 17h14v-2l-2-3V5a2 2 0 0 0-2-2H9a2 2 0 0 0-2 2v7l-2 3v2z"></path>
          </svg>
        </button>

        <button
          v-if="hasActiveConditions"
          type="button"
          class="sn-btn sn-btn-text"
          @click="clearAllFilters"
          title="Reset to default"
        >
          Clear
        </button>
      </div>
    </div>

    <!-- Collapsible Filter Builder Body -->
    <div v-if="isOpen || isPinned" class="sn-filter-body">
      <div class="sn-condition-section-label">
        All of these conditions must be met
      </div>

      <!-- Condition Groups -->
      <div v-if="!filterGroups.length" class="sn-no-conditions">
        <em>No conditions applied. Showing all records. Click <strong>AND</strong> or <strong>OR</strong> to add filter conditions.</em>
      </div>

      <div
        v-for="(group, gIdx) in filterGroups"
        :key="gIdx"
        class="sn-group-block"
      >
        <div
          v-for="(cond, cIdx) in group.conditions"
          :key="cIdx"
          class="sn-condition-row"
        >
          <!-- Prefix label (empty for first, 'or' for subsequent in OR group) -->
          <div class="sn-cond-prefix">
            <span v-if="cIdx > 0" class="sn-prefix-tag">{{ group.logical_operator.toLowerCase() }}</span>
          </div>

          <!-- Field selector -->
          <select
            v-model="cond.field"
            class="sn-select sn-field-select"
            @change="onFieldChange(cond)"
          >
            <option v-for="(meta, fKey) in fieldsMeta" :key="fKey" :value="fKey">
              {{ meta.label }}
            </option>
          </select>

          <!-- Operator selector -->
          <select
            v-model="cond.operator"
            class="sn-select sn-operator-select"
            @change="onOperatorChange(cond)"
          >
            <option
              v-for="op in getOperatorsForField(cond.field)"
              :key="op.value"
              :value="op.value"
            >
              {{ op.label }}
            </option>
          </select>

          <!-- Value Input (Dynamic based on data type and operator) -->
          <div class="sn-value-input-container">
            <!-- No value needed for is_empty / is_not_empty -->
            <span v-if="cond.operator === 'is_empty' || cond.operator === 'is_not_empty'" class="sn-empty-placeholder">
              (no value required)
            </span>

            <!-- Multiselect listbox for 'is_one_of' and 'is_not_one_of' -->
            <div v-else-if="cond.operator === 'is_one_of' || cond.operator === 'is_not_one_of'" class="sn-multiselect-box">
              <select
                multiple
                v-model="cond.values"
                class="sn-multi-select"
                size="4"
              >
                <option
                  v-for="opt in getEnumOptions(cond.field)"
                  :key="opt"
                  :value="opt"
                >
                  {{ opt }}
                </option>
              </select>
            </div>

            <!-- Between Range for Numeric / Date -->
            <div v-else-if="cond.operator === 'between'" class="sn-between-inputs">
              <template v-if="getFieldType(cond.field) === 'date'">
                <input v-model="cond.value" type="date" class="sn-input sn-date-input" />
                <span class="sn-range-sep">and</span>
                <input v-model="cond.value_to" type="date" class="sn-input sn-date-input" />
              </template>
              <template v-else>
                <input v-model="cond.value" type="number" step="any" placeholder="Min" class="sn-input sn-num-input" />
                <span class="sn-range-sep">and</span>
                <input v-model="cond.value_to" type="number" step="any" placeholder="Max" class="sn-input sn-num-input" />
              </template>
            </div>

            <!-- Single Date input -->
            <input
              v-else-if="getFieldType(cond.field) === 'date'"
              v-model="cond.value"
              type="date"
              class="sn-input sn-date-input"
            />

            <!-- Single Enum dropdown for 'is' / 'is_not' -->
            <select
              v-else-if="getFieldType(cond.field) === 'enum'"
              v-model="cond.value"
              class="sn-select sn-val-select"
            >
              <option value="">-- Select --</option>
              <option
                v-for="opt in getEnumOptions(cond.field)"
                :key="opt"
                :value="opt"
              >
                {{ opt }}
              </option>
            </select>

            <!-- Single Numeric input -->
            <input
              v-else-if="getFieldType(cond.field) === 'numeric'"
              v-model="cond.value"
              type="number"
              step="any"
              placeholder="Score (0-20)"
              class="sn-input sn-num-input"
            />

            <!-- Standard text input with magnifying glass search icon -->
            <div v-else class="sn-text-search-wrap">
              <input
                v-model="cond.value"
                type="text"
                placeholder="Search value..."
                class="sn-input sn-text-input"
                @keyup.enter="applyFilter"
              />
              <span class="sn-search-icon">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
              </span>
            </div>
          </div>

          <!-- Trailing Row Actions (AND, OR, Remove) -->
          <div class="sn-row-actions">
            <button
              type="button"
              class="sn-btn-action sn-btn-and"
              @click="addConditionToGroup(gIdx, 'AND')"
              title="Add condition with AND"
            >
              AND
            </button>
            <button
              type="button"
              class="sn-btn-action sn-btn-or"
              @click="addConditionToGroup(gIdx, 'OR')"
              title="Add condition with OR"
            >
              OR
            </button>
            <button
              type="button"
              class="sn-btn-remove"
              @click="removeCondition(gIdx, cIdx)"
              title="Delete condition"
            >
              &times;
            </button>
          </div>
        </div>
      </div>

      <!-- Sorting Controls Section -->
      <div v-if="sortRules.length" class="sn-sort-section">
        <div class="sn-sort-title">Order by:</div>
        <div v-for="(rule, sIdx) in sortRules" :key="sIdx" class="sn-sort-row">
          <select v-model="rule.field" class="sn-select sn-sort-select">
            <option v-for="(meta, fKey) in fieldsMeta" :key="fKey" :value="fKey">
              {{ meta.label }}
            </option>
          </select>
          <select v-model="rule.direction" class="sn-select sn-sort-dir">
            <option value="desc">Descending (Z-A / High-Low)</option>
            <option value="asc">Ascending (A-Z / Low-High)</option>
          </select>
          <button
            type="button"
            class="sn-btn-remove"
            @click="removeSortRule(sIdx)"
            title="Remove sort rule"
          >
            &times;
          </button>
        </div>
      </div>
    </div>

    <!-- Active Breadcrumb Summary String (ServiceNow-Style) -->
    <div class="sn-breadcrumb-bar">
      <span class="sn-breadcrumb-text">
        <span class="sn-crumb-all">All</span>
        <template v-if="readableSummary && readableSummary !== 'All'">
          <span class="sn-crumb-sep">&gt;</span>
          <span class="sn-crumb-query">{{ readableSummary.replace(/^All\s*>\s*/, '') }}</span>
        </template>
      </span>
      <span v-if="totalCount !== null" class="sn-total-badge">
        {{ totalCount }} {{ totalCount === 1 ? 'record' : 'records' }}
      </span>
    </div>

    <!-- Save Filter Modal -->
    <div v-if="showSaveModal" class="sn-modal-overlay" @click.self="showSaveModal = false">
      <div class="sn-modal-card">
        <h3>Save Current Filter</h3>
        <p class="sn-modal-desc">Save this filter configuration to easily access it later.</p>

        <div class="sn-form-group">
          <label>Filter Name <span class="req">*</span></label>
          <input
            v-model="newFilterName"
            type="text"
            placeholder="e.g. Critical High-Priority Audits"
            class="sn-input"
            autofocus
          />
        </div>

        <div class="sn-form-group">
          <label>Description (Optional)</label>
          <input
            v-model="newFilterDesc"
            type="text"
            placeholder="Brief explanation of this filter"
            class="sn-input"
          />
        </div>

        <div class="sn-modal-actions">
          <button type="button" class="sn-btn sn-btn-outline" @click="showSaveModal = false">
            Cancel
          </button>
          <button
            type="button"
            class="sn-btn sn-btn-primary"
            :disabled="!newFilterName.trim()"
            @click="submitSaveFilter"
          >
            Save Filter
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { getSavedFilters, createSavedFilter, deleteSavedFilter } from "../api";

const props = defineProps({
  totalCount: {
    type: Number,
    default: null,
  },
  readableSummary: {
    type: String,
    default: "All",
  },
});

const emit = defineEmits(["filter-changed", "run-filter"]);

// State
const isOpen = ref(true);
const isPinned = ref(true);
const showSavedDropdown = ref(false);
const showSaveModal = ref(false);
const newFilterName = ref("");
const newFilterDesc = ref("");
const savedFilters = ref([]);
const activeSavedFilterName = ref("");

// Filter Groups: list of { logical_operator: 'AND'|'OR', conditions: [...] }
const filterGroups = ref([
  {
    logical_operator: "AND",
    conditions: [
      { field: "company_name", operator: "contains", value: "", value_to: null, values: [] }
    ]
  }
]);

// Sort rules
const sortRules = ref([
  { field: "submitted_at", direction: "desc" }
]);

// Fields metadata & verified schema definitions
const fieldsMeta = {
  // ── Respondent identity ─────────────────────────────────────────────────
  company_name: {
    label: "Organization Name",
    type: "text",
  },
  name: {
    label: "Respondent Name",
    type: "text",
  },
  email: {
    label: "Recipient Email",
    type: "text",
  },
  designation: {
    label: "Job Role / Designation",
    type: "text",
  },
  // ── Demographics (sourced from answers JSONB, surfaced to top-level) ────
  function: {
    label: "Function / Department",
    type: "enum",
    options: [
      "Administration", "Engineering", "ESG / Sustainability", "Finance",
      "HR / People", "Legal & Compliance", "Manufacturing / Production",
      "Marketing & Communications", "Operations", "Project Management",
      "Quality Assurance / Quality Control", "Research & Development (R&D)",
      "Sales & Business Development", "Supply Chain / Procurement / Logistics",
      "Technology / IT / Product Management", "Other",
    ],
  },
  role: {
    label: "Role Level",
    type: "enum",
    options: [
      "Individual Contributor / Team Member",
      "People Manager/Supervisor",
      "Head of Function/Director",
      "VP / Senior Leader",
      "C-Suite / Executive",
      "Board Member / Trustee",
      "Consultant / Advisor",
      "Other",
    ],
  },
  country: {
    label: "Country",
    type: "text",
  },
  state_ut: {
    label: "State / UT (India)",
    type: "text",
  },
  gender: {
    label: "Gender Identity",
    type: "enum",
    options: [
      "Man", "Woman", "Non-binary / Gender non-conforming",
      "Prefer not to say", "Other gender identity",
    ],
  },
  is_pwd: {
    label: "Person with Disability (PwD)",
    type: "enum",
    options: ["Yes", "No", "Prefer not to say"],
  },
  is_neurodivergent: {
    label: "Neurodivergent",
    type: "enum",
    options: ["Yes", "No", "Prefer not to say"],
  },
  is_marginalized: {
    label: "Underrepresented / Marginalized",
    type: "enum",
    options: ["Yes", "No", "Prefer not to say"],
  },
  // ── Audit outcome ───────────────────────────────────────────────────────
  status: {
    label: "Status",
    type: "enum",
    options: ["pending", "sending", "sent", "fa
```
> _Truncated to 16000 bytes — see full file in the source repo._

#### `frontend/src/composables/useAccessibility.js`

```js
import { ref, onMounted } from "vue";

export function useAccessibility() {
  const dyslexiaMode = ref(false);
  const largeLineHeight = ref(false);
  const highContrast = ref(false);

  function loadSettings() {
    const saved = localStorage.getItem("nd_accessibility");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        dyslexiaMode.value = !!parsed.dyslexiaMode;
        largeLineHeight.value = !!parsed.largeLineHeight;
        highContrast.value = !!parsed.highContrast;
      } catch (e) {
        console.error("Accessibility settings parse failed", e);
      }
    }
  }

  function applySettings() {
    const body = document.body;
    
    if (dyslexiaMode.value) {
      body.classList.add("accessibility-dyslexia");
    } else {
      body.classList.remove("accessibility-dyslexia");
    }

    if (largeLineHeight.value) {
      body.classList.add("accessibility-lineheight");
    } else {
      body.classList.remove("accessibility-lineheight");
    }

    if (highContrast.value) {
      body.classList.add("accessibility-highcontrast");
    } else {
      body.classList.remove("accessibility-highcontrast");
    }

    localStorage.setItem("nd_accessibility", JSON.stringify({
      dyslexiaMode: dyslexiaMode.value,
      largeLineHeight: largeLineHeight.value,
      highContrast: highContrast.value
    }));
  }

  function toggleDyslexia() {
    dyslexiaMode.value = !dyslexiaMode.value;
    applySettings();
  }

  function toggleLineHeight() {
    largeLineHeight.value = !largeLineHeight.value;
    applySettings();
  }

  function toggleHighContrast() {
    highContrast.value = !highContrast.value;
    applySettings();
  }

  onMounted(() => {
    loadSettings();
    applySettings();
  });

  return {
    dyslexiaMode,
    largeLineHeight,
    highContrast,
    toggleDyslexia,
    toggleLineHeight,
    toggleHighContrast
  };
}

```

#### `frontend/src/composables/useDraftSaving.js`

```js
import { ref, watch, onUnmounted } from "vue";

const RESUME_SESSION_MS = 30 * 60 * 1000; // 30 minutes

export function useDraftSaving(formData, currentStep, API_BASE = "/api") {
  const isSaving = ref(false);
  const saveError = ref("");
  const resumeUrl = ref("");
  const draftId = ref(localStorage.getItem("nd_draft_id") || null);

  // Restore from LocalStorage — ONLY if the user arrived via a resume link.
  //
  // Flow:
  //   Fresh visit  → wipe any leftover draft, form starts blank.
  //   Resume link  → ResumeDraft.vue sets "nd_resume_ready" + "nd_resume_at" timestamp,
  //                  we restore the draft and start a 30-minute session window.
  //   After 30 min → draft is treated as expired; next load starts blank.
  //   Start Fresh  → call clearDraft() which wipes everything immediately.
  function restoreLocalDraft() {
    const resumeReady = localStorage.getItem("nd_resume_ready");

    if (!resumeReady) {
      // Fresh visit — wipe any leftover draft so the form is always blank
      localStorage.removeItem("nd_draft_state");
      localStorage.removeItem("nd_draft_id");
      localStorage.removeItem("nd_resume_at");
      return;
    }

    // Check 30-minute session window
    const resumedAt = parseInt(localStorage.getItem("nd_resume_at") || "0", 10);
    const expired = Date.now() - resumedAt > RESUME_SESSION_MS;

    // Consume the flag immediately (single-use regardless of expiry)
    localStorage.removeItem("nd_resume_ready");

    if (expired) {
      localStorage.removeItem("nd_draft_state");
      localStorage.removeItem("nd_draft_id");
      localStorage.removeItem("nd_resume_at");
      return;
    }

    const saved = localStorage.getItem("nd_draft_state");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        Object.assign(formData, parsed.formData);
        currentStep.value = parsed.currentStep;
        if (parsed.draftId) draftId.value = parsed.draftId;
      } catch (e) {
        console.error("Failed to parse local draft", e);
      }
    }
  }

  // Auto-save to LocalStorage (includes draftId so it survives page reloads within session)
  function saveToLocal() {
    const payload = {
      formData: { ...formData },
      currentStep: currentStep.value,
      draftId: draftId.value,
    };
    localStorage.setItem("nd_draft_state", JSON.stringify(payload));
  }

  // Sync to Backend
  async function syncToBackend() {
    isSaving.value = true;
    saveError.value = "";
    try {
      const response = await fetch(`${API_BASE}/drafts/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          draft_id: draftId.value || null,
          email: formData.email,
          company_name: formData.company_name,
          form_state: formData,
          current_step: currentStep.value
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Failed to save draft.");

      draftId.value = data.draft_id;
      localStorage.setItem("nd_draft_id", data.draft_id);
      resumeUrl.value = data.resume_url;
      return data.resume_url;
    } catch (e) {
      saveError.value = e.message;
      throw e;
    } finally {
      isSaving.value = false;
    }
  }

  function clearDraft() {
    localStorage.removeItem("nd_draft_state");
    localStorage.removeItem("nd_draft_id");
    localStorage.removeItem("nd_resume_ready");
    localStorage.removeItem("nd_resume_at");
    draftId.value = null;
    resumeUrl.value = "";
  }

  // 30s auto-save to localStorage
  const localInterval = setInterval(saveToLocal, 30000);

  // Also save on every form/step change
  watch([formData, currentStep], saveToLocal, { deep: true });

  onUnmounted(() => {
    clearInterval(localInterval);
  });

  return {
    isSaving,
    saveError,
    resumeUrl,
    draftId,
    restoreLocalDraft,
    saveToLocal,
    syncToBackend,
    clearDraft,
  };
}

```

#### `frontend/src/main.js`

```js
import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import "./style.css";
import { getMsalInstance, completeAdminLogin, clearMsalCache } from "./authConfig";

function mountApp() {
    createApp(App).use(router).mount("#app");
}

async function handleAuthRedirect() {
    try {
        const msalInstance = await getMsalInstance();
        const response = await msalInstance.handleRedirectPromise();

        if (response?.account) {
            const result = await completeAdminLogin(response);
            if (result.ok) {
                mountApp();
                await router.isReady();
                await router.replace("/admin/dashboard");
                return;
            }
            sessionStorage.setItem(
                "nd_auth_error",
                `Access denied: ${result.email || "your account"} is not in admin_users.`
            );
            clearMsalCache();
        }
    } catch (error) {
        console.error("Auth redirect error:", error);
        sessionStorage.setItem("nd_auth_error", error.message || "Authentication failed.");
        clearMsalCache();
    }

    mountApp();
}

handleAuthRedirect();

```

#### `frontend/src/router/index.js`

```js
import { createRouter, createWebHistory } from "vue-router";
import AuditForm        from "../views/AuditForm.vue";
import AdminLogin       from "../views/AdminLogin.vue";
import Overview         from "../views/Overview.vue";
import Submissions      from "../views/Submissions.vue";
import SubmissionDetail from "../views/SubmissionDetail.vue";
import Analytics        from "../views/Analytics.vue";
import Settings         from "../views/Settings.vue";
import Support          from "../views/Support.vue";
import UserManagement   from "../views/UserManagement.vue";
import ResumeDraft      from "../views/ResumeDraft.vue";
import OrgLogin         from "../views/OrgLogin.vue";
import OrgVerify        from "../views/OrgVerify.vue";
import OrgDashboard     from "../views/OrgDashboard.vue";
import Organisations    from "../views/Organisations.vue";
import BookCall         from "../views/BookCall.vue";
import FormBuilder      from "../views/FormBuilder.vue";
import SuperDashboard    from "../views/SuperDashboard.vue";

const routes = [
  { path: "/",                        component: AuditForm },
  { path: "/audit",                   component: AuditForm },
  { path: "/book-a-call",             component: BookCall },
  { path: "/portal",                  component: AdminLogin },
  { path: "/admin",                   redirect: "/GPadmin" },
  { path: "/GPadmin",                 component: AdminLogin },
  { path: "/gpadmin",                 redirect: "/GPadmin" },
  { path: "/admin/dashboard",         component: Overview,         meta: { requiresAuth: true } },
  { path: "/admin/submissions",       component: Submissions,      meta: { requiresAuth: true } },
  { path: "/admin/submissions/:id([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})",   component: SubmissionDetail, meta: { requiresAuth: true } },
  { path: "/admin/analytics",         component: Analytics,        meta: { requiresAuth: true } },
  { path: "/admin/settings",          component: Settings,         meta: { requiresAuth: true } },
  { path: "/admin/support",           component: Support,          meta: { requiresAuth: true } },
  { path: "/admin/users",             component: UserManagement,   meta: { requiresAuth: true, requiresSuper: true } },
  { path: "/admin/super-dashboard",   component: SuperDashboard,  meta: { requiresAuth: true, requiresSuper: true } },
  { path: "/admin/system-dashboard",  redirect: "/admin/super-dashboard" },
  { path: "/admin/organisations",     component: Organisations,    meta: { requiresAuth: true } },
  { path: "/admin/form-builder",      component: FormBuilder,      meta: { requiresAuth: true } },

  // Public / org routes
  { path: "/invite/:token",           component: AuditForm },
  { path: "/resume",                  component: ResumeDraft },
  { path: "/org/login",               component: OrgLogin },
  { path: "/org/verify",              component: OrgVerify },
  { path: "/org/dashboard",           component: OrgDashboard,     meta: { requiresOrgAuth: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  if (to.meta.requiresAuth && !sessionStorage.getItem("nd_auth")) {
    return "/GPadmin";
  }
  if (to.meta.requiresSuper && sessionStorage.getItem("nd_role") !== "super") {
    return "/admin/dashboard";
  }
  if (to.meta.requiresOrgAuth && !localStorage.getItem("org_token")) {
    return "/org/login";
  }
});

export default router;

```

#### `frontend/src/style.css`

```css
/* ==========================================================================
   NIWI — Unified Enterprise Design System (Tokens, Resets & Components)
   ========================================================================== */

:root {
  /* Core NIWI Color Palette */
  --primary: #161057;
  --primary-hover: #0F0A42;
  --primary-rgb: 22, 16, 87;
  --accent: #04907C;
  --accent-hover: #037A69;
  --accent-rgb: 4, 144, 124;
  --accent-soft: rgba(4, 144, 124, 0.08);

  /* Destructive & Warning Palette */
  --danger: #E05A47;
  --danger-hover: #C53030;
  --danger-soft: #FEE2E2;
  --warning: #D97706;
  --warning-soft: #FEF3C7;
  --success: #059669;
  --success-soft: #D1FAE5;

  /* Neutral & Backgrounds */
  --bg: #FAFAF8;
  --bg-cream: #FAF9F5;
  --surface: #FFFFFF;
  --surface-alt: #F8FAFC;
  --border: rgba(22, 16, 87, 0.10);
  --border-strong: rgba(22, 16, 87, 0.20);
  --border-light: #E2E8F0;

  /* Typography Colors */
  --text-main: #1E293B;
  --text-muted: #64748B;
  --text-subtle: #94A3B8;

  /* Typography Font Families */
  --font-heading: 'Fraunces', serif;
  --font-body: 'Geist', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-mono: 'Geist Mono', 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace;

  /* Elevation Shadows */
  --shadow-sm: 0 1px 3px rgba(22, 16, 87, 0.04);
  --shadow-md: 0 4px 14px rgba(22, 16, 87, 0.06);
  --shadow-lg: 0 8px 24px rgba(22, 16, 87, 0.09);
  --shadow-card: 0 2px 10px rgba(22, 16, 87, 0.03);

  /* Border Radii */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 18px;
  --radius-full: 9999px;
}

/* Global resets & typography */
html, body {
  margin: 0;
  padding: 0;
  overflow-x: hidden;
  max-width: 100vw;
  background-color: var(--bg);
  color: var(--text-main);
  font-family: var(--font-body);
  -webkit-text-size-adjust: 100%;
  -webkit-font-smoothing: antialiased;
}

*, *::before, *::after {
  box-sizing: border-box;
}

img, video {
  max-width: 100%;
}

h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-heading);
  color: var(--primary);
  font-weight: 700;
  letter-spacing: -0.015em;
  margin: 0;
}

p {
  margin: 0;
}

/* Standardized Button Styles */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-family: var(--font-body);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  border: 1.5px solid transparent;
  line-height: 1.4;
  text-decoration: none;
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn-primary {
  background-color: var(--accent);
  color: #FFFFFF !important;
  border-color: var(--accent);
}
.btn-primary:hover:not(:disabled) {
  background-color: var(--accent-hover);
  border-color: var(--accent-hover);
  box-shadow: 0 2px 8px rgba(4, 144, 124, 0.25);
}

.btn-outline {
  background-color: #FFFFFF;
  color: var(--primary);
  border-color: rgba(22, 16, 87, 0.25);
}
.btn-outline:hover:not(:disabled) {
  background-color: #F8FAFC;
  border-color: var(--primary);
}

.btn-danger {
  background-color: var(--danger);
  color: #FFFFFF;
  border-color: var(--danger);
}
.btn-danger:hover:not(:disabled) {
  background-color: var(--danger-hover);
  border-color: var(--danger-hover);
}

.btn-danger-outline {
  background-color: #FFFFFF;
  color: var(--danger);
  border-color: #FECACA;
}
.btn-danger-outline:hover:not(:disabled) {
  background-color: var(--danger-soft);
  border-color: var(--danger);
}

.btn-sm {
  padding: 5px 12px;
  font-size: 0.8rem;
  border-radius: 6px;
}

.btn-lg {
  padding: 11px 22px;
  font-size: 1rem;
  border-radius: 8px;
}

/* Standardized Card Styles */
.card, .niwi-card {
  background: var(--surface);
  border: 1.5px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 20px;
  box-sizing: border-box;
}

/* Standardized Status Badges */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 9px;
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: 700;
  border: 1px solid currentColor;
  line-height: 1.3;
}

.badge-level-1, .badge-l1 {
  background: #FEE2E2;
  color: #991B1B;
  border-color: #FECACA;
}

.badge-level-2, .badge-l2 {
  background: #FEF3C7;
  color: #92400E;
  border-color: #FDE68A;
}

.badge-level-3, .badge-l3 {
  background: #D1FAE5;
  color: #065F46;
  border-color: #A7F3D0;
}

.badge-success, .badge-delivered, .badge-sent {
  background: #ECFDF5;
  color: #047857;
  border-color: #A7F3D0;
}

.badge-warning, .badge-pending {
  background: #FFFBEB;
  color: #B45309;
  border-color: #FDE68A;
}

.badge-danger {
  background: #FEF2F2;
  color: #B91C1C;
  border-color: #FECACA;
}

.badge-neutral {
  background: #F1F5F9;
  color: #475569;
  border-color: #CBD5E1;
}

/* Standardized Inputs */
input[type="text"],
input[type="email"],
input[type="password"],
input[type="number"],
input[type="date"],
select,
textarea {
  font-family: var(--font-body);
  font-size: 0.875rem;
  color: var(--text-main);
  background: #FFFFFF;
  border: 1.5px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: 8px 12px;
  outline: none;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  box-sizing: border-box;
}

input:focus,
select:focus,
textarea:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(22, 16, 87, 0.08);
}

/* Responsive Table Wrapper */
.table-container, .niwi-table-container {
  width: 100%;
  min-width: 0;
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  background: #FFFFFF;
  border: 1.5px solid rgba(22, 16, 87, 0.10);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
}

/* Universal Animations */
.animate-in {
  animation: fadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

```

#### `frontend/src/utils/csvExport.js`

```js
/**
 * csvExport.js — Detailed CSV export for NIWI audit submissions
 * Includes: respondent info, all 40 Q&A responses with question text, section scores, overall score
 */

// Full question labels matching AuditForm.vue sections
const QUESTION_LABELS = {
  q5:  "LC1 – Strategy & Direction",
  q6:  "LC2 – Executive Accountability",
  q7:  "LC3 – Leadership Training & Modelling",
  q8:  "LC4 – Employee Resource Group",
  q9:  "LC5 – Public Commitment",
  q10: "RO1 – Inclusive Job Design",
  q11: "RO2 – Transparent Application Process",
  q12: "RO3 – Skills-Based Assessment",
  q13: "RO4 – Flexible Interviews",
  q14: "RO5 – Structured Onboarding",
  q15: "WE1 – Lifecycle Adjustments",
  q16: "WE2 – Clear Adjustment Pathways",
  q17: "WE3 – Manager & HR Training",
  q18: "WE4 – Built-In Inclusive Practices",
  q19: "WE5 – Regular Policy Review",
  q20: "BE1 – Universal Design Principles",
  q21: "BE2 – Sensory Impact Consideration",
  q22: "BE3 – Varied Workspaces",
  q23: "BE4 – Quiet & Low-Stimulation Spaces",
  q24: "BE5 – Hybrid & Remote Balance",
  q25: "TM1 – Inclusive Leadership Training",
  q26: "TM2 – Structured Feedback",
  q27: "TM3 – Wellbeing & Coaching Support",
  q28: "TM4 – Accessible Learning & Development",
  q29: "TM5 – Strengths-Based Development",
  q30: "CA1 – Neuro-Inclusive Communication",
  q31: "CA2 – Clear & Structured Communication",
  q32: "CA3 – Accessible Formats",
  q33: "CA4 – Inclusive Language",
  q34: "CA5 – Feedback & Improvement",
  q35: "PC1 – Neuro-Inclusive Design",
  q36: "PC2 – Multiple Contact Channels",
  q37: "PC3 – Sensory-Aware Environments",
  q38: "PC4 – Staff Neurodiversity Training",
  q39: "PC5 – Regular Inclusivity Assessment",
  q40: "SP1 – Neuro-Inclusive Supplier Comms",
  q41: "SP2 – Inclusive Procurement Criteria",
  q42: "SP3 – Procurement Staff Training",
  q43: "SP4 – Multiple Supplier Contact Methods",
  q44: "SP5 – Supplier Feedback Mechanisms",
};

const SECTION_SCORE_LABELS = {
  lc: "Leadership & Culture",
  ro: "Recruitment & Onboarding",
  we: "Work Environment & Adjustments",
  be: "Built Environment & Sensory",
  tm: "Talent Management & Development",
  ca: "Communication & Accessibility",
  pc: "Products & Customer Experience",
  sp: "Suppliers & Procurement",
};

function escapeCSV(val) {
  if (val === null || val === undefined) return "";
  const str = String(val);
  if (str.includes(",") || str.includes('"') || str.includes("\n")) {
    return `"${str.replace(/"/g, '""')}"`;
  }
  return str;
}

function formatDate(iso) {
  if (!iso) return "";
  const d = new Date(iso);
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

/**
 * Build CSV rows for one or multiple submissions.
 * Each submission = one row with all fields.
 */
export function buildDetailedCSV(submissions) {
  const headers = [
    // Respondent info
    "Submitted Date",
    "Name",
    "Designation",
    "Organisation",
    "Email",
    "Contact Number",
    "Physical Workspace",
    "Has Suppliers",
    // All 40 questions
    ...Object.values(QUESTION_LABELS),
    // Section scores
    ...Object.values(SECTION_SCORE_LABELS).map(s => `${s} Score`),
    ...Object.values(SECTION_SCORE_LABELS).map(s => `${s} Level`),
    // Overall
    "Overall Score (/20)",
    "Overall Maturity Level",
    "Status",
  ];

  const rows = submissions.map(s => {
    const qAnswers = Object.keys(QUESTION_LABELS).map(qk => s[qk] || "");
    const sectionScores = Object.keys(SECTION_SCORE_LABELS).map(k => s[`${k}_score`] ?? "N/A");
    const sectionLevels = Object.keys(SECTION_SCORE_LABELS).map(k => s[`${k}_level`] || "N/A");

    return [
      formatDate(s.submitted_at),
      s.name || "",
      s.designation || "",
      s.company_name || "",
      s.email || "",
      s.contact_number || "",
      s.has_physical_workspace || "",
      s.has_suppliers || "",
      ...qAnswers,
      ...sectionScores,
      ...sectionLevels,
      s.overall_avg ?? "",
      s.overall_level || "",
      s.status || "",
    ];
  });

  const csvLines = [
    headers.map(escapeCSV).join(","),
    ...rows.map(row => row.map(escapeCSV).join(",")),
  ];

  return csvLines.join("\n");
}

/**
 * Trigger a browser download of a CSV string.
 */
export function downloadCSV(csvString, filename) {
  const blob = new Blob(["\uFEFF" + csvString], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/**
 * Download a single submission as CSV.
 */
export function downloadSingleSubmission(submission) {
  const csv = buildDetailedCSV([submission]);
  const date = formatDate(submission.submitted_at).replace(/ /g, "-");
  const org = (submission.company_name || "submission").replace(/[^a-z0-9]/gi, "_");
  downloadCSV(csv, `NIWI_${org}_${date}.csv`);
}

/**
 * Download multiple submissions as CSV with optional date range label.
 */
export function downloadFilteredSubmissions(submissions, dateFrom, dateTo) {
  const csv = buildDetailedCSV(submissions);
  const from = dateFrom || "all";
  const to = dateTo || "time";
  downloadCSV(csv, `NIWI_submissions_${from}_to_${to}.csv`);
}

```

_…and 22 more file(s) not shown._

## Improvements & refactors

- [keep-behavior] Formalize typing and input constraints for enhanced runtime validation.
- [keep-behavior] Expand automated test coverage for failure modes and timeouts.
- [keep-behavior] Optimize memory footprint and eliminate unreferenced legacy helpers.


## Definition of done

- [ ] Every functional requirement is implemented and covered by a test.
- [ ] Every acceptance-criteria scenario passes (including the failure paths).
- [ ] Every operation this unit owns in `architecture/INTERFACES.md` responds correctly.
- [ ] Every entity it writes matches `architecture/DATA-MODEL.md` (fields, types, constraints).
- [ ] Every write is satisfiable against the schema: no required (NOT NULL, no-default) column or foreign key is left unfilled; anonymous/public operations write only to anonymous-capable entities (no owner FK).
- [ ] Every enum/domain value this unit uses is one of the members fully enumerated in `architecture/DATA-MODEL.md`.
- [ ] Every edge case & failure mode above is handled.
- [ ] `node scripts/analyze.mjs --check --out <out>` passes — no unresolved agent callouts or placeholders, and every reference resolves.

