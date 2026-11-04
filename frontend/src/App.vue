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
            <router-link to="/admin/dashboard" class="top-nav-link" :class="{ active: route.path === '/admin/dashboard' }">
              Dashboard
            </router-link>
            <router-link to="/admin/submissions" class="top-nav-link" :class="{ active: route.path.includes('submissions') }">
              Submissions
            </router-link>
            <router-link to="/admin/analytics" class="top-nav-link" :class="{ active: route.path === '/admin/analytics' }">
              Analytics
            </router-link>
            <router-link to="/admin/organisations" class="top-nav-link" :class="{ active: route.path === '/admin/organisations' }">
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
import { getSettings, toggleNotifications } from "./api";
import { getMsalInstance, clearMsalCache } from "./authConfig";

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
  --text-subtle: #94A3B8;
  --bg: #FAFAF8;
  --surface: #FFFFFF;
  --border: rgba(22, 16, 87, 0.08);
  --border-strong: rgba(22, 16, 87, 0.16);
  --accent: #04907C;
  --accent-hover: #037A69;
  --accent-rgb: 4, 144, 124;
  --accent-soft: rgba(4, 144, 124, 0.08);
  --c-bg: var(--bg);
  --c-white: var(--surface);
  --c-accent: var(--accent);
  --c-border: var(--border);

  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(22, 16, 87, 0.04);
  --shadow-md: 0 4px 14px rgba(22, 16, 87, 0.05);
  --shadow-lg: 0 8px 24px rgba(22, 16, 87, 0.08);

  /* Typography */
  --font-body: 'Geist', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-heading: 'Fraunces', serif;
  --line-height-body: 1.6;
  --line-height-heading: 1.2;
}

*, *::before, *::after { 
  box-sizing: border-box; 
  margin: 0; 
  padding: 0; 
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}

body {
  font-family: var(--font-body);
  line-height: var(--line-height-body);
  background-color: var(--bg);
  color: var(--primary);
}

body::before { content: none; }

/* Accessibility classes */
body.accessibility-dyslexia {
  --font-body: 'OpenDyslexic', sans-serif !important;
}
body.accessibility-lineheight {
  --line-height-body: 2.1 !important;
}
body.accessibility-highcontrast {
  background: #000000 !important;
  color: #FFFFFF !important;
  --bg: #111 !important;
  --surface: #000 !important;
  --border: #fff !important;
  --c-bg: #111 !important;
  --c-white: #000 !important;
}

body.accessibility-highcontrast .card,
body.accessibility-highcontrast .info-item,
body.accessibility-highcontrast input,
body.accessibility-highcontrast button,
body.accessibility-highcontrast .step-card,
body.accessibility-highcontrast .opt-btn {
  background: #000 !important;
  color: #fff !important;
  border-color: #fff !important;
}

#app, .app-shell {
  position: relative;
}

h1, h2, h3, .brand-name, .stat-value, .page-header h1,
.chart-title, .step-tag, .topbar-title {
  font-family: var(--font-heading);
  line-height: var(--line-height-heading);
  font-weight: 700;
  letter-spacing: -0.02em;
}

#app-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  min-height: 100dvh;
  width: 100%;
}

/* Public form/login */
.public-shell {
  flex: 1;
  width: 100%;
  min-width: 0;
  height: 100vh;
  height: 100dvh;
  max-height: 100vh;
  max-height: 100dvh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: transparent;
  padding: 0;
}

/* Main area */
.admin-layout {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--bg);
  box-sizing: border-box;
}

/* High-End Sticky Top Navbar */
.top-navbar {
  position: sticky;
  top: 0;
  z-index: 500;
  width: 100%;
  background: #FAF9F5;
  border-bottom: 1.5px solid rgba(22, 16, 87, 0.12);
  box-shadow: 0 2px 10px rgba(22, 16, 87, 0.03);
}

.topbar-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 24px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.topbar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  flex-shrink: 0;
}

.topbar-logo {
  height: 38px;
  width: auto;
  object-fit: contain;
}

.topbar-brand-title {
  font-family: var(--font-heading);
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--primary);
  letter-spacing: -0.02em;
}

.topbar-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  justify-content: center;
}

.top-nav-link {
  font-family: var(--font-body);
  font-size: 0.9rem;
  font-weight: 600;
  color: #475569;
  text-decoration: none;
  padding: 8px 14px;
  border-radius: 99px;
  white-space: nowrap;
  flex-shrink: 0;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.top-nav-link:hover {
  color: var(--primary);
  background: rgba(22, 16, 87, 0.05);
}

.top-nav-link.active {
  color: var(--primary);
  background: rgba(22, 16, 87, 0.1);
  font-weight: 700;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: clamp(8px, 2vw, 20px);
  flex-shrink: 0;
}

.mobile-nav-toggle {
  display: none;
  background: #FFFFFF;
  border: 1.5px solid var(--border);
  border-radius: 8px;
  width: 44px;
  height: 44px;
  min-width: 44px;
  min-height: 44px;
  align-items: center;
  justify-content: center;
  color: var(--primary);
  cursor: pointer;
  transition: all 0.15s ease;
}

.mobile-nav-toggle:focus {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.mobile-nav-menu {
  display: flex;
  flex-direction: column;
  background: #FFFFFF;
  border-bottom: 1.5px solid var(--border);
  padding: 16px 20px;
  gap: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  max-height: calc(100vh - 72px);
  overflow-y: auto;
}

.mobile-nav-link {
  font-size: 0.95rem;
  font-weight: 600;
  color: #475569;
  text-decoration: none;
  padding: 12px 16px;
  border-radius: 8px;
  min-height: 44px;
  display: flex;
  align-items: center;
  transition: all 0.15s;
}

.mobile-nav-link:hover, .mobile-nav-link.active {
  background: rgba(22, 16, 87, 0.06);
  color: var(--primary);
}

.mobile-nav-divider {
  height: 1px;
  background: var(--border);
  margin: 6px 0;
}

.mobile-logout {
  color: #C0392B !important;
}




.header-powered {
  display: flex; align-items: center; gap: 8px;
  padding-right: 24px;
  border-right: 2px solid rgba(0,0,0,0.06);
}
.powered-label {
  font-size: 0.68rem; color: var(--text-muted); font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.08em;
}
.powered-logo {
  height: 24px; width: auto; object-fit: contain;
}

.share-audit-btn {
  background: var(--surface); color: var(--primary);
  border: 1px solid var(--border); border-radius: 99px;
  padding: 10px 20px; font-size: 0.875rem; font-weight: 600;
  cursor: pointer; text-decoration: none; display: flex; align-items: center; gap: 8px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); font-family: var(--font-body);
}
.share-audit-btn:hover { 
  background: var(--bg); 
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}
.share-audit-btn:active {
  transform: translateY(1px);
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

.icon-btn {
  width: 44px; height: 44px; border-radius: 50%;
  border: 1px solid var(--border); background: var(--surface);
  display: grid; place-items: center; cursor: pointer; color: var(--primary);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.icon-btn:hover { 
  transform: translateY(-1px); 
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
}
.icon-btn:active {
  transform: translateY(1px);
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.icon-btn:focus {
  outline: 2px solid var(--accent); outline-offset: 2px;
}
.icon-btn.bell-on { background: var(--accent); color: var(--surface); }

.bell-wrap { position: relative; }
.bell-badge {
  position: absolute; top: 4px; right: 4px;
  width: 10px; height: 10px; border-radius: 50%;
  background: #ff4444; border: 2px solid var(--surface);
}
.bell-popover {
  position: absolute; top: calc(100% + 12px); right: 0;
  width: min(290px, calc(100vw - 24px)); max-width: calc(100vw - 24px); padding: 16px;
  background: var(--surface); border: 1.5px solid var(--border);
  border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  z-index: 200;
  animation: fadeUp 0.3s cubic-bezier(0.4, 0, 0.2, 1) both;
}
.bell-pop-title {
  font-size: 0.85rem; font-weight: 700; color: var(--primary);
  margin-bottom: 8px; font-family: var(--font-body);
}
.bell-pop-text { font-size: 0.8rem; color: var(--text-muted); line-height: 1.5; margin-bottom: 8px; }
.bell-pop-email { font-size: 0.78rem; color: var(--primary); font-weight: 600; margin-bottom: 8px; }
.bell-pop-warn { font-size: 0.78rem; color: #C0392B; margin-bottom: 8px; }
.bell-pop-link {
  font-size: 0.8rem; font-weight: 600; color: var(--primary);
  text-decoration: none; display: inline-block;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.bell-pop-link:hover { text-decoration: underline; color: var(--accent); }
.bell-pop-msg { font-size: 0.78rem; margin-top: 12px; font-weight: 600; }
.bell-pop-msg.success { color: var(--accent); }
.bell-pop-msg.error { color: #C0392B; }

.profile-wrap { position: relative; }
.avatar {
  width: 44px; height: 44px; border-radius: 50%;
  background: var(--primary); color: var(--surface); cursor: pointer;
  display: grid; place-items: center;
  font-size: 0.95rem; font-weight: 600;
  border: none;
  font-family: var(--font-body);
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.avatar:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.12); }
.avatar:active { transform: translateY(1px); box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
.avatar:focus { outline: 2px solid var(--accent); outline-offset: 2px; }

.profile-popover {
  position: absolute; top: calc(100% + 12px); right: 0;
  width: min(230px, calc(100vw - 24px)); max-width: calc(100vw - 24px);
  background: var(--surface); border: 1.5px solid var(--border);
  border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,0.12);
  z-index: 200; overflow: hidden;
  display: flex; flex-direction: column;
  animation: fadeUp 0.3s cubic-bezier(0.4, 0, 0.2, 1) both;
}
.profile-header {
  padding: 16px; border-bottom: 1px solid var(--border); background: var(--bg);
}
.profile-name { font-weight: 600; font-size: 0.9rem; color: var(--primary); margin-bottom: 4px; }
.profile-role { font-size: 0.75rem; color: var(--text-muted); font-weight: 500; text-transform: uppercase; letter-spacing: 0.08em; }
.profile-item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px; color: var(--primary); text-decoration: none;
  font-size: 0.85rem; font-weight: 500; transition: background 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  min-height: 44px;
}
.profile-item:hover { background: var(--bg); }
.logout-item { color: #C0392B; border-top: 1px solid var(--border); }
.logout-item:hover { background: #FFF0F0; }

.page-content {
  padding: clamp(16px, 3vw, 24px) clamp(12px, 3vw, 32px) clamp(24px, 5vw, 48px);
  flex: 1;
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}
.page-header { margin-bottom: 24px; display: flex; align-items: center; justify-content: space-between; flex-shrink: 0; }
.page-header h1 { font-size: clamp(1.4rem, 4vw, 2.25rem); color: var(--primary); }

/* Animations */
@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.animate-in {
  animation: fadeUp 0.35s cubic-bezier(0.4, 0, 0.2, 1) both;
}

@keyframes shimmer {
  from { background-position: -200% 0; }
  to   { background-position:  200% 0; }
}

/* Updated Card */
.card {
  background: var(--surface); border-radius: 14px;
  padding: 24px; margin-bottom: 20px;
  border: 1px solid var(--border);
  transition: box-shadow 0.2s cubic-bezier(0.4, 0, 0.2, 1), transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.card:hover {
  box-shadow: 0 6px 20px rgba(0,0,0,0.06);
  transform: translateY(-1px);
}

/* Global Form Fields */
.field { margin-bottom: 24px; }
.field label {
  display: block; font-size: 0.875rem; font-weight: 500;
  color: var(--primary); margin-bottom: 8px;
  letter-spacing: 0.01em;
  font-family: var(--font-body);
}
.field input:not([type="checkbox"]), .field textarea, .field select, .input {
  width: 100%; padding: 10px 14px;
  border: 1.5px solid var(--border); border-radius: 8px;
  font-size: 15px; background: var(--surface); color: var(--primary);
  font-family: var(--font-body);
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  outline: none;
}
.field input:not([type="checkbox"]):focus, .field textarea:focus, .field select:focus, .input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(var(--accent-rgb), 0.15);
}

/* Updated Buttons */
.btn, .button {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 20px; border-radius: 8px;
  font-weight: 500; font-size: 14px;
  letter-spacing: 0.01em; cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: var(--font-body); border: none;
}
.btn:focus, .button:focus {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
.btn:disabled, .button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
  pointer-events: none;
}

.btn-primary { 
  background: var(--primary); color: var(--surface); 
}
.btn-primary:hover:not(:disabled) { 
  transform: translateY(-1px); 
  box-shadow: 0 4px 12px rgba(0,0,0,0.12); 
}
.btn-primary:active:not(:disabled) {
  transform: translateY(1px);
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

.btn-lime, .btn-accent { 
  background: var(--accent); color: var(--surface); 
}
.btn-lime:hover:not(:disabled), .btn-accent:hover:not(:disabled) { 
  transform: translateY(-1px); 
  box-shadow: 0 4px 12px rgba(0,0,0,0.12); 
}
.btn-lime:active:not(:disabled), .btn-accent:active:not(:disabled) {
  transform: translateY(1px);
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

.btn-outline { 
  background: transparent; color: var(--primary); 
  border: 1.5px solid var(--border);
}
.btn-outline:hover:not(:disabled) { 
  background: var(--bg);
  transform: translateY(-1px); 
  box-shadow: 0 4px 12px rgba(0,0,0,0.05); 
}
.btn-outline:active:not(:disabled) {
  transform: translateY(1px);
  box-shadow: 0 1px 4px rgba(0,0,0,0.02);
}

.btn-secondary { 
  background: var(--bg); color: var(--primary); 
}
.btn-secondary:hover:not(:disabled) { 
  transform: translateY(-1px); 
  box-shadow: 0 4px 12px rgba(0,0,0,0.08); 
}
.btn-secondary:active:not(:disabled) {
  transform: translateY(1px);
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}

.btn-danger { 
  background: #ff4444; color: var(--surface); 
}
.btn-danger:hover:not(:disabled) { 
  transform: translateY(-1px); 
  box-shadow: 0 4px 12px rgba(255, 68, 68, 0.2); 
}
.btn-danger:active:not(:disabled) {
  transform: translateY(1px);
  box-shadow: 0 1px 4px rgba(255, 68, 68, 0.1);
}

/* Badges */
.badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 12px; border-radius: 99px;
  font-size: 0.75rem; font-weight: 600;
  border: 1px solid var(--border);
  font-family: var(--font-body);
}
.badge-pending  { background: var(--bg); color: var(--primary); }
.badge-sent, .badge-delivered { background: var(--surface); color: var(--accent); border-color: var(--accent); }
.badge-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

/* Alerts */
.alert { padding: 12px 16px; border-radius: 8px; font-size: 0.875rem; margin-top: 12px; border: 1px solid; }
.alert-error   { background: #FFF0F0; color: #C0392B; border-color: #C0392B; }
.alert-success { background: var(--bg); color: var(--accent); border-color: var(--accent); }

.loading { text-align: center; padding: 48px; color: var(--text-muted); font-size: 0.9rem; }

/* Shimmer Skeleton */
.skeleton {
  background: linear-gradient(90deg, #eee 25%, #f5f5f5 50%, #eee 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
  border-radius: 4px;
  color: transparent !important;
  border: none !important;
}
.skeleton * {
  visibility: hidden;
}
.skeleton-card {
  box-shadow: none !important;
}
.skeleton-text {
  height: 1em;
  width: 60%;
  margin: 4px 0;
}
.skeleton-title {
  height: 2rem;
  width: 40%;
  border-radius: 6px;
}
.skeleton-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
}

@media (max-width: 1200px) {
  .header-powered {
    display: none;
  }
  .topbar-right {
    gap: 12px;
  }
  .top-nav-link {
    padding: 7px 11px;
    font-size: 0.86rem;
  }
  .topbar-inner {
    padding: 0 16px;
    gap: 10px;
  }
}

@media (max-width: 1024px) {
  .topbar-nav {
    display: none;
  }
  .mobile-nav-toggle {
    display: inline-flex;
  }
  .topbar-inner {
    padding: 0 16px;
    height: 64px;
  }
  .page-content {
    padding: 20px 16px 36px;
  }
}

@media (max-width: 768px) {
  .topbar-inner {
    padding: 0 12px;
    height: 60px;
  }
  .page-content {
    padding: 16px 12px 32px;
  }
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  .page-header h1 {
    font-size: clamp(1.4rem, 5vw, 1.9rem);
  }
}

@media (max-width: 480px) {
  .topbar-brand-title {
    font-size: 1.15rem;
  }
  .topbar-logo {
    height: 32px;
  }
  .topbar-right {
    gap: 8px;
  }
  .icon-btn, .avatar {
    width: 40px;
    height: 40px;
    min-width: 40px;
    min-height: 40px;
  }
  .mobile-nav-toggle {
    width: 40px;
    height: 40px;
    min-width: 40px;
    min-height: 40px;
  }
  .card {
    padding: 16px 12px;
    border-radius: 12px;
  }
  .btn, .button {
    min-height: 44px;
    padding: 10px 16px;
  }
}

@media (max-width: 360px) {
  .topbar-inner {
    padding: 0 8px;
  }
  .page-content {
    padding: 12px 8px 24px;
  }
  .topbar-brand {
    gap: 6px;
  }
}


</style>

