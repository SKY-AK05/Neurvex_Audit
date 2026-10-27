<template>
  <div class="verify-page">
    <div class="verify-card">
      <div class="verify-logo">
        <img src="/logonew1.png" alt="NIWI" class="logo-img" />
      </div>

      <div v-if="loading" class="loader-wrap">
        <div class="spinner"></div>
        <h2 class="loader-title">Verifying Access</h2>
        <p class="loader-desc">Validating your secure magic login link…</p>
      </div>

      <div v-else-if="error" class="error-wrap">
        <div class="error-icon">!</div>
        <h2>Authentication Failed</h2>
        <p class="error-msg">{{ error }}</p>
        <router-link to="/org/login" class="btn-primary-pill">Back to Organisation Login →</router-link>
      </div>

      <div class="powered-by-wrap">
        <span class="powered-label">Powered by</span>
        <img src="/logo_orchvate.png" alt="Orchvate" class="powered-logo" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();
const loading = ref(true);
const error = ref("");

onMounted(async () => {
  const token = route.query.token;
  if (!token) {
    error.value = "Missing verification token.";
    loading.value = false;
    return;
  }

  try {
    const API_BASE = import.meta.env.VITE_API_BASE || "/api";
    const res = await fetch(`${API_BASE}/org/verify?token=${token}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Verification failed.");

    // Store Session JWT
    localStorage.setItem("org_token", data.token);
    localStorage.setItem("org_name", data.organization.name);
    localStorage.setItem("org_user_email", data.email);

    router.push("/org/dashboard");
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.verify-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  min-height: 100dvh;
  background: var(--bg, #FAFAF8);
  padding: 1.5rem;
  box-sizing: border-box;
  font-family: var(--font-body, 'Geist', 'Inter', sans-serif);
}

.verify-card {
  background: #FFFFFF;
  border: 1px solid rgba(22, 16, 87, 0.08);
  border-radius: 18px;
  padding: 3rem 2.5rem;
  box-shadow: 0 12px 36px rgba(22, 16, 87, 0.05);
  text-align: center;
  max-width: 440px;
  width: 100%;
  box-sizing: border-box;
}

.verify-logo {
  margin-bottom: 1.5rem;
}

.logo-img {
  height: 44px;
  width: auto;
  border-radius: 8px;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(22, 16, 87, 0.1);
  border-top-color: var(--accent, #04907C);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 1.25rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loader-title {
  font-family: 'Fraunces', serif;
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--primary, #161057);
  letter-spacing: -0.02em;
  margin-bottom: 0.5rem;
}

.loader-desc {
  color: #64748B;
  font-size: 0.9rem;
  line-height: 1.6;
}

.error-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #FEE2E2;
  color: #DC2626;
  border: 1.5px solid #FCA5A5;
  font-size: 1.5rem;
  font-weight: 800;
  display: inline-grid;
  place-items: center;
  margin: 0 auto 1.25rem;
}

.error-wrap h2 {
  font-family: 'Fraunces', serif;
  font-size: 1.5rem;
  font-weight: 800;
  color: #991B1B;
  letter-spacing: -0.02em;
  margin-bottom: 0.5rem;
}

.error-msg {
  color: #475569;
  font-size: 0.9rem;
  line-height: 1.5;
  margin-bottom: 1.75rem;
}

.btn-primary-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--primary, #161057);
  color: #FFFFFF;
  text-decoration: none;
  font-weight: 700;
  font-size: 0.9rem;
  padding: 0.75rem 1.8rem;
  border-radius: 99px;
  box-shadow: 0 4px 14px rgba(22, 16, 87, 0.2);
  transition: transform 0.2s, box-shadow 0.2s, background 0.2s;
}

.btn-primary-pill:hover {
  background: #0f0a42;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(22, 16, 87, 0.28);
}

.powered-by-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  margin-top: 2.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid rgba(22, 16, 87, 0.08);
}

.powered-label {
  font-size: 0.65rem;
  color: #94A3B8;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.powered-logo {
  height: 18px;
  width: auto;
}
</style>
