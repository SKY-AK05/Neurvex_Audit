<template>
  <div class="verify-page">
    <div class="verify-card">
      <div v-if="loading" class="loader">
        <p>Verifying magic login link...</p>
      </div>
      <div v-else-if="error" class="error-wrap">
        <h2>Authentication Failed</h2>
        <p class="error-msg">{{ error }}</p>
        <router-link to="/org/login" class="btn btn-primary">Back to Login</router-link>
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
  display: flex; align-items: center; justify-content: center;
  flex: 1;
  background: var(--c-bg);
  background-image:
    linear-gradient(to right, rgba(180,175,165,0.25) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(180,175,165,0.25) 1px, transparent 1px);
  background-size: 32px 32px;
  border-radius: 32px;
  box-shadow: 0 12px 48px rgba(0,0,0,0.3);
  overflow-y: auto;
}
.verify-card { background: white; border: 2px solid var(--c-primary-dark); padding: 3rem; border-radius: 16px; text-align: center; max-width: 400px; width: 90%; }
.loader p { font-size: 1.1rem; font-weight: bold; }
.error-wrap h2 { font-family: 'Fraunces', serif; color: #C0392B; margin-bottom: 1rem; }
.error-msg { margin-bottom: 2rem; color: #555; }
</style>
