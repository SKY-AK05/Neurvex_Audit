<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Settings</h1>
        <p>Configure sender details for outgoing emails and admin submission alerts.</p>
      </div>
    </div>

    <p v-if="loading" class="loading">Loading settings…</p>
    <p v-else-if="loadError" class="alert alert-error">{{ loadError }}</p>

    <form v-else class="settings-form" @submit.prevent="save">
      <div class="card">
        <h2>Email sender</h2>
        <p class="card-hint">
          Used as the from address when sending audit results to respondents.
          Must be a domain verified in Azure Communication Services.
        </p>

        <div class="field">
          <label for="sender-name">From name</label>
          <input
            id="sender-name"
            v-model="form.sender_name"
            type="text"
            placeholder="Orchvate"
            required
          />
        </div>

        <div class="field">
          <label for="sender-address">From email address</label>
          <input
            id="sender-address"
            v-model="form.sender_address"
            type="email"
            placeholder="noreply@yourdomain.com"
            required
          />
        </div>
      </div>

      <div class="card">
        <h2>Support requests</h2>
        <p class="card-hint">
          Support form messages from the Support page are delivered to this inbox.
        </p>
        <div class="field">
          <label for="support-email">Support inbox email</label>
          <input
            id="support-email"
            v-model="form.support_email"
            type="email"
            placeholder="aakash.padyachi@rochvate.com"
            required
          />
        </div>
      </div>

      <div class="card">
        <h2>Admin notifications</h2>
        <p class="card-hint">
          When the bell icon is on in the header, this address receives an email
          each time someone submits a new audit.
        </p>

        <div class="field">
          <label for="notification-email">Notification email(s)</label>
          <input
            id="notification-email"
            v-model="form.notification_email"
            type="text"
            placeholder="admin@yourcompany.com, other@company.com"
          />
        </div>

        <div class="field">
          <label for="notification-cc-email">CC email(s)</label>
          <input
            id="notification-cc-email"
            v-model="form.notification_cc_email"
            type="text"
            placeholder="cc@yourcompany.com (optional)"
          />
        </div>

        <div class="notify-status" :class="{ on: form.notifications_enabled }">
          <span class="notify-dot"></span>
          <span>
            {{ form.notifications_enabled
              ? 'Alerts are ON — you will be emailed for new submissions'
              : 'Alerts are OFF — click the bell in the header to turn on' }}
          </span>
        </div>
      </div>

      <div class="actions">
        <button type="submit" class="btn btn-primary" :disabled="saving">
          {{ saving ? 'Saving…' : 'Save Settings' }}
        </button>
        <div v-if="msg" :class="`alert alert-${msgType} msg-inline`">{{ msg }}</div>
      </div>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from "vue";
import { getSettings, saveSettings } from "../api";

const loading = ref(true);
const saving = ref(false);
const loadError = ref("");
const msg = ref("");
const msgType = ref("success");

const form = reactive({
  sender_name: "",
  sender_address: "",
  notification_email: "",
  notification_cc_email: "",
  notifications_enabled: false,
  support_email: "",
});

onMounted(async () => {
  try {
    const data = await getSettings();
    form.sender_name = data.sender_name || "";
    form.sender_address = data.sender_address || "";
    form.notification_email = data.notification_email || "";
    form.notification_cc_email = data.notification_cc_email || "";
    form.notifications_enabled = !!data.notifications_enabled;
    form.support_email = data.support_email || "";
  } catch (e) {
    loadError.value = e.message;
  } finally {
    loading.value = false;
  }
  
  window.addEventListener("settings-updated", syncFromApp);
});

onBeforeUnmount(() => {
  window.removeEventListener("settings-updated", syncFromApp);
});

function syncFromApp(e) {
  // Only sync the toggle state to prevent overwriting user's typing in the email fields
  if (e.detail !== undefined && e.detail.notifications_enabled !== undefined) {
    form.notifications_enabled = !!e.detail.notifications_enabled;
  }
}

async function save() {
  saving.value = true;
  msg.value = "";
  try {
    const data = await saveSettings({ ...form });
    form.sender_name = data.sender_name;
    form.sender_address = data.sender_address;
    form.notification_email = data.notification_email;
    form.notification_cc_email = data.notification_cc_email;
    form.notifications_enabled = data.notifications_enabled;
    form.support_email = data.support_email || "";
    window.dispatchEvent(new CustomEvent("settings-updated", { detail: data }));
    msgType.value = "success";
    msg.value = "Settings saved.";
  } catch (e) {
    msgType.value = "error";
    msg.value = e.message;
  } finally {
    saving.value = false;
  }
}
</script>

<style scoped>
.page-header { margin-bottom: 1.5rem; }
.page-header h1 {
  font-size: 1.7rem; font-weight: 700; color: var(--c-primary-dark);
  letter-spacing: -0.02em; font-family: 'Playfair Display', serif;
}
.page-header p { color: #888; font-size: 0.875rem; margin-top: 0.3rem; }

.settings-form { 
  display: grid; 
  grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); 
  gap: 1.5rem; 
  max-width: 1200px; 
  align-items: start;
}

.card h2 {
  font-size: 1rem; font-weight: 700; color: var(--c-primary-dark);
  margin-bottom: 0.35rem; padding-bottom: 0;
  border: none; font-family: 'Playfair Display', serif;
}
.card-hint {
  font-size: 0.82rem; color: #888; line-height: 1.5;
  margin-bottom: 1.25rem;
}



.notify-status {
  display: flex; align-items: flex-start; gap: 0.6rem;
  padding: 0.85rem 1rem; border-radius: 10px;
  background: var(--c-bg); border: 1.5px solid #E2DDD4;
  font-size: 0.85rem; color: #666; line-height: 1.45;
  margin-top: 0.5rem;
}
.notify-status.on {
  background: #EDFFD4; border-color: var(--c-accent); color: #3A5A00;
}
.notify-dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: #ccc; flex-shrink: 0; margin-top: 0.25em;
}
.notify-status.on .notify-dot { background: var(--c-accent); box-shadow: 0 0 0 2px var(--c-primary-dark); }

.actions { 
  grid-column: 1 / -1; 
  display: flex; 
  align-items: center;
  gap: 1.25rem; 
  margin-top: 1rem;
}
.msg-inline {
  margin: 0;
  padding: 0.6rem 1rem;
}
.loading { color: #aaa; padding: 2rem 0; }
</style>
