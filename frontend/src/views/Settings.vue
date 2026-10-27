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
        <div class="fields-row">
          <div class="field">
            <label for="sender-name">From name</label>
            <input id="sender-name" v-model="form.sender_name" type="text" placeholder="Orchvate" required />
          </div>
          <div class="field">
            <label for="sender-address">From email address</label>
            <input id="sender-address" v-model="form.sender_address" type="email" placeholder="noreply@yourdomain.com" required />
          </div>
        </div>
      </div>

      <div class="card">
        <h2>Support &amp; notifications</h2>
        <p class="card-hint">
          Support form messages are delivered to the support inbox. The notification email receives an alert each time a new audit is submitted.
        </p>
        <div class="fields-row">
          <div class="field">
            <label for="support-email">Support inbox email</label>
            <input id="support-email" v-model="form.support_email" type="email" placeholder="support@yourcompany.com" required />
          </div>
          <div class="field">
            <label for="notification-email">Notification email(s)</label>
            <input id="notification-email" v-model="form.notification_email" type="text" placeholder="admin@yourcompany.com" />
          </div>
          <div class="field">
            <label for="notification-cc-email">CC email(s) <span style="font-weight:400;color:#aaa">(optional)</span></label>
            <input id="notification-cc-email" v-model="form.notification_cc_email" type="text" placeholder="cc@yourcompany.com" />
          </div>
          <div class="field" style="display:flex;align-items:flex-end">
            <div class="notify-status" :class="{ on: form.notifications_enabled }" style="width:100%">
              <span class="notify-dot"></span>
              <span>{{ form.notifications_enabled ? 'Alerts ON — emailed for new submissions' : 'Alerts OFF — use bell icon to enable' }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <h2>Scoring &amp; analysis</h2>
        <p class="card-hint">
          Configure how audit responses are analyzed and flagged in the report.
        </p>
        <div class="fields-row">
          <div class="field">
            <label for="low-visibility-threshold">Low Visibility Threshold (%)</label>
            <input id="low-visibility-threshold" v-model.number="form.low_visibility_threshold" type="number" min="0" max="100" />
            <p style="font-size: 0.75rem; color: #888; margin-top: 0.3rem;">If this percentage or more of answers in a section are "Not Sure", it is flagged as Low Visibility.</p>
          </div>
        </div>
      </div>

      <div class="card danger-zone">
        <h2 style="color: #C0392B;">⚠️ Danger Zone</h2>
        <p class="card-hint">
          <strong>Delete all submission records permanently.</strong> This action cannot be undone. All audit submissions, scores, and email drafts will be permanently deleted from the database.
        </p>
        <div class="delete-section">
          <div class="field" style="max-width: 400px;">
            <label for="delete-password">Enter password to confirm deletion</label>
            <input 
              id="delete-password" 
              v-model="deletePassword" 
              type="password" 
              placeholder="Enter deletion password"
              :disabled="deleting"
            />
          </div>
          <button 
            type="button" 
            class="btn btn-danger" 
            @click="confirmDeleteAll"
            :disabled="!deletePassword || deleting"
          >
            {{ deleting ? 'Deleting...' : '🗑️ Delete All Records' }}
          </button>
        </div>
        <div v-if="deleteMsg" :class="`alert alert-${deleteMsgType}`" style="margin-top: 1rem;">{{ deleteMsg }}</div>
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
import { getSettings, saveSettings, deleteAllRecords } from "../api";

const loading = ref(true);
const saving = ref(false);
const loadError = ref("");
const msg = ref("");
const msgType = ref("success");

const deletePassword = ref("");
const deleting = ref(false);
const deleteMsg = ref("");
const deleteMsgType = ref("success");

const form = reactive({
  sender_name: "",
  sender_address: "",
  notification_email: "",
  notification_cc_email: "",
  notifications_enabled: false,
  support_email: "",
  low_visibility_threshold: 50,
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
    form.low_visibility_threshold = data.low_visibility_threshold !== undefined ? data.low_visibility_threshold : 50;
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
    form.low_visibility_threshold = data.low_visibility_threshold;
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

async function confirmDeleteAll() {
  const confirmed = confirm(
    "⚠️ WARNING: This will permanently delete ALL submission records from the database.\n\n" +
    "This includes:\n" +
    "• All audit submissions\n" +
    "• All scores and analysis\n" +
    "• All email drafts\n" +
    "• All submission history\n\n" +
    "This action CANNOT be undone.\n\n" +
    "Are you absolutely sure you want to proceed?"
  );

  if (!confirmed) {
    return;
  }

  // Second confirmation
  const secondConfirm = confirm(
    "⚠️ FINAL WARNING\n\n" +
    "You are about to delete ALL records permanently.\n\n" +
    "Click OK to proceed with deletion, or Cancel to abort."
  );

  if (!secondConfirm) {
    return;
  }

  deleting.value = true;
  deleteMsg.value = "";

  try {
    const result = await deleteAllRecords(deletePassword.value);
    deleteMsgType.value = "success";
    deleteMsg.value = `✅ Successfully deleted ${result.deleted_count} submission record(s). All data has been permanently removed.`;
    deletePassword.value = "";
    
    // Refresh the page after 3 seconds to clear any cached data
    setTimeout(() => {
      window.location.reload();
    }, 3000);
  } catch (e) {
    deleteMsgType.value = "error";
    deleteMsg.value = `❌ ${e.message}`;
  } finally {
    deleting.value = false;
  }
}
</script>

<style scoped>
.page-header { margin-bottom: 1.5rem; }
.page-header h1 {
  font-size: 2.25rem; font-weight: 800; color: var(--c-primary-dark, #161057);
  letter-spacing: -0.03em; font-family: 'Fraunces', serif;
}
.page-header p { color: #64748B; font-size: 0.9rem; margin-top: 0.35rem; }

.settings-form {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  max-width: 100%;
}

.card {
  background: var(--c-white, #FFFFFF);
  border: 1px solid rgba(22, 16, 87, 0.08);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(22, 16, 87, 0.03);
}

.card h2 {
  font-size: 1.15rem; font-weight: 800; color: var(--c-primary-dark, #161057);
  margin-bottom: 0.35rem;
  border: none; font-family: 'Fraunces', serif;
  letter-spacing: -0.015em;
}
.card-hint {
  font-size: 0.85rem; color: #64748B; line-height: 1.5;
  margin-bottom: 1.25rem;
}

.fields-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
}

.notify-status {
  display: flex; align-items: flex-start; gap: 0.6rem;
  padding: 0.75rem 1rem; border-radius: 10px;
  background: #FAFAF8; border: 1px solid rgba(22, 16, 87, 0.08);
  font-size: 0.85rem; color: #475569; line-height: 1.45;
  margin-top: 0.5rem;
}
.notify-status.on {
  background: #DCFCE7; border-color: #86EFAC; color: #166534; font-weight: 600;
}
.notify-dot {
  width: 10px; height: 10px; border-radius: 50%;
  background: #94A3B8; flex-shrink: 0; margin-top: 0.25em;
}
.notify-status.on .notify-dot { background: #16A34A; }

.actions {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding-top: 0.5rem;
}
.actions .btn-primary {
  border-radius: 99px;
  padding: 0.65rem 1.6rem;
  font-weight: 700;
  box-shadow: 0 4px 14px rgba(22, 16, 87, 0.2);
}
.msg-inline { margin: 0; padding: 0.6rem 1rem; border-radius: 8px; }
.loading { color: #94A3B8; padding: 2rem 0; }

.danger-zone {
  border: 1px solid #FECACA;
  background: #FFFDFD;
}

.danger-zone h2 {
  border-bottom: 1px solid rgba(192, 57, 43, 0.12);
  padding-bottom: 0.5rem;
  margin-bottom: 0.5rem;
}

.delete-section {
  display: flex;
  align-items: flex-end;
  gap: 1rem;
  margin-top: 1rem;
  flex-wrap: wrap;
}

.delete-section .field {
  flex: 1;
  min-width: 250px;
}
.delete-section .btn-danger {
  border-radius: 99px;
  padding: 0.65rem 1.5rem;
  font-weight: 700;
}
</style>
