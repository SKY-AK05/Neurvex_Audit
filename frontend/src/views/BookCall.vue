<template>
  <div class="book-page">
    <div class="book-card">
      <!-- Header -->
      <div class="book-header">
        <p class="brand">Orchvate</p>
        <h1>Book a Complimentary Call</h1>
        <p class="subtitle">
          We'd love to walk through your NIWI � Neuro-Inclusive Workplace Index results, reflect on what they mean for your
          organisation, and explore the next phase of your neurodiversity inclusion journey.
        </p>
      </div>

      <!-- Success state -->
      <div v-if="submitted" class="success-box">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#3A7A00" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="9 12 11 14 15 10"/></svg>
        <h2>Request received!</h2>
        <p>Thank you, <strong>{{ form.name }}</strong>. We'll be in touch at <strong>{{ form.email }}</strong> to confirm your call.</p>
      </div>

      <!-- Form -->
      <form v-else @submit.prevent="submit" class="book-form">
        <div class="field-row">
          <div class="field">
            <label>Full name <span class="req">*</span></label>
            <input v-model="form.name" type="text" placeholder="Jane Smith" required />
          </div>
          <div class="field">
            <label>Job title</label>
            <input v-model="form.designation" type="text" placeholder="HR Director" />
          </div>
        </div>

        <div class="field-row">
          <div class="field">
            <label>Organisation <span class="req">*</span></label>
            <input v-model="form.company" type="text" placeholder="Acme Ltd" required />
          </div>
          <div class="field">
            <label>Work email <span class="req">*</span></label>
            <input v-model="form.email" type="email" placeholder="jane@acme.com" required />
          </div>
        </div>

        <div class="field">
          <label>Phone number</label>
          <input v-model="form.phone" type="tel" placeholder="+44 7700 900000" />
        </div>

        <div class="field">
          <label>Preferred time to call</label>
          <select v-model="form.preferred_time">
            <option value="">No preference</option>
            <option>Morning (9 am – 12 pm IST)</option>
            <option>Afternoon (12 pm – 3 pm IST)</option>
            <option>Late afternoon (3 pm – 6 pm IST)</option>
          </select>
        </div>

        <div class="field">
          <label>Anything you'd like us to know?</label>
          <textarea v-model="form.message" rows="3" placeholder="e.g. specific areas from the audit you'd like to focus on…"></textarea>
        </div>

        <p v-if="errorMsg" class="form-error">{{ errorMsg }}</p>

        <button type="submit" class="submit-btn" :disabled="loading">
          <span v-if="loading">Sending…</span>
          <span v-else>Request a call →</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

const form = ref({
  name: "",
  designation: "",
  company: "",
  email: "",
  phone: "",
  preferred_time: "",
  message: "",
});

const submitted = ref(false);
const loading   = ref(false);
const errorMsg  = ref("");

async function submit() {
  errorMsg.value = "";
  loading.value  = true;
  try {
    const res = await fetch(`${API_BASE}/book-call`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form.value),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw new Error(data.detail || "Something went wrong. Please try again.");
    }
    submitted.value = true;
  } catch (e) {
    errorMsg.value = e.message;
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.book-page {
  min-height: 100vh;
  background: #F4F2F0;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 3rem 1rem 4rem;
}

.book-card {
  background: #fff;
  border-radius: 16px;
  border: 2px solid #1E1A4A;
  box-shadow: 6px 6px 0 rgba(0,0,0,0.08);
  max-width: 640px;
  width: 100%;
  overflow: hidden;
}

.book-header {
  background: #1E1A4A;
  padding: 2.5rem 2.5rem 2rem;
  color: #fff;
}

.brand {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: #AFA9EC;
  margin: 0 0 1rem;
}

.book-header h1 {
  font-family: 'Fraunces', serif;
  font-size: 1.75rem;
  font-weight: 700;
  margin: 0 0 0.75rem;
  line-height: 1.2;
}

.subtitle {
  font-size: 0.9rem;
  color: #AFA9EC;
  line-height: 1.6;
  margin: 0;
}

.book-form {
  padding: 2rem 2.5rem 2.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.field label {
  font-size: 0.8rem;
  font-weight: 700;
  color: #1E1A4A;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.req { color: #C0392B; }

.field input,
.field select,
.field textarea {
  border: 2px solid #1E1A4A;
  border-radius: 8px;
  padding: 0.65rem 0.9rem;
  font-size: 0.95rem;
  font-family: 'Inter', sans-serif;
  color: #1E1A4A;
  background: #fff;
  outline: none;
  transition: box-shadow 0.15s, transform 0.15s;
  resize: vertical;
}

.field input:focus,
.field select:focus,
.field textarea:focus {
  box-shadow: 4px 4px 0 #7F77DD;
  transform: translate(-2px, -2px);
}

.form-error {
  color: #C0392B;
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0;
}

.submit-btn {
  background: #1E1A4A;
  color: #fff;
  border: 2px solid #1E1A4A;
  border-radius: 8px;
  padding: 0.85rem 2rem;
  font-size: 0.95rem;
  font-weight: 700;
  cursor: pointer;
  font-family: 'Inter', sans-serif;
  transition: background 0.15s, box-shadow 0.15s, transform 0.15s;
  align-self: flex-start;
}

.submit-btn:hover:not(:disabled) {
  background: #7F77DD;
  border-color: #7F77DD;
  box-shadow: 4px 4px 0 rgba(0,0,0,0.15);
  transform: translate(-2px, -2px);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.success-box {
  padding: 3rem 2.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 1rem;
}

.success-box h2 {
  font-family: 'Fraunces', serif;
  font-size: 1.5rem;
  color: #1E1A4A;
  margin: 0;
}

.success-box p {
  color: #555;
  font-size: 0.95rem;
  line-height: 1.6;
  margin: 0;
}

@media (max-width: 520px) {
  .book-header { padding: 2rem 1.5rem 1.5rem; }
  .book-form { padding: 1.5rem; }
  .field-row { grid-template-columns: 1fr; }
}
</style>
