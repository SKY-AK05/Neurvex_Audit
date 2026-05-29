<template>
  <div class="form-page">
    <div class="form-inner">
      <header class="form-header">
        <div class="form-header-left">
          <router-link to="/" class="form-logo">
            <img src="/logonew1.png" alt="" class="form-logo-img" />
            <span class="form-logo-name">Neuro-Inclusive Workplace Index</span>
          </router-link>
        </div>
        <div class="form-header-right">
          <div class="header-powered">
            <span class="header-powered-label">Powered by</span>
            <img src="/logo_orchvate.png" alt="Orchvate" class="header-powered-logo" />
          </div>
        </div>
      </header>

      <div v-if="submitted" class="success-wrap">
        <div class="success-box">
          <div class="success-icon">?</div>
          <h2>Request received</h2>
          <p>
            Thank you, <strong>{{ form.name }}</strong>. We'll be in touch at
            <strong>{{ form.email }}</strong> to confirm your call.
          </p>
          <router-link to="/" class="btn-back">Back to audit</router-link>
        </div>
      </div>

      <div v-else class="book-wrap">
        <div class="book-card">
          <div class="step-card-head">
            <div class="step-tag">Orchvate</div>
            <h1>Book a Complimentary Call</h1>
            <p class="step-sub">
              We'd love to walk through your NIWI results, reflect on what they mean for your
              organisation, and explore the next phase of your neurodiversity inclusion journey.
            </p>
          </div>

          <div class="book-scroll">
            <form @submit.prevent="submit" class="book-form">
              <div class="fields-grid">
                <div class="field">
                  <label>Full name *</label>
                  <input v-model="form.name" type="text" placeholder="Jane Smith" required />
                </div>
                <div class="field">
                  <label>Job title</label>
                  <input v-model="form.designation" type="text" placeholder="HR Director" />
                </div>
                <div class="field">
                  <label>Organisation *</label>
                  <input v-model="form.company" type="text" placeholder="Acme Ltd" required />
                </div>
                <div class="field">
                  <label>Work email *</label>
                  <input v-model="form.email" type="email" placeholder="jane@acme.com" required />
                </div>
                <div class="field field--full">
                  <label>Phone number</label>
                  <input v-model="form.phone" type="tel" placeholder="+44 7700 900000" />
                </div>
                <div class="field field--full">
                  <label>Preferred time to call</label>
                  <select v-model="form.preferred_time">
                    <option value="">No preference</option>
                    <option>Morning (9 am – 12 pm IST)</option>
                    <option>Afternoon (12 pm – 3 pm IST)</option>
                    <option>Late afternoon (3 pm – 6 pm IST)</option>
                  </select>
                </div>
                <div class="field field--full">
                  <label>Anything you'd like us to know?</label>
                  <textarea
                    v-model="form.message"
                    rows="4"
                    placeholder="e.g. specific areas from the audit you'd like to focus on…"
                  ></textarea>
                </div>
              </div>

              <p v-if="errorMsg" class="alert alert-error">{{ errorMsg }}</p>
            </form>
          </div>

          <div class="book-actions">
            <button type="button" class="btn-submit" :disabled="loading" @click="submit">
              {{ loading ? "Sending…" : "Request a call ?" }}
            </button>
          </div>
        </div>
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
.form-page {
  flex: 1;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background: var(--c-bg);
  background-image:
    linear-gradient(to right, rgba(180, 175, 165, 0.25) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(180, 175, 165, 0.25) 1px, transparent 1px);
  background-size: 32px 32px;
  border-radius: 32px;
  box-shadow: 0 12px 48px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
}

.form-inner {
  display: flex;
  flex-direction: column;
  flex: 1;
  width: 100%;
  min-height: 0;
  overflow: hidden;
}

.form-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.6rem 2rem;
  border-bottom: 2px solid var(--c-primary-dark);
  background: var(--c-bg);
  flex-shrink: 0;
  z-index: 10;
}

.form-header-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.form-header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-left: auto;
}

.form-logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  color: inherit;
}

.form-logo-img {
  height: 36px;
  width: auto;
  display: block;
  object-fit: contain;
  border-radius: 6px;
  flex-shrink: 0;
}

.form-logo-name {
  font-size: 0.95rem;
  font-weight: 800;
  color: var(--c-primary-dark);
  font-family: "Fraunces", serif;
}

.header-powered {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.header-powered-label {
  font-size: 0.7rem;
  color: #aaa;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.header-powered-logo {
  height: 22px;
  width: auto;
  object-fit: contain;
  opacity: 0.65;
}

.book-wrap {
  flex: 1;
  min-height: 0;
  overflow: hidden;
  display: flex;
  justify-content: center;
  padding: 0.75rem 2rem 1rem;
  width: 100%;
  box-sizing: border-box;
}

.book-card {
  display: flex;
  flex-direction: column;
  min-height: 0;
  max-height: 100%;
  width: 100%;
  max-width: 720px;
  overflow: hidden;
  background: var(--c-white);
  border: 2px solid var(--c-primary-dark);
  border-radius: 20px;
  box-shadow: 4px 4px 0 rgba(22, 16, 87, 0.15);
}

.step-card-head {
  flex-shrink: 0;
  padding: 2rem 2.5rem 0;
}

.step-tag {
  display: inline-block;
  background: transparent;
  color: #161057;
  font-size: 0.7rem;
  font-weight: 800;
  padding: 0.2rem 0.7rem;
  border-radius: 99px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 0.85rem;
  border: 1.5px solid #161057;
  font-family: "Fraunces", serif;
}

.step-card-head h1 {
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--c-primary-dark);
  letter-spacing: -0.03em;
  margin-bottom: 0.35rem;
  font-family: "Fraunces", serif;
}

.step-sub {
  color: #999;
  font-size: 0.875rem;
  margin-bottom: 0;
  line-height: 1.55;
}

.book-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  overscroll-behavior: contain;
  padding: 1.25rem 2.5rem 1rem;
  -webkit-overflow-scrolling: touch;
}

.book-form {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.fields-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.field--full {
  grid-column: 1 / -1;
}

.field label {
  display: block;
  font-size: 0.72rem;
  font-weight: 800;
  color: var(--c-primary-dark);
  margin-bottom: 0.35rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-family: "Fraunces", serif;
}

.field input,
.field select,
.field textarea {
  width: 100%;
  padding: 0.7rem 0.9rem;
  border: 2px solid var(--c-primary-dark);
  border-radius: 10px;
  font-size: 0.9rem;
  background: var(--c-white);
  color: var(--c-primary-dark);
  transition: border-color 0.15s, box-shadow 0.15s;
  font-family: inherit;
  box-sizing: border-box;
}

.field textarea {
  resize: vertical;
  min-height: 100px;
}

.field input:focus,
.field select:focus,
.field textarea:focus {
  outline: none;
  border-color: var(--c-primary-dark);
  box-shadow: 3px 3px 0 var(--c-accent);
}

.book-actions {
  flex-shrink: 0;
  padding: 1rem 2.5rem 1.5rem;
  border-top: 1px solid #e2ddd4;
}

.btn-submit {
  background: var(--c-primary-dark);
  color: var(--c-white);
  border: 2px solid var(--c-primary-dark);
  border-radius: 99px;
  padding: 0.7rem 1.75rem;
  font-size: 0.9rem;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.15s;
  font-family: "Fraunces", serif;
  box-shadow: 3px 3px 0 rgba(22, 16, 87, 0.3);
}

.btn-submit:hover:not(:disabled) {
  transform: translate(-2px, -2px);
  box-shadow: 5px 5px 0 rgba(22, 16, 87, 0.3);
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  box-shadow: none;
}

.alert {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  font-size: 0.875rem;
  margin-top: 0.75rem;
}

.alert-error {
  background: #fff0f0;
  color: #c0392b;
  border: 1px solid #ffcaca;
}

.success-wrap {
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  overflow-y: auto;
}

.success-box {
  background: var(--c-white);
  border-radius: 16px;
  padding: 3rem 2.5rem;
  text-align: center;
  border: 2px solid var(--c-primary-dark);
  max-width: 440px;
  width: 100%;
  box-shadow: 4px 4px 0 rgba(22, 16, 87, 0.15);
}

.success-icon {
  width: 64px;
  height: 64px;
  background: var(--c-accent);
  border-radius: 50%;
  display: inline-grid;
  place-items: center;
  font-size: 1.8rem;
  margin-bottom: 1.25rem;
  color: var(--c-primary-dark);
  font-weight: 800;
}

.success-box h2 {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--c-primary-dark);
  margin-bottom: 0.75rem;
  font-family: "Fraunces", serif;
}

.success-box p {
  color: #666;
  line-height: 1.6;
  font-size: 0.9rem;
  margin-bottom: 1.5rem;
}

.btn-back {
  display: inline-block;
  background: var(--c-white);
  border: 2px solid var(--c-primary-dark);
  border-radius: 99px;
  padding: 0.65rem 1.4rem;
  font-size: 0.875rem;
  font-weight: 700;
  cursor: pointer;
  color: var(--c-primary-dark);
  text-decoration: none;
  font-family: "Fraunces", serif;
  box-shadow: 3px 3px 0 var(--c-primary-dark);
  transition: all 0.15s;
}

.btn-back:hover {
  transform: translate(-2px, -2px);
  box-shadow: 5px 5px 0 var(--c-primary-dark);
}

@media (max-width: 640px) {
  .form-header {
    padding: 0.6rem 1rem;
  }

  .form-logo-name {
    font-size: 0.8rem;
  }

  .book-wrap {
    padding: 0.5rem 1rem 0.75rem;
  }

  .step-card-head {
    padding: 1.25rem 1.25rem 0;
  }

  .book-scroll {
    padding: 1rem 1.25rem 0.75rem;
  }

  .book-actions {
    padding: 0.85rem 1.25rem 1.25rem;
  }

  .fields-grid {
    grid-template-columns: 1fr;
  }

  .step-card-head h1 {
    font-size: 1.45rem;
  }
}
</style>
