<template>
  <div class="login-page">
    <div class="login-card">
      <div class="header">
        <h2>Organisation Dashboard</h2>
        <p>Enter your email and company name to register or receive your access link.</p>
      </div>

      <form @submit.prevent="handleSubmit" class="login-form">
        <div class="field">
          <label>Work Email Address *</label>
          <input v-model="email" type="email" placeholder="jane@company.com" required />
        </div>
        <div class="field">
          <label>Company Name *</label>
          <input v-model="companyName" type="text" placeholder="Acme Inc" required />
        </div>

        <button type="submit" class="btn btn-primary submit-btn" :disabled="loading">
          {{ loading ? "Sending Link..." : "Get Magic Link" }}
        </button>

        <div v-if="message" class="alert alert-success">{{ message }}</div>
        <div v-if="error" class="alert alert-error">{{ error }}</div>
      </form>
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
.login-page { display: flex; align-items: center; justify-content: center; height: 100vh; background: var(--c-bg); }
.login-card { background: white; border: 2px solid var(--c-primary-dark); padding: 3rem; border-radius: 16px; box-shadow: 4px 4px 0 var(--c-primary-dark); max-width: 450px; width: 90%; }
.header h2 { font-family: 'Playfair Display', serif; font-size: 1.5rem; margin-bottom: 0.5rem; color: var(--c-primary-dark); }
.header p { font-size: 0.85rem; color: #666; margin-bottom: 2rem; }
.submit-btn { width: 100%; margin-top: 1rem; }
</style>
