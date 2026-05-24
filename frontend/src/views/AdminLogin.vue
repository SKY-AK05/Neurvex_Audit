<template>
  <div class="login-wrap">
    <!-- Ambient glowing background effect -->
    <div class="glow-orb"></div>
    
    <div class="login-box">
      <div class="login-logo">
        <!-- Light login card → use dark logo -->
        <img src="/logo-dark.png" alt="Neurvex" class="login-logo-img" />
      </div>
      <h2>Admin Login</h2>
      <p class="login-sub">Neurvex Dashboard</p>
      
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

      <!-- Local Dev Bypass Option -->
      <div v-if="isLocalhost" class="dev-bypass-wrap" style="margin-top: 2rem; border-top: 1px dashed var(--c-primary-dark); padding-top: 1.5rem;">
        <p style="font-size: 0.8rem; color: #666; margin-bottom: 1rem; font-weight: bold;">Developer Mode: Bypass Microsoft Login</p>
        <div style="display: flex; gap: 0.5rem; justify-content: center; align-items: center;">
          <input v-model="devEmail" type="email" placeholder="admin.email@orchvate.com" style="padding: 0.5rem 0.75rem; border: 2px solid var(--c-primary-dark); border-radius: 8px; font-size: 0.85rem; width: 220px; background: white; color: var(--c-primary-dark);" />
          <button @click="handleDevLogin" class="btn btn-primary" style="font-size: 0.8rem; padding: 0.45rem 1rem;">Log In</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { msalInstance, loginRequest } from "../authConfig";

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
  const storedError = sessionStorage.getItem("nd_auth_error");
  if (storedError) {
    error.value = true;
    errorMsg.value = storedError;
    sessionStorage.removeItem("nd_auth_error");
  }

  try {
    await msalInstance.initialize();
    // Clear any stale MSAL interaction state that causes interaction_in_progress errors
    const keys = Object.keys(sessionStorage).filter(k =>
      k.includes("interaction.status") || k.includes("request.params")
    );
    keys.forEach(k => sessionStorage.removeItem(k));
    await msalInstance.handleRedirectPromise();
  } catch (err) {
    // ignore
  }
});

async function login() {
  error.value = false;
  loading.value = true;
  try {
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
  display: flex; align-items: center; justify-content: center;
  position: relative;
  overflow: hidden;
  /* Ensure the grid background from App.vue shines through, but we add our own ambient layer */
}

.glow-orb {
  position: absolute;
  width: 700px;
  height: 700px;
  background: radial-gradient(circle, rgba(200, 241, 53, 0.45) 0%, rgba(200, 241, 53, 0) 60%);
  border-radius: 50%;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 0;
  animation: pulse 5s infinite alternate ease-in-out;
  pointer-events: none;
}

@keyframes pulse {
  0% { transform: translate(-50%, -50%) scale(1); opacity: 0.5; }
  100% { transform: translate(-50%, -50%) scale(1.15); opacity: 1; }
}

.login-box {
  position: relative;
  z-index: 1;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  padding: 3.5rem 3rem;
  border-radius: 24px;
  width: 440px;
  text-align: center;
  border: 2px solid var(--c-primary-dark);
  box-shadow: 12px 12px 0px var(--c-accent);
  transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.3s ease;
}

.login-box:hover {
  transform: translate(-4px, -4px);
  box-shadow: 16px 16px 0px var(--c-accent);
}

.login-logo {
  margin-bottom: 1.5rem;
  display: flex;
  justify-content: center;
}

.login-logo-img {
  height: 56px;
  width: auto;
  object-fit: contain;
  animation: float 4s ease-in-out infinite;
}

@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-6px); }
  100% { transform: translateY(0px); }
}

h2 {
  font-size: 1.85rem;
  font-weight: 800;
  margin-bottom: 0.25rem;
  color: var(--c-primary-dark);
  font-family: 'Playfair Display', serif;
  letter-spacing: -0.02em;
}

.login-sub {
  color: #666;
  font-size: 1rem;
  margin-bottom: 2.5rem;
  font-weight: 500;
}

.error-msg {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background: #FFF0F0;
  color: #C0392B;
  padding: 0.85rem;
  border-radius: 10px;
  border: 2px solid #C0392B;
  font-size: 0.85rem;
  margin-bottom: 1.5rem;
  font-weight: 700;
  text-align: left;
}

.ms-login-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.85rem;
  padding: 1.1rem;
  font-size: 1.05rem;
  background: var(--c-primary-dark);
  color: var(--c-white);
  border: 2px solid var(--c-primary-dark);
  border-radius: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);
  font-family: 'Inter', sans-serif;
  box-shadow: 4px 4px 0px rgba(26, 26, 26, 0.2);
}

.ms-login-btn:hover:not(:disabled) {
  background: #2a2a2a;
  transform: translateY(-2px);
  box-shadow: 4px 8px 0px rgba(26, 26, 26, 0.25);
}

.ms-login-btn:active:not(:disabled) {
  transform: translateY(1px);
  box-shadow: 2px 2px 0px rgba(26, 26, 26, 0.3);
}

.ms-login-btn:disabled {
  opacity: 0.75;
  cursor: not-allowed;
}

.ms-logo {
  width: 22px;
  height: 22px;
}

/* Simple loading spinner */
.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: var(--c-accent);
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
