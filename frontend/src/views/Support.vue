<template>
  <div>
    <div class="page-header">
      <h1>Support</h1>
      <p>Send a message to the Orchvate team. You will receive a reply at the email you provide.</p>
    </div>

    <div class="support-layout">
      <div class="card support-card">
        <h2>Contact support</h2>
        <p class="card-hint">
          Describe your issue or question. Your request is emailed to our support team.
        </p>

        <form class="support-form" @submit.prevent="submit">
          <div class="field">
            <label for="support-name">Your name *</label>
            <input id="support-name" v-model="form.name" type="text" placeholder="Jane Smith" required />
          </div>
          <div class="field">
            <label for="support-email">Your email *</label>
            <input id="support-email" v-model="form.email" type="email" placeholder="you@company.com" required />
          </div>
          <div class="field">
            <label for="support-subject">Subject *</label>
            <input id="support-subject" v-model="form.subject" type="text" placeholder="Brief summary" required />
          </div>
          <div class="field">
            <label for="support-message">Message *</label>
            <textarea
              id="support-message"
              v-model="form.message"
              rows="6"
              placeholder="How can we help?"
              required
            ></textarea>
          </div>
          <button type="submit" class="btn btn-primary" :disabled="sending">
            {{ sending ? 'Sending…' : 'Send request →' }}
          </button>
        </form>

        <div v-if="msg" :class="`alert alert-${msgType}`" style="margin-top:1rem">{{ msg }}</div>
      </div>

      <div class="card info-card">
        <h2>Before you write</h2>
        <ul class="info-list">
          <li>Include your organisation name if relevant to the audit tool.</li>
          <li>For submission issues, mention the respondent or submission ID.</li>
          <li>We aim to respond within 1–2 business days.</li>
        </ul>
        <p class="info-email">
          Requests are sent to our support inbox. Replies will come to the email address you enter above.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { submitSupportRequest } from "../api";

const form = reactive({
  name: "",
  email: "",
  subject: "",
  message: "",
});

const sending = ref(false);
const msg = ref("");
const msgType = ref("success");

onMounted(() => {
  const saved = sessionStorage.getItem("support_contact");
  if (saved) {
    try {
      const c = JSON.parse(saved);
      if (c.name) form.name = c.name;
      if (c.email) form.email = c.email;
    } catch { /* ignore */ }
  }
});

async function submit() {
  sending.value = true;
  msg.value = "";
  try {
    const res = await submitSupportRequest({ ...form });
    sessionStorage.setItem("support_contact", JSON.stringify({
      name: form.name,
      email: form.email,
    }));
    msgType.value = "success";
    msg.value = res.message || "Your support request was sent successfully.";
    form.subject = "";
    form.message = "";
  } catch (e) {
    msgType.value = "error";
    msg.value = e.message;
  } finally {
    sending.value = false;
  }
}
</script>

<style scoped>
.page-header { margin-bottom: 1.5rem; }
.page-header h1 {
  font-size: 1.7rem; font-weight: 700; color: var(--c-primary-dark);
  font-family: 'Fraunces', serif;
}
.page-header p { color: #888; font-size: 0.875rem; margin-top: 0.3rem; }

.support-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 1.25rem;
  align-items: start;
  max-width: 860px;
}

.support-card h2,
.info-card h2 {
  font-size: 1rem; font-weight: 700; margin-bottom: 0.35rem;
  font-family: 'Fraunces', serif;
}
.card-hint {
  font-size: 0.82rem; color: #888; line-height: 1.5;
  margin-bottom: 1rem;
}

.info-list {
  margin: 0 0 1rem; padding-left: 1.2rem;
  font-size: 0.85rem; color: #555; line-height: 1.7;
}
.info-email {
  font-size: 0.8rem; color: #888; line-height: 1.5;
  padding-top: 0.75rem; border-top: 1px solid #E2DDD4;
}

@media (max-width: 800px) {
  .support-layout { grid-template-columns: 1fr; }
  .info-card { order: -1; }
}
</style>
