<template>
  <div id="app-shell">
    <div :class="isAdmin ? 'admin-layout' : 'public-shell'">
      <!-- Dark Slim Sidebar -->
      <aside v-if="isAdmin" class="sidebar">
        <div class="sidebar-top">
          <div class="sidebar-brand">
            <img src="/logonew.png" alt="NIWI" class="brand-logo-icon" />
            <span class="brand-text">NIWI</span>
          </div>

          <nav class="sidebar-nav">
            <router-link to="/admin/dashboard" class="nav-item" :class="{ active: route.path === '/admin/dashboard' }" title="Dashboard">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="nav-icon"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
              <span class="nav-text">Dashboard</span>
            </router-link>
            <router-link to="/admin/analytics" class="nav-item" :class="{ active: route.path === '/admin/analytics' }" title="Analytics">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="nav-icon"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
              <span class="nav-text">Analytics</span>
            </router-link>
            <router-link to="/admin/submissions" class="nav-item" :class="{ active: route.path.includes('submissions') }" title="Submissions">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="nav-icon"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
              <span class="nav-text">Submissions</span>
            </router-link>
            <router-link to="/admin/organisations" class="nav-item" :class="{ active: route.path === '/admin/organisations' }" title="Organisations">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="nav-icon"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
              <span class="nav-text">Organisations</span>
            </router-link>
          </nav>
        </div>
      </aside>

      <!-- Main App Content wrapped in floating rounded container -->
      <div v-if="isAdmin" class="main-container-wrapper">
        <div class="main-rounded-container">
          <!-- Internal Top Header -->
          <header class="main-header">
            <div class="header-right">
              <div class="header-powered">
                <span class="powered-label">Powered by</span>
                <img src="/logo_orchvate.png" alt="Orchvate" class="powered-logo" />
              </div>

              <div class="bell-wrap" ref="bellWrap">
                <button
                  type="button"
                  class="icon-btn"
                  :class="{ 'bell-on': notificationsEnabled }"
                  title="Submission email alerts"
                  @click.stop="onBellClick"
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

              <div class="profile-wrap" ref="profileWrap">
                <div class="avatar" @click.stop="profileOpen = !profileOpen">{{ userInitials }}</div>
                <div v-if="profileOpen" class="profile-popover">
                  <div class="profile-header">
                    <div class="profile-name">{{ userName }}</div>
                    <div class="profile-role">{{ isSuper ? 'Super Admin' : 'Admin' }}</div>
                  </div>
                  <router-link to="/admin/settings" class="profile-item" @click="profileOpen = false">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>
                    Settings
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
            </div>
          </header>

          <main class="page-content">
            <router-view />
          </main>
        </div>
      </div>
      
      <router-view v-else />
      

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
const pageTitle = computed(() => pageTitles[route.path] || "NIWI � Neuro-Inclusive Workplace Index");

const notificationsEnabled = ref(false);
const notificationEmail = ref("");
const bellOpen = ref(false);
const bellWrap = ref(null);
const bellMsg = ref("");
const bellMsgType = ref("success");
const bellToggling = ref(false);

const profileOpen = ref(false);
const profileWrap = ref(null);

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
  --c-primary-dark: #161057;
  --c-primary-light: #4A5A89;
  --c-accent: #04907C;
  --c-accent-secondary: #20C0B0;
  --c-accent-retro: #FFF8F2;
  --c-bg: #F5F2EB;
  --c-white: #FFFFFF;
  --font-body: 'Geist', 'Inter', sans-serif;
  --line-height-body: 1.5;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: var(--font-body);
  line-height: var(--line-height-body);
  background-color: var(--c-bg);
  color: var(--c-primary-dark);
  background-image:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3CfeColorMatrix type='saturate' values='0'/%3E%3C/filter%3E%3Crect width='200' height='200' filter='url(%23n)' opacity='0.4'/%3E%3C/svg%3E"),
    linear-gradient(to right, rgba(0,0,0,0.06) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(0,0,0,0.06) 1px, transparent 1px);
  background-size: 200px 200px, 32px 32px, 32px 32px;
  background-attachment: fixed;
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
  font-family: 'Fraunces', serif;
}

#app-shell { display: flex; flex-direction: column; min-height: 100vh; width: 100%; }

/* Public form/login — fill viewport so step content can center */
.public-shell {
  flex: 1;
  width: 100%;
  min-width: 0;
  height: 100dvh;
  max-height: 100dvh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* ── Design tokens ── */
/* Cream: var(--c-bg)  |  Black: var(--c-primary-dark)  |  Lime: var(--c-accent);
   Card: var(--c-white)   |  Border: var(--c-primary-dark)  |  Muted: #888     */

/* Main area */
.admin-layout, .public-shell {
  flex: 1; display: flex; flex-direction: row; height: 100vh;
  background: #2a2b2e; /* Dark floating background */
  padding: 1rem;
  box-sizing: border-box;
  gap: 1rem;
}
.public-shell {
  flex-direction: column;
  overflow: hidden;
}

.sidebar {
  width: 60px;
  background: transparent;
  display: flex; flex-direction: column;
  justify-content: flex-start;
  align-items: center;
  z-index: 50;
  flex-shrink: 0;
  height: calc(100vh - 2rem);
  position: sticky;
  top: 1rem;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.sidebar:hover {
  width: 220px;
  align-items: stretch;
}

.sidebar-top {
  display: flex; flex-direction: column; gap: 2.5rem; align-items: center; width: 100%;
}
.sidebar:hover .sidebar-top {
  align-items: flex-start;
  padding: 0 0.5rem;
}

.sidebar-brand {
  display: flex; align-items: center; justify-content: flex-start;
  white-space: nowrap;
  width: 48px;
  overflow: hidden;
  transition: width 0.3s;
  padding-left: 4px;
}
.sidebar:hover .sidebar-brand {
  width: 100%;
}

.brand-logo-icon {
  height: 44px;
  width: 44px;
  display: block;
  object-fit: contain;
  border-radius: 8px;
  flex-shrink: 0;
}

.brand-text {
  margin-left: 0.75rem; font-weight: 800; font-size: 1.2rem; color: var(--c-white); font-family: 'Fraunces', serif;
  opacity: 0; transition: opacity 0.2s; white-space: nowrap;
}
.sidebar:hover .brand-text { opacity: 1; transition-delay: 0.1s; }

.sidebar-nav {
  display: flex; flex-direction: column; gap: 1.25rem; width: 100%;
}

.nav-item {
  display: flex; align-items: center; justify-content: flex-start;
  width: 44px; height: 44px; border-radius: 14px; margin: 0 auto;
  color: rgba(255,255,255,0.75); 
  text-decoration: none; cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  padding-left: 10px;
  box-sizing: border-box;
  position: relative;
}
.sidebar:hover .nav-item {
  width: 100%;
}

.nav-icon { flex-shrink: 0; stroke: currentColor; position: relative; z-index: 2; }
.nav-text {
  position: absolute;
  left: 46px;
  font-weight: 600; font-size: 0.95rem; white-space: nowrap;
  opacity: 0; transition: opacity 0.2s;
}
.sidebar:hover .nav-text { opacity: 1; transition-delay: 0.1s; }

.nav-item:hover { color: var(--c-white); background: rgba(255,255,255,0.1); transform: translateY(-2px); }
.sidebar:hover .nav-item:hover { transform: translateX(4px); }

.nav-item.active {
  background: var(--c-bg); color: var(--c-primary-dark);
  box-shadow: 0 4px 12px rgba(255, 255, 255, 0.2);
}
.nav-item.active svg { stroke: var(--c-primary-dark) !important; color: var(--c-primary-dark) !important; }

.main-container-wrapper {
  flex: 1; display: flex; flex-direction: column;
  min-width: 0;
}

.main-rounded-container {
  background: var(--c-bg);
  background-image:
    linear-gradient(to right, rgba(180,175,165,0.25) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(180,175,165,0.25) 1px, transparent 1px);
  background-size: 32px 32px;
  border-radius: 32px;
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 12px 48px rgba(0,0,0,0.3);
}

.main-header {
  height: 48px;
  display: flex; align-items: center; justify-content: flex-end;
  padding: 0.5rem 3rem 0;
  flex-shrink: 0;
}
.header-logo {
  height: 28px;
  width: auto;
  object-fit: contain;
}
.header-right {
  display: flex; align-items: center; gap: 1.5rem;
}
.header-powered {
  display: flex; align-items: center; gap: 0.5rem;
  padding-right: 1.5rem;
  border-right: 2px solid rgba(0,0,0,0.06);
}
.powered-label {
  font-size: 0.68rem; color: #888; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.05em;
}
.powered-logo {
  height: 24px; width: auto; object-fit: contain;
}

.share-audit-btn {
  background: var(--c-white); color: var(--c-primary-dark);
  border: 2px solid var(--c-primary-dark); border-radius: 99px;
  padding: 0.5rem 1.1rem; font-size: 0.875rem; font-weight: 700;
  cursor: pointer; text-decoration: none; display: flex; align-items: center; gap: 0.4rem;
  transition: all 0.15s; font-family: 'Fraunces', serif;
}
.share-audit-btn:hover { background: var(--c-accent-retro); transform: translate(-1px, -1px); }

.icon-btn {
  width: 44px; height: 44px; border-radius: 50%;
  border: 2px solid var(--c-primary-dark); background: var(--c-white);
  display: grid; place-items: center; cursor: pointer; color: var(--c-primary-dark);
  transition: all 0.15s; box-shadow: 2px 2px 0 rgba(255,255,255,0.2);
}
.icon-btn:hover { background: var(--c-accent); transform: translateY(-2px); box-shadow: 2px 4px 0 rgba(255,255,255,0.3); }
.icon-btn.bell-on { background: var(--c-accent-retro); }

.bell-wrap { position: relative; }
.bell-badge {
  position: absolute; top: 4px; right: 4px;
  width: 10px; height: 10px; border-radius: 50%;
  background: var(--c-accent-retro); border: 2px solid var(--c-primary-dark);
}
.bell-popover {
  position: absolute; top: calc(100% + 12px); right: -60px;
  width: 280px; padding: 1rem 1.1rem;
  background: var(--c-white); border: 2px solid var(--c-primary-dark);
  border-radius: 12px; box-shadow: 4px 4px 0 var(--c-accent);
  z-index: 200;
}
.bell-pop-title {
  font-size: 0.85rem; font-weight: 800; color: var(--c-primary-dark);
  margin-bottom: 0.4rem; font-family: 'Fraunces', serif;
}
.bell-pop-text { font-size: 0.8rem; color: #666; line-height: 1.45; margin-bottom: 0.5rem; }
.bell-pop-email { font-size: 0.78rem; color: var(--c-primary-dark); font-weight: 600; margin-bottom: 0.5rem; }
.bell-pop-warn { font-size: 0.78rem; color: #C0392B; margin-bottom: 0.5rem; }
.bell-pop-link {
  font-size: 0.8rem; font-weight: 700; color: var(--c-primary-dark);
  text-decoration: none; display: inline-block;
}
.bell-pop-link:hover { text-decoration: underline; }
.bell-pop-msg { font-size: 0.78rem; margin-top: 0.6rem; font-weight: 600; }
.bell-pop-msg.success { color: #3A7A00; }
.bell-pop-msg.error { color: #C0392B; }

.profile-wrap { position: relative; }
.avatar {
  width: 44px; height: 44px; border-radius: 50%;
  background: var(--c-primary-dark); color: var(--c-accent); cursor: pointer;
  display: grid; place-items: center;
  font-size: 0.95rem; font-weight: 800;
  border: 2px solid var(--c-accent);
  font-family: 'Fraunces', serif;
  transition: all 0.15s;
  box-shadow: 2px 2px 0 rgba(255,255,255,0.2);
}
.avatar:hover { transform: translateY(-2px); box-shadow: 2px 4px 0 rgba(255,255,255,0.3); }

.profile-popover {
  position: absolute; top: calc(100% + 12px); right: 0;
  width: 220px; background: var(--c-white); border: 2px solid var(--c-primary-dark);
  border-radius: 12px; box-shadow: 4px 4px 0 var(--c-accent);
  z-index: 200; overflow: hidden;
  display: flex; flex-direction: column;
}
.profile-header {
  padding: 1rem; border-bottom: 1px solid #eee; background: #fdfdfc;
}
.profile-name { font-weight: 800; font-size: 0.9rem; color: var(--c-primary-dark); margin-bottom: 0.1rem; }
.profile-role { font-size: 0.75rem; color: #888; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
.profile-item {
  display: flex; align-items: center; gap: 0.75rem;
  padding: 0.8rem 1rem; color: var(--c-primary-dark); text-decoration: none;
  font-size: 0.85rem; font-weight: 600; transition: background 0.15s;
}
.profile-item:hover { background: #f5f5f5; }
.logout-item { color: #C0392B; border-top: 1px solid #eee; }
.logout-item:hover { background: #FFF0F0; }

.page-content {
  padding: 0.25rem 3rem 2rem;
  flex: 1;
  width: 100%;
  overflow-y: auto; display: flex; flex-direction: column; }
.page-header { margin-bottom: 2rem; display: flex; align-items: center; justify-content: space-between; flex-shrink: 0; }
.page-header h1 { font-size: 2rem; font-weight: 800; color: var(--c-primary-dark); letter-spacing: -0.02em; }

/* Shared card — large radius, clean thick border */
.card {
  background: var(--c-white); border-radius: 12px;
  padding: 1.5rem; margin-bottom: 1.25rem;
  border: 2px solid var(--c-primary-dark);
  box-shadow: 4px 4px 0 var(--c-primary-dark);
}

/* Global Form Fields */
.field { margin-bottom: 1.25rem; }
.field label {
  display: block; font-size: 0.75rem; font-weight: 800;
  color: var(--c-primary-dark); margin-bottom: 0.4rem;
  text-transform: uppercase; letter-spacing: 0.05em;
  font-family: 'Inter', sans-serif;
}
.field input:not([type="checkbox"]), .field textarea, .field select {
  width: 100%; padding: 0.8rem 1rem;
  border: 2px solid var(--c-primary-dark); border-radius: 8px;
  font-size: 0.95rem; background: var(--c-white); color: var(--c-primary-dark);
  font-family: 'Inter', sans-serif;
  transition: all 0.15s;
  box-shadow: 2px 2px 0 rgba(0,0,0,0.1);
}
.field input:not([type="checkbox"]):focus, .field textarea:focus, .field select:focus {
  outline: none;
  box-shadow: 4px 4px 0 var(--c-accent);
  transform: translate(-2px, -2px);
}

/* Shared buttons */
.btn {
  padding: 0.6rem 1.3rem; border-radius: 99px;
  font-size: 0.875rem; font-weight: 700; cursor: pointer; transition: all 0.15s;
  display: inline-flex; align-items: center; gap: 0.4rem;
  font-family: 'Fraunces', serif; border: 2px solid var(--c-primary-dark);
}
.btn-primary { background: var(--c-primary-dark); color: var(--c-white); box-shadow: 3px 3px 0 var(--c-accent-retro); }
.btn-primary:hover:not(:disabled) { transform: translate(-2px,-2px); box-shadow: 5px 5px 0 var(--c-accent-retro); }
.btn-primary:disabled { background: #aaa; border-color: #aaa; box-shadow: none; cursor: not-allowed; }
.btn-lime { background: var(--c-accent-retro); color: var(--c-primary-dark); box-shadow: 3px 3px 0 var(--c-primary-dark); }
.btn-lime:hover:not(:disabled) { transform: translate(-2px,-2px); box-shadow: 5px 5px 0 var(--c-primary-dark); }
.btn-outline { background: var(--c-white); color: var(--c-primary-dark); box-shadow: 3px 3px 0 var(--c-primary-dark); }
.btn-outline:hover { transform: translate(-2px,-2px); box-shadow: 5px 5px 0 var(--c-primary-dark); }
.btn-secondary { background: var(--c-bg); color: var(--c-primary-dark); box-shadow: 3px 3px 0 var(--c-primary-dark); }
.btn-secondary:hover { transform: translate(-2px,-2px); box-shadow: 5px 5px 0 var(--c-primary-dark); }
.btn-danger { background: #ff4444; color: var(--c-white); box-shadow: 3px 3px 0 var(--c-primary-dark); }
.btn-danger:hover:not(:disabled) { transform: translate(-2px,-2px); box-shadow: 5px 5px 0 var(--c-primary-dark); }

/* Badges */
.badge {
  display: inline-flex; align-items: center; gap: 0.3rem;
  padding: 0.25rem 0.75rem; border-radius: 99px;
  font-size: 0.78rem; font-weight: 700;
  border: 1.5px solid currentColor;
  font-family: 'Fraunces', serif;
}
.badge-pending  { background: var(--c-bg); color: var(--c-primary-dark); }
.badge-sent, .badge-delivered { background: var(--c-accent-retro); color: var(--c-primary-dark); border-color: var(--c-primary-dark); }
.badge-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

/* Alerts */
.alert { padding: 0.75rem 1rem; border-radius: 10px; font-size: 0.875rem; margin-top: 0.75rem; border: 2px solid; }
.alert-error   { background: #FFF0F0; color: #C0392B; border-color: #C0392B; }
.alert-success { background: var(--c-accent-retro); color: var(--c-primary-dark); border-color: var(--c-primary-dark); }

.loading { text-align: center; padding: 3rem; color: #aaa; font-size: 0.9rem; }

/* Skeleton Loading Animations */
@keyframes skeleton-pulse {
  0% { background-color: rgba(0, 0, 0, 0.05); }
  50% { background-color: rgba(0, 0, 0, 0.12); }
  100% { background-color: rgba(0, 0, 0, 0.05); }
}
.skeleton {
  animation: skeleton-pulse 1.5s ease-in-out infinite;
  border-radius: 4px;
  color: transparent !important;
  background-color: rgba(0, 0, 0, 0.08);
}
.skeleton * {
  visibility: hidden;
}
.skeleton-card {
  border-color: rgba(0, 0, 0, 0.05) !important;
  box-shadow: none !important;
}
.skeleton-text {
  height: 1em;
  width: 60%;
  border-radius: 4px;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
  margin: 0.25rem 0;
}
.skeleton-title {
  height: 2rem;
  width: 40%;
  border-radius: 6px;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}
.skeleton-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  animation: skeleton-pulse 1.5s ease-in-out infinite;
}
</style>
