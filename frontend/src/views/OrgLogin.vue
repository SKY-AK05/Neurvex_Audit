<template>
  <div class="login-page">
    <div class="login-card">
      <div class="header">
        <div class="login-logo-wrap">
          <img src="/logonew.png" alt="NIWI" class="login-logo" />
        </div>
        <h2>Organisation Dashboard</h2>
        <p class="subtitle">Enter your email and company name to register or receive your access link.</p>
      </div>

      <form @submit.prevent="handleSubmit" class="login-form">
        <div class="field-group">
          <label class="field-label">Work Email Address *</label>
          <input
            v-model="email"
            type="email"
            class="field-input"
            placeholder="jane@company.com"
            required
          />
        </div>

        <div class="field-group">
          <label class="field-label">Company Name *</label>
          <input
            v-model="companyName"
            type="text"
            class="field-input"
            placeholder="Acme Inc"
            required
          />
        </div>

        <button type="submit" class="btn-primary-pill submit-btn" :disabled="loading">
          {{ loading ? "Sending Link…" : "Get Magic Link →" }}
        </button>

        <div v-if="message" class="alert-success">{{ message }}</div>
        <div v-if="error" class="alert-error">{{ error }}</div>
      </form>

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
import { ref } from "vue";

const email = ref("");
const companyName = ref("");
const loading = ref(false);
const message = ref("");
const error = ref("");

async function handleSubmit() {
  loading.value = true;
  message.value = "";
  error.value = "";
  try {
    const API_BASE = import.meta.env.VITE_API_BASE || "/api";
    const res = await fetch(`${API_BASE}/org/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: email.value, company_name: companyName.value })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Request failed.");
    message.value = "We have emailed you a magic access link. Please check your inbox!";
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-page {
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

.login-card {
  background: #FFFFFF;
  border: 1px solid rgba(22, 16, 87, 0.08);
  border-radius: 20px;
  padding: 3rem 2.5rem;
  box-shadow: 0 16px 48px rgba(22, 16, 87, 0.06);
  max-width: 440px;
  width: 100%;
  box-sizing: border-box;
}

.login-logo-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 1.25rem;
}

.login-logo {
  height: 56px;
  width: auto;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(22, 16, 87, 0.08);
}

.header h2 {
  font-family: 'Fraunces', serif;
  font-size: 1.75rem;
  font-weight: 800;
  margin-bottom: 0.35rem;
  color: var(--primary, #161057);
  text-align: center;
  letter-spacing: -0.025em;
}

.subtitle {
  font-size: 0.925rem;
  color: #64748B;
  margin-bottom: 2rem;
  text-align: center;
  line-height: 1.5;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.field-label {
  font-size: 0.825rem;
  font-weight: 600;
  color: #1E293B;
  letter-spacing: 0.01em;
}

.field-input {
  width: 100%;
  padding: 0.65rem 0.85rem;
  border: 1px solid rgba(22, 16, 87, 0.16);
  border-radius: 10px;
  font-size: 0.9rem;
  font-family: inherit;
  color: #1E293B;
  background: #FFFFFF;
  transition: border-color 0.15s, box-shadow 0.15s;
  outline: none;
  box-sizing: border-box;
}

.field-input:focus {
  border-color: var(--accent, #04907C);
  box-shadow: 0 0 0 3px rgba(4, 144, 124, 0.15);
}

.btn-primary-pill {
  width: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background: var(--primary, #161057);
  color: #FFFFFF;
  border: none;
  border-radius: 99px;
  padding: 0.8rem 1.5rem;
  font-size: 0.95rem;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(22, 16, 87, 0.2);
  transition: transform 0.2s, box-shadow 0.2s, background 0.2s;
  margin-top: 0.5rem;
}

.btn-primary-pill:hover:not(:disabled) {
  background: #0f0a42;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(22, 16, 87, 0.28);
}

.btn-primary-pill:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.alert-success {
  background: #DCFCE7;
  color: #166534;
  border: 1px solid #86EFAC;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  font-size: 0.85rem;
  text-align: center;
}

.alert-error {
  background: #FEE2E2;
  color: #991B1B;
  border: 1px solid #FCA5A5;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  font-size: 0.85rem;
  text-align: center;
}

.login-footer {
  margin-top: 2rem;
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
}

.powered-logo {
  height: 18px;
  width: auto;
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
</style>
