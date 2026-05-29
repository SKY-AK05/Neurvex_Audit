<template>
  <div class="resume-page">
    <div class="resume-card">
      <div v-if="loading" class="loader">
        <p>Verifying session and loading your progress...</p>
      </div>
      <div v-else-if="error" class="error-wrap">
        <h2>Cannot Resume Audit</h2>
        <p class="error-msg">{{ error }}</p>
        <router-link to="/" class="btn btn-primary">Start New Audit</router-link>
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
    error.value = "Missing session token.";
    loading.value = false;
    return;
  }

  try {
    const API_BASE = import.meta.env.VITE_API_BASE || "/api";
    const res = await fetch(`${API_BASE}/drafts/resume?token=${token}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Failed to resume.");

    // Store state in LocalStorage for AuditForm to fetch
    localStorage.setItem("nd_draft_state", JSON.stringify({
      formData: data.form_state,
      currentStep: data.current_step
    }));
    localStorage.setItem("nd_draft_id", data.draft_id);
    // Signal to AuditForm that this is a legitimate resume — not a fresh visit
    localStorage.setItem("nd_resume_ready", "1");
    // Timestamp for the 30-minute session window
    localStorage.setItem("nd_resume_at", String(Date.now()));

    // Redirect to main audit form page
    router.push("/");
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.resume-page {
  display: flex; align-items: center; justify-content: center; height: 100vh; background: var(--c-bg);
}
.resume-card {
  background: white; border: 2px solid var(--c-primary-dark); padding: 3rem; border-radius: 16px;
  box-shadow: 4px 4px 0 var(--c-primary-dark); text-align: center; max-width: 450px; width: 90%;
}
.error-wrap h2 { font-family: 'Fraunces', serif; color: #C0392B; margin-bottom: 1rem; }
.error-msg { margin-bottom: 2rem; color: #555; }
</style>
