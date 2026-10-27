<template>
  <div class="login-wrap">
    <!-- Ambient glowing background effect -->
    <div class="glow-orb"></div>
    
    <div class="login-box">
      <div class="login-logo">
        <!-- Light login card ? use dark logo -->
        <img src="/logonew.png" alt="NIWI" class="login-logo-img" />
      </div>
      <h2>Admin Login</h2>
      <p class="login-sub">NIWI Dashboard</p>
      
      <div v-if="error" class="error-msg">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
        {{ errorMsg }}
      </div>
      
      <button class="ms-login-btn" @click="login" :disabled="loading">
        <svg v-if="!loading" class="ms-logo" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 21 21">
          <rect x="1" y="1" width="9" height="9" fill="#f25022"/>
          <rect x="11" y="1" width="9" height="9" fill="#7fba00"/>
          <rect x="1" y="11" width="9" height="9" fill="#00a4ef"/>
          <rect x="11" y="11" width="9" height="9" fill="#ffb900"/>
        </svg>
        <div v-else class="spinner"></div>
        <span>{{ loading ? 'Connecting to Microsoft...' : 'Sign in with Microsoft' }}</span>
      </button>

      <!-- Powered by Orchvate footer -->
      <div class="login-footer">
        <div class="powered-by-wrap">
          <span class="powered-label">Powered by</span>
          <img src="/logo_orchvate.png" alt="Orchvate" class="powered-logo" />
        </div>
        <router-link to="/" class="back-link">← Back to Self-Assessment</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { getMsalInstance, loginRequest, completeAdminLogin, clearMsalCache } from "../authConfig";

const error    = ref(false);
const errorMsg = ref("");
const loading  = ref(false);
const router   = useRouter();

const isLocalhost = ref(window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1");
const devEmail = ref("");

async function handleDevLogin() {
  if (!devEmail.value) {
    error.value = true;
    errorMsg.value = "Please enter a developer email address.";
    return;
  }
  
  loading.value = true;
  error.value = false;
  try {
    const API_BASE = import.meta.env.VITE_API_BASE || "/api";
    const res = await fetch(`${API_BASE}/auth/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: devEmail.value.trim() })
    });
    
    if (!res.ok) throw new Error("Bypass verification request failed.");
    const data = await res.json();
    if (data.authorized) {
      sessionStorage.setItem("nd_auth", "1");
      sessionStorage.setItem("nd_user_name", devEmail.value);
      sessionStorage.setItem("nd_role", data.role);
      sessionStorage.setItem("nd_auth_token", "local_bypass:" + devEmail.value.trim());
      sessionStorage.removeItem("nd_auth_error");
      router.push("/admin/dashboard");
    } else {
      error.value = true;
      errorMsg.value = "Access Denied: This email is not authorized in admin_users.";
    }
  } catch (err) {
    error.value = true;
    errorMsg.value = err.message || "Failed to bypass login.";
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  if (sessionStorage.getItem("nd_auth") === "1") {
    router.replace("/admin/dashboard");
    return;
  }

  const storedError = sessionStorage.getItem("nd_auth_error");
  if (storedError) {
    error.value = true;
    errorMsg.value = storedError;
    sessionStorage.removeItem("nd_auth_error");
  }

  try {
    const msalInstance = await getMsalInstance();
    const response = await msalInstance.handleRedirectPromise();
    if (response?.account) {
      const result = await completeAdminLogin(response);
      if (result.ok) {
        router.replace("/admin/dashboard");
        return;
      }
      error.value = true;
      errorMsg.value = `Access denied: ${result.email || "your account"} is not in admin_users.`;
      clearMsalCache();
    }
  } catch (err) {
    error.value = true;
    errorMsg.value = err.message || "Authentication failed.";
    clearMsalCache();
  }
});

async function login() {
  error.value = false;
  loading.value = true;
  try {
    const msalInstance = await getMsalInstance();
    await msalInstance.loginRedirect(loginRequest);
  } catch (err) {
    console.error("Login failed:", err);
    error.value = true;
    errorMsg.value = err.message || "Authentication failed.";
    loading.value = false;
  }
}
</script>

<style scoped>
.login-wrap {
  min-height: 100vh;
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  background: var(--bg, #FAFAF8);
  padding: 1.5rem;
  box-sizing: border-box;
}

.glow-orb {
  position: absolute;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(4, 144, 124, 0.08) 0%, rgba(22, 16, 87, 0.04) 40%, transparent 70%);
  border-radius: 50%;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 0;
  pointer-events: none;
}

.login-box {
  position: relative;
  z-index: 1;
  background: #FFFFFF;
  border: 1px solid rgba(22, 16, 87, 0.08);
  box-shadow: 0 16px 48px rgba(22, 16, 87, 0.06);
  padding: 3rem 2.5rem;
  border-radius: 20px;
  width: 100%;
  max-width: 440px;
  text-align: center;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  box-sizing: border-box;
}

.login-box:hover {
  box-shadow: 0 20px 56px rgba(22, 16, 87, 0.09);
}

.login-logo {
  margin-bottom: 1.25rem;
  display: flex;
  justify-content: center;
}

.login-logo-img {
  height: 56px;
  width: auto;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(22, 16, 87, 0.08);
}

h2 {
  font-size: 1.85rem;
  font-weight: 800;
  margin-bottom: 0.35rem;
  color: var(--primary, #161057);
  font-family: 'Fraunces', serif;
  letter-spacing: -0.025em;
}

.login-sub {
  color: #64748B;
  font-size: 0.95rem;
  margin-bottom: 2rem;
  font-weight: 500;
  font-family: var(--font-body, 'Geist', 'Inter', sans-serif);
}

.error-msg {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background: #FEE2E2;
  color: #991B1B;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  border: 1px solid #FCA5A5;
  font-size: 0.85rem;
  margin-bottom: 1.5rem;
  font-weight: 600;
  text-align: left;
}

.ms-login-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.85rem;
  padding: 0.85rem 1.5rem;
  font-size: 0.95rem;
  background: var(--primary, #161057);
  color: #FFFFFF;
  border: none;
  border-radius: 99px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: var(--font-body, 'Geist', 'Inter', sans-serif);
  box-shadow: 0 4px 14px rgba(22, 16, 87, 0.2);
}

.ms-login-btn:hover:not(:disabled) {
  background: #0f0a42;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(22, 16, 87, 0.28);
}

.ms-login-btn:active:not(:disabled) {
  transform: translateY(1px);
  box-shadow: 0 1px 4px rgba(22, 16, 87, 0.12);
}

.ms-login-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.ms-logo {
  width: 20px;
  height: 20px;
}

.login-footer {
  margin-top: 2.25rem;
  padding-top: 1.5rem;
  border-top: 1px solid rgba(22, 16, 87, 0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.85rem;
}

.powered-by-wrap {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.powered-label {
  font-size: 0.65rem;
  color: #94A3B8;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-family: var(--font-body, 'Geist', 'Inter', sans-serif);
}

.powered-logo {
  height: 18px;
  width: auto;
  object-fit: contain;
}

.back-link {
  font-size: 0.825rem;
  color: #64748B;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.15s;
}

.back-link:hover {
  color: var(--primary, #161057);
}

/* Loading spinner */
.spinner {
  width: 20px;
  height: 20px;
  border: 2.5px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #FFFFFF;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
