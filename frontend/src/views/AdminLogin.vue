<template>
  <div class="login-wrap">
    <!-- Ambient glowing background effect -->
    <div class="glow-orb"></div>
    
    <div class="login-box">
      <div class="login-logo">
        <span class="logo-mark">O</span>
      </div>
      <h2>Admin Login</h2>
      <p class="login-sub">Neurvex Audit Dashboard</p>
      
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

onMounted(async () => {
  const storedError = sessionStorage.getItem("nd_auth_error");
  if (storedError) {
    error.value = true;
    errorMsg.value = storedError;
    sessionStorage.removeItem("nd_auth_error");
  }

  try {
    await msalInstance.initialize();
  } catch (err) {
    // ignore if already initialized
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
}

.login-logo .logo-mark {
  width: 64px;
  height: 64px;
  background: var(--c-accent);
  border-radius: 16px;
  display: inline-grid;
  place-items: center;
  font-weight: 900;
  font-size: 2.2rem;
  color: var(--c-primary-dark);
  border: 3px solid var(--c-primary-dark);
  box-shadow: 4px 4px 0 var(--c-primary-dark);
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
