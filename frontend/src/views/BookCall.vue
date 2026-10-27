<template>
  <div class="book-page">
    <!-- Compact Top Header matching Reference Page 2 -->
    <header class="book-header">
      <router-link to="/" class="header-brand">
        <img src="/logonew1.png" alt="NIWI" class="niwi-logo" />
        <span class="niwi-brand-text">Neuro-Inclusive<br/>Workplace Index</span>
      </router-link>
      <div class="header-powered">
        <span class="powered-label">POWERED BY</span>
        <img src="/logo_orchvate.png" alt="Orchvate" class="orchvate-logo" />
      </div>
    </header>

    <div class="book-container">
      <!-- Success State -->
      <div v-if="submitted" class="success-wrap">
        <div class="success-card">
          <div class="success-icon">✓</div>
          <h2>Request Received</h2>
          <p class="success-desc">
            Thank you, <strong>{{ form.name }}</strong>. We'll be in touch at
            <strong>{{ form.email }}</strong> to confirm your call.
          </p>
          <router-link to="/" class="btn-primary-pill">Back to Self-Assessment →</router-link>
        </div>
      </div>

      <!-- Booking Form -->
      <div v-else class="book-card">
        <div class="card-head">
          <div class="card-tag">Orchvate Advisory</div>
          <h1 class="card-title">Book a Complimentary Call</h1>
          <p class="card-subtitle">
            We'd love to walk through your NIWI results, reflect on what they mean for your
            organisation, and explore the next phase of your neuro-inclusion journey.
          </p>
        </div>

        <form @submit.prevent="submit" class="book-form">
          <div class="fields-grid">
            <div class="field-group">
              <label class="field-label">Full Name *</label>
              <input
                v-model="form.name"
                type="text"
                class="field-input"
                placeholder="Jane Smith"
                required
              />
            </div>

            <div class="field-group">
              <label class="field-label">Job Title</label>
              <input
                v-model="form.designation"
                type="text"
                class="field-input"
                placeholder="HR Director"
              />
            </div>

            <div class="field-group">
              <label class="field-label">Organisation *</label>
              <input
                v-model="form.company"
                type="text"
                class="field-input"
                placeholder="Acme Ltd"
                required
              />
            </div>

            <div class="field-group">
              <label class="field-label">Work Email *</label>
              <input
                v-model="form.email"
                type="email"
                class="field-input"
                placeholder="jane@acme.com"
                required
              />
            </div>

            <div class="field-group full-width">
              <label class="field-label">Phone Number</label>
              <input
                v-model="form.phone"
                type="tel"
                class="field-input"
                placeholder="+44 7700 900000"
              />
            </div>

            <div class="field-group full-width">
              <label class="field-label">Preferred Time to Call</label>
              <select v-model="form.preferred_time" class="field-select">
                <option value="">No preference</option>
                <option>Morning (9 am – 12 pm IST)</option>
                <option>Afternoon (12 pm – 3 pm IST)</option>
                <option>Late afternoon (3 pm – 6 pm IST)</option>
              </select>
            </div>

            <div class="field-group full-width">
              <label class="field-label">Anything you'd like us to know?</label>
              <textarea
                v-model="form.message"
                rows="4"
                class="field-textarea"
                placeholder="e.g. specific areas from the audit you'd like to focus on…"
              ></textarea>
            </div>
          </div>

          <p v-if="errorMsg" class="alert-error">{{ errorMsg }}</p>

          <div class="card-footer">
            <router-link to="/" class="btn-ghost-pill">← Cancel</router-link>
            <button type="submit" class="btn-primary-pill" :disabled="loading">
              {{ loading ? "Sending…" : "Request a Call →" }}
            </button>
          </div>
        </form>
      </div>
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
const loading = ref(false);
const errorMsg = ref("");

async function submit() {
  errorMsg.value = "";
  if (!form.value.name?.trim() || !form.value.company?.trim() || !form.value.email?.trim()) {
    errorMsg.value = "Please fill in all required fields.";
    return;
  }
  loading.value = true;
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
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
  background: var(--bg, #FAFAF8);
  font-family: var(--font-body, 'Geist', 'Inter', sans-serif);
  color: var(--primary, #161057);
  overflow-y: auto;
}

/* Header */
.book-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 2.5rem;
  border-bottom: 1px solid rgba(22, 16, 87, 0.08);
  background: #FFFFFF;
  flex-shrink: 0;
}

.header-brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
}

.niwi-logo {
  height: 32px;
  width: auto;
  border-radius: 6px;
}

.niwi-brand-text {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--primary, #161057);
  line-height: 1.2;
}

.header-powered {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.powered-label {
  font-size: 0.6rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #9CA3AF;
}

.orchvate-logo {
  height: 20px;
  width: auto;
}

/* Container */
.book-container {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding: 2.5rem 1.5rem 4rem;
  max-width: 820px;
  margin: 0 auto;
  width: 100%;
}

.book-card {
  background: #FFFFFF;
  border: 1px solid rgba(22, 16, 87, 0.08);
  border-radius: 16px;
  padding: 2.5rem 2.5rem;
  box-shadow: 0 4px 24px rgba(22, 16, 87, 0.04);
  width: 100%;
}

.card-head {
  margin-bottom: 2rem;
}

.card-tag {
  display: inline-block;
  background: #EDE9FE;
  color: #6D28D9;
  font-size: 0.6875rem;
  font-weight: 700;
  padding: 0.22rem 0.65rem;
  border-radius: 99px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 0.75rem;
}

.card-title {
  font-family: 'Fraunces', serif;
  font-size: 1.85rem;
  font-weight: 800;
  color: var(--primary, #161057);
  letter-spacing: -0.025em;
  line-height: 1.2;
  margin-bottom: 0.5rem;
}

.card-subtitle {
  color: #64748B;
  font-size: 0.925rem;
  line-height: 1.6;
}

/* Form */
.book-form {
  display: flex;
  flex-direction: column;
}

.fields-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
  margin-bottom: 1.75rem;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.field-group.full-width {
  grid-column: 1 / -1;
}

.field-label {
  font-size: 0.825rem;
  font-weight: 600;
  color: #1E293B;
  letter-spacing: 0.01em;
}

.field-input,
.field-select,
.field-textarea {
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

.field-input:focus,
.field-select:focus,
.field-textarea:focus {
  border-color: var(--accent, #04907C);
  box-shadow: 0 0 0 3px rgba(4, 144, 124, 0.15);
}

.field-textarea {
  resize: vertical;
  min-height: 90px;
}

.alert-error {
  background: #FEE2E2;
  color: #991B1B;
  border: 1px solid #FCA5A5;
  border-radius: 10px;
  padding: 0.75rem 1rem;
  font-size: 0.85rem;
  margin-bottom: 1.5rem;
}

.card-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 1rem;
  padding-top: 1.25rem;
  border-top: 1px solid rgba(22, 16, 87, 0.08);
}

.btn-primary-pill {
  background: var(--primary, #161057);
  color: #FFFFFF;
  border: none;
  border-radius: 99px;
  padding: 0.75rem 2rem;
  font-size: 0.925rem;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  box-shadow: 0 4px 14px rgba(22, 16, 87, 0.2);
  transition: transform 0.2s, box-shadow 0.2s, background 0.2s;
}

.btn-primary-pill:hover:not(:disabled) {
  background: #0f0a42;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(22, 16, 87, 0.28);
}

.btn-primary-pill:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-ghost-pill {
  background: transparent;
  color: #64748B;
  border: 1px solid rgba(22, 16, 87, 0.14);
  border-radius: 99px;
  padding: 0.72rem 1.6rem;
  font-size: 0.9rem;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.btn-ghost-pill:hover {
  background: rgba(22, 16, 87, 0.04);
  color: var(--primary, #161057);
}

/* Success Card */
.success-wrap {
  width: 100%;
  display: flex;
  justify-content: center;
}

.success-card {
  background: #FFFFFF;
  border: 1px solid rgba(22, 16, 87, 0.08);
  border-radius: 16px;
  padding: 3.5rem 3rem;
  text-align: center;
  box-shadow: 0 8px 32px rgba(22, 16, 87, 0.05);
  max-width: 580px;
  width: 100%;
}

.success-icon {
  width: 64px;
  height: 64px;
  background: #E6F4F1;
  color: var(--accent, #04907C);
  border: 2px solid var(--accent, #04907C);
  border-radius: 50%;
  display: inline-grid;
  place-items: center;
  font-size: 1.8rem;
  font-weight: 700;
  margin: 0 auto 1.5rem;
}

.success-card h2 {
  font-family: 'Fraunces', serif;
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--primary, #161057);
  letter-spacing: -0.02em;
  margin-bottom: 0.85rem;
}

.success-desc {
  color: #475569;
  font-size: 0.95rem;
  line-height: 1.65;
  margin-bottom: 2rem;
}

@media (max-width: 680px) {
  .book-header {
    padding: 0.75rem 1.25rem;
  }
  .book-container {
    padding: 1.5rem 1rem 3rem;
  }
  .book-card {
    padding: 1.75rem 1.5rem;
  }
  .fields-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  .card-title {
    font-size: 1.5rem;
  }
}
</style>
