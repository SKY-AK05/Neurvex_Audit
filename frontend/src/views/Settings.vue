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

      <div class="card">
        <div class="card-header-flex">
          <div>
            <h2>Security &amp; Traffic Management</h2>
            <p class="card-hint">
              Configure public assessment submission rate limits, burst thresholds, and abuse mitigation.
              Changes are committed to PostgreSQL and immediately synchronized across all application workers.
            </p>
          </div>
          <div class="sync-badge" :class="{ synchronized: rateLimitsMeta.sync_status === 'SYNCHRONIZED' }">
            <span class="sync-dot"></span>
            <span>{{ rateLimitsMeta.sync_status === 'SYNCHRONIZED' ? 'Workers In Sync' : 'Syncing' }}</span>
          </div>
        </div>

        <div class="meta-strip">
          <div class="meta-item">
            <span class="meta-label">Last Updated:</span>
            <span class="meta-val">{{ formatDate(rateLimitsMeta.last_updated_at) }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Updated By:</span>
            <span class="meta-val">{{ rateLimitsMeta.last_updated_by || 'system' }}</span>
          </div>
          <div class="meta-item">
            <span class="meta-label">Blocked (429):</span>
            <span class="meta-val">{{ rateLimitsMeta.metrics?.rate_limit_exceeded_total || 0 }}</span>
          </div>
        </div>

        <div class="fields-row rate-limits-grid">
          <div class="field">
            <label for="submit_rate_limit_hour">
              Public submissions / IP / hour
              <span class="limit-badge">Default: 500</span>
            </label>
            <input
              id="submit_rate_limit_hour"
              v-model.number="rateLimits.submit_rate_limit_hour"
              type="number"
              min="1"
              max="100000"
              required
            />
            <p class="field-help">Maximum assessment submissions per client IP within one hour (shared corporate IP).</p>
          </div>

          <div class="field">
            <label for="submit_rate_limit_day">
              Public submissions / IP / day
              <span class="limit-badge">Default: 2000</span>
            </label>
            <input
              id="submit_rate_limit_day"
              v-model.number="rateLimits.submit_rate_limit_day"
              type="number"
              min="1"
              max="1000000"
              required
            />
            <p class="field-help">Daily safety ceiling per client IP within 24 hours. Must be ≥ hourly limit.</p>
          </div>

          <div class="field">
            <label for="secure_submit_rate_limit_hour">
              Secure-link submissions / IP / hour
              <span class="limit-badge">Default: 500</span>
            </label>
            <input
              id="secure_submit_rate_limit_hour"
              v-model.number="rateLimits.secure_submit_rate_limit_hour"
              type="number"
              min="1"
              max="100000"
              required
            />
            <p class="field-help">Higher allowance for employees submitting through validated secure assessment links.</p>
          </div>

          <div class="field">
            <label for="secure_submit_rate_limit_day">
              Secure-link submissions / IP / day
              <span class="limit-badge">Default: 2000</span>
            </label>
            <input
              id="secure_submit_rate_limit_day"
              v-model.number="rateLimits.secure_submit_rate_limit_day"
              type="number"
              min="1"
              max="1000000"
              required
            />
            <p class="field-help">Daily ceiling for valid assessment-link traffic from a shared office network.</p>
          </div>

          <div class="field">
            <label for="assessment_session_limit_hour">
              Assessment session attempts / hour
              <span class="limit-badge">Default: 3</span>
            </label>
            <input
              id="assessment_session_limit_hour"
              v-model.number="rateLimits.assessment_session_limit_hour"
              type="number"
              min="1"
              max="100"
              required
            />
            <p class="field-help">Maximum submission attempts per draft session ID to stop retry spam.</p>
          </div>

          <div class="field">
            <label for="invalid_token_limit_minute">
              Invalid-token attempts / IP / min
              <span class="limit-badge">Default: 10</span>
            </label>
            <input
              id="invalid_token_limit_minute"
              v-model.number="rateLimits.invalid_token_limit_minute"
              type="number"
              min="1"
              max="1000"
              required
            />
            <p class="field-help">Aggressive mitigation against token brute-forcing, scanning, and revoked links.</p>
          </div>
        </div>

        <div class="rate-limit-actions">
          <button
            type="button"
            class="btn btn-primary"
            :disabled="savingRateLimits || resettingRateLimits"
            @click="saveRateLimits"
          >
            {{ savingRateLimits ? 'Saving…' : 'Save Rate Limits' }}
          </button>
          <button
            type="button"
            class="btn btn-outline"
            :disabled="savingRateLimits || resettingRateLimits || !hasRateLimitChanges"
            @click="cancelRateLimits"
          >
            Reset Changes
          </button>
          <button
            type="button"
            class="btn btn-outline"
            :disabled="savingRateLimits || resettingRateLimits"
            @click="handleRestoreDefaults"
          >
            {{ resettingRateLimits ? 'Restoring…' : 'Restore Defaults' }}
          </button>
          <div v-if="rateLimitMsg" :class="`alert alert-${rateLimitMsgType} msg-inline`">
            {{ rateLimitMsg }}
          </div>
        </div>
      </div>

      <div v-if="isSuperAdmin" class="card danger-zone">
        <h2 style="color: #C0392B;">⚠️ Danger Zone</h2>
        <p class="card-hint">
          <strong>Delete all submission records permanently.</strong> This action cannot be undone. All audit submissions, scores, and email drafts will be permanently deleted from the database. Organisations and admin user accounts will NOT be deleted.
        </p>
        <div class="delete-section">
          <div class="field" style="max-width: 400px;">
            <label for="delete-confirm">Type <strong>DELETE ALL SUBMISSIONS</strong> to confirm</label>
            <input 
              id="delete-confirm" 
              v-model="deleteConfirmText" 
              type="text" 
              placeholder="DELETE ALL SUBMISSIONS"
              :disabled="deleting"
            />
          </div>
          <button 
            type="button" 
            class="btn btn-danger" 
            @click="confirmDeleteAll"
            :disabled="deleteConfirmText !== 'DELETE ALL SUBMISSIONS' || deleting"
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
import { ref, reactive, computed, onMounted, onBeforeUnmount } from "vue";
import {
  getSettings,
  saveSettings,
  deleteAllRecords,
  getRateLimitSettings,
  updateRateLimitSettings,
  resetRateLimitSettings,
} from "../api";

const loading = ref(true);
const saving = ref(false);
const loadError = ref("");
const msg = ref("");
const msgType = ref("success");

const isSuperAdmin = ref(sessionStorage.getItem("nd_role") === "super");
const deleteConfirmText = ref("");
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

// Security & Traffic Management: Rate Limits State
const rateLimits = reactive({
  submit_rate_limit_hour: 500,
  submit_rate_limit_day: 2000,
  secure_submit_rate_limit_hour: 500,
  secure_submit_rate_limit_day: 2000,
  assessment_session_limit_hour: 3,
  invalid_token_limit_minute: 10,
});

const originalRateLimits = ref({ ...rateLimits });
const rateLimitsMeta = reactive({
  last_updated_at: null,
  last_updated_by: "system",
  last_synced_at: null,
  sync_status: "SYNCHRONIZED",
  metrics: { rate_limit_exceeded_total: 0, last_rate_limit_exceeded_at: null },
});
const savingRateLimits = ref(false);
const resettingRateLimits = ref(false);
const rateLimitMsg = ref("");
const rateLimitMsgType = ref("success");

const hasRateLimitChanges = computed(() => {
  return Object.keys(rateLimits).some(
    (k) => rateLimits[k] !== originalRateLimits.value[k]
  );
});

function formatDate(isoStr) {
  if (!isoStr) return "Never (System Defaults)";
  try {
    const d = new Date(isoStr);
    return d.toLocaleString("en-GB", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return isoStr;
  }
}

function applyRateLimitResponse(res) {
  if (!res) return;
  if (res.settings) {
    Object.assign(rateLimits, res.settings);
    originalRateLimits.value = { ...res.settings };
  }
  rateLimitsMeta.last_updated_at = res.last_updated_at;
  rateLimitsMeta.last_updated_by = res.last_updated_by;
  rateLimitsMeta.last_synced_at = res.last_synced_at;
  rateLimitsMeta.sync_status = res.sync_status || "SYNCHRONIZED";
  if (res.metrics) {
    rateLimitsMeta.metrics = res.metrics;
  }
}

function isSignificantIncrease(newVals, oldVals) {
  for (const k of Object.keys(newVals)) {
    const oldV = Number(oldVals[k]) || 0;
    const newV = Number(newVals[k]) || 0;
    if (oldV > 0 && newV >= oldV * 2 && newV - oldV >= 100) {
      return true;
    }
  }
  return false;
}

async function saveRateLimits() {
  rateLimitMsg.value = "";

  // Validation
  for (const [k, v] of Object.entries(rateLimits)) {
    if (v === null || v === undefined || v === "" || isNaN(v) || Number(v) <= 0) {
      rateLimitMsgType.value = "error";
      rateLimitMsg.value = "All rate limits must be positive integers.";
      return;
    }
  }

  if (Number(rateLimits.submit_rate_limit_day) < Number(rateLimits.submit_rate_limit_hour)) {
    rateLimitMsgType.value = "error";
    rateLimitMsg.value = "Public daily limit cannot be less than hourly limit.";
    return;
  }

  if (Number(rateLimits.secure_submit_rate_limit_day) < Number(rateLimits.secure_submit_rate_limit_hour)) {
    rateLimitMsgType.value = "error";
    rateLimitMsg.value = "Secure-link daily limit cannot be less than hourly limit.";
    return;
  }

  // Significant increase prompt
  if (isSignificantIncrease(rateLimits, originalRateLimits.value)) {
    const ok = confirm(
      "⚠️ Significant Rate Limit Increase\n\n" +
      "You are setting one or more rate limits to more than double their current values.\n" +
      "This permits higher inbound traffic volumes to the application.\n\n" +
      "Do you want to confirm this change?"
    );
    if (!ok) return;
  }

  savingRateLimits.value = true;
  try {
    const payload = {};
    for (const [k, v] of Object.entries(rateLimits)) {
      payload[k] = parseInt(v, 10);
    }
    const res = await updateRateLimitSettings(payload);
    applyRateLimitResponse(res);
    rateLimitMsgType.value = "success";
    rateLimitMsg.value = "Rate limits saved and synchronized across all workers.";
  } catch (e) {
    rateLimitMsgType.value = "error";
    rateLimitMsg.value = e.message || "Failed to save rate limits.";
  } finally {
    savingRateLimits.value = false;
  }
}

function cancelRateLimits() {
  Object.assign(rateLimits, originalRateLimits.value);
  rateLimitMsg.value = "";
}

async function handleRestoreDefaults() {
  const ok = confirm(
    "Restore Rate Limit Defaults\n\n" +
    "Are you sure you want to restore all submission rate limits to system defaults?\n" +
    "• Public: 500/hr, 2,000/day\n" +
    "• Secure-Link: 500/hr, 2,000/day\n" +
    "• Session Attempts: 3/hr\n" +
    "• Invalid Token Attempts: 10/min"
  );
  if (!ok) return;

  resettingRateLimits.value = true;
  rateLimitMsg.value = "";
  try {
    const res = await resetRateLimitSettings();
    applyRateLimitResponse(res);
    rateLimitMsgType.value = "success";
    rateLimitMsg.value = "Rate limits restored to system defaults.";
  } catch (e) {
    rateLimitMsgType.value = "error";
    rateLimitMsg.value = e.message || "Failed to restore defaults.";
  } finally {
    resettingRateLimits.value = false;
  }
}

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

  try {
    const rlRes = await getRateLimitSettings();
    applyRateLimitResponse(rlRes);
  } catch (e) {
    console.warn("Could not load rate limit settings:", e);
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
  if (deleteConfirmText.value !== "DELETE ALL SUBMISSIONS") {
    return;
  }

  const confirmed = confirm(
    "⚠️ WARNING: This will permanently delete ALL submission records from the database.\n\n" +
    "This includes:\n" +
    "• All audit submissions\n" +
    "• All scores and analysis\n" +
    "• All email drafts\n" +
    "• All submission history\n\n" +
    "Organisations and administrator user accounts will NOT be deleted.\n\n" +
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
    const result = await deleteAllRecords({ confirmation: deleteConfirmText.value });
    deleteMsgType.value = "success";
    deleteMsg.value = `✅ Successfully deleted ${result.deleted_count} submission record(s). All data has been permanently removed.`;
    deleteConfirmText.value = "";
    
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
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
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
  flex-wrap: wrap;
}
.actions .btn-primary {
  border-radius: 99px;
  padding: 0.75rem 1.75rem;
  font-weight: 700;
  min-height: 44px;
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
  padding: 0.75rem 1.5rem;
  font-weight: 700;
  min-height: 44px;
}

.card-header-flex {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.sync-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.4rem 0.85rem;
  border-radius: 99px;
  font-size: 0.78rem;
  font-weight: 700;
  background: #F1F5F9;
  color: #475569;
  border: 1px solid #CBD5E1;
  white-space: nowrap;
}

.sync-badge.synchronized {
  background: #DCFCE7;
  color: #166534;
  border-color: #86EFAC;
}

.sync-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #64748B;
}

.sync-badge.synchronized .sync-dot {
  background: #16A34A;
}

.meta-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  padding: 0.75rem 1rem;
  margin-bottom: 1.25rem;
}

.meta-item {
  display: flex;
  gap: 0.4rem;
  font-size: 0.82rem;
}

.meta-label {
  color: #64748B;
  font-weight: 500;
}

.meta-val {
  color: #0F172A;
  font-weight: 700;
}

.rate-limits-grid {
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
}

.limit-badge {
  font-size: 0.72rem;
  font-weight: 500;
  color: #64748B;
  background: #F1F5F9;
  padding: 0.15rem 0.45rem;
  border-radius: 4px;
  margin-left: 0.4rem;
}

.field-help {
  font-size: 0.76rem;
  color: #64748B;
  margin-top: 0.35rem;
  line-height: 1.35;
}

.rate-limit-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 1.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid rgba(22, 16, 87, 0.08);
  flex-wrap: wrap;
}

.rate-limit-actions .btn {
  border-radius: 99px;
  padding: 0.65rem 1.4rem;
  font-size: 0.875rem;
  font-weight: 600;
  min-height: 42px;
}

@media (max-width: 640px) {
  .card {
    padding: clamp(14px, 4vw, 20px);
    border-radius: 12px;
  }
  .fields-row {
    grid-template-columns: 1fr;
  }
  .actions .btn-primary {
    width: 100%;
    justify-content: center;
  }
  .delete-section {
    flex-direction: column;
    align-items: stretch;
  }
  .delete-section .field {
    min-width: 100%;
    max-width: 100% !important;
  }
  .delete-section .btn-danger {
    width: 100%;
    justify-content: center;
  }
}
</style>
