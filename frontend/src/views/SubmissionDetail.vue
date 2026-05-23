<template>
  <div>
    <!-- Back -->
    <button class="back-btn" @click="$router.push('/admin/submissions')">
      ← Back to submissions
    </button>

    <p v-if="loading" class="loading">Loading…</p>
    <p v-else-if="error" class="alert alert-error">{{ error }}</p>

    <template v-else-if="sub">

      <!-- Respondent -->
      <div class="card">
        <h2>Respondent</h2>
        <div class="info-grid">
          <div class="info-item">
            <label>Name</label>
            <span>{{ sub.name }}</span>
          </div>
          <div class="info-item">
            <label>Organisation</label>
            <span>{{ sub.company_name }}</span>
          </div>
          <div class="info-item">
            <label>Job Role / Designation</label>
            <span>{{ sub.designation || '—' }}</span>
          </div>
          <div class="info-item">
            <label>Email</label>
            <span>{{ sub.email }}</span>
          </div>
          <div class="info-item">
            <label>Contact</label>
            <span>{{ sub.contact_number || "—" }}</span>
          </div>
          <div class="info-item">
            <label>Submitted</label>
            <span>{{ fmtDate(sub.submitted_at) }}</span>
          </div>
          <div class="info-item">
            <label>Status</label>
            <div class="status-row">
              <span :class="`badge badge-${sub.status === 'sent' ? 'delivered' : 'pending'}`">
                <span class="badge-dot"></span>
                {{ sub.status === 'sent' ? 'Delivered' : 'Pending' }}
              </span>
              <span v-if="sub.status === 'sent'" class="sent-time">Sent {{ fmtDate(sub.sent_at) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Score Breakdown -->
      <div class="card">
        <h2>Score Breakdown</h2>
        <ScoreTable :data="sub" />
      </div>

      <!-- Email Draft -->
      <div class="card">
        <div class="email-header">
          <h2>Email Draft</h2>
          <span class="email-to">To: {{ sub.email }}</span>
        </div>
        <RichEditor
          v-model="emailBody"
          :readonly="sub.status === 'sent'"
        />
        <div v-if="sub.status !== 'sent'" class="action-row">
          <button class="btn btn-secondary" @click="regenerate" :disabled="regenerating || saving">
            {{ regenerating ? "Regenerating…" : "Regenerate Draft" }}
          </button>
          <button class="btn btn-secondary" @click="save" :disabled="saving">
            {{ saving ? "Saving…" : "Save Changes" }}
          </button>
          <button class="btn btn-lime" @click="send" :disabled="sending">
            {{ sending ? "Sending…" : "Send Email →" }}
          </button>
        </div>
        <div v-else class="sent-confirm">
          <span class="sent-check">✓</span> Email sent on {{ fmtDate(sub.sent_at) }}
        </div>
        <div v-if="actionMsg" :class="`alert alert-${actionMsgType}`" style="margin-top:0.75rem">{{ actionMsg }}</div>
      </div>

    </template>

    <!-- Custom Modal -->
    <div v-if="modalConfig.show" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <h3>{{ modalConfig.title }}</h3>
        <p>{{ modalConfig.message }}</p>
        <div class="modal-actions">
          <button class="btn btn-secondary" @click="closeModal">Cancel</button>
          <button class="btn btn-lime" @click="modalConfig.onConfirm">{{ modalConfig.confirmText }}</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import { getSubmission, saveEmail, sendEmail, regenerateEmail } from "../api";
import ScoreTable from "../components/ScoreTable.vue";
import RichEditor from "../components/RichEditor.vue";
import { normalizeEmailHtml } from "../utils/emailHtml.js";

const route         = useRoute();
const sub           = ref(null);
const loading       = ref(true);
const error         = ref("");
const emailBody     = ref("");
const saving        = ref(false);
const sending       = ref(false);
const regenerating  = ref(false);
const actionMsg     = ref("");
const actionMsgType = ref("success");
const isInitialLoad = ref(true);
let autoSaveTimeout = null;

const modalConfig = ref({
  show: false,
  title: "",
  message: "",
  confirmText: "",
  onConfirm: null
});

function openModal(title, message, confirmText, onConfirm) {
  modalConfig.value = { show: true, title, message, confirmText, onConfirm };
}

function closeModal() {
  modalConfig.value.show = false;
}

onMounted(async () => {
  try {
    sub.value       = await getSubmission(route.params.id);
    emailBody.value = normalizeEmailHtml(sub.value.email_body || "");
    // Prevent watcher from triggering on this initial data population
    setTimeout(() => { isInitialLoad.value = false; }, 100);
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
});

watch(emailBody, (newVal) => {
  if (isInitialLoad.value || !sub.value || sub.value.status === 'sent') return;

  saving.value = true;
  actionMsg.value = "";

  if (autoSaveTimeout) clearTimeout(autoSaveTimeout);
  
  autoSaveTimeout = setTimeout(async () => {
    try {
      await saveEmail(route.params.id, newVal);
      showMsg("success", "Auto-saved changes.");
    } catch (e) {
      showMsg("error", "Auto-save failed: " + e.message);
    } finally {
      saving.value = false;
    }
  }, 1500);
});

async function save() {
  saving.value    = true;
  actionMsg.value = "";
  try {
    await saveEmail(route.params.id, emailBody.value);
    showMsg("success", "Changes saved.");
  } catch (e) {
    showMsg("error", e.message);
  } finally {
    saving.value = false;
  }
}

function regenerate() {
  openModal(
    "Regenerate Draft?",
    "This will overwrite your current draft with the default system-generated text. This cannot be undone.",
    "Yes, Regenerate",
    confirmRegenerate
  );
}

async function confirmRegenerate() {
  closeModal();
  regenerating.value = true;
  actionMsg.value = "";
  try {
    const res = await regenerateEmail(route.params.id);
    isInitialLoad.value = true; // prevent autosave trigger on replacement
    emailBody.value = normalizeEmailHtml(res.email_body);
    setTimeout(() => { isInitialLoad.value = false; }, 100);
    showMsg("success", "Draft regenerated successfully.");
  } catch (e) {
    showMsg("error", e.message);
  } finally {
    regenerating.value = false;
  }
}

function send() {
  openModal(
    "Send Email?",
    "Send this email to the respondent? This cannot be undone.",
    "Yes, Send Email",
    confirmSend
  );
}

async function confirmSend() {
  closeModal();
  sending.value   = true;
  actionMsg.value = "";
  try {
    const res         = await sendEmail(route.params.id);
    sub.value.status  = "sent";
    sub.value.sent_at = res.sent_at;
    showMsg("success", `Email sent at ${fmtDate(res.sent_at)}.`);
  } catch (e) {
    showMsg("error", e.message);
  } finally {
    sending.value = false;
  }
}

function showMsg(type, msg) {
  actionMsgType.value = type;
  actionMsg.value     = msg;
}
function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-GB", { dateStyle: "short", timeStyle: "short" });
}
</script>

<style scoped>
.back-btn {
  display: inline-flex; align-items: center; gap: 0.4rem;
  background: none; border: none; cursor: pointer;
  color: #888; font-size: 0.875rem; font-weight: 500;
  padding: 0 0 1.25rem; transition: color 0.15s;
  font-family: 'Geist', monospace;
}
.back-btn:hover { color: var(--c-primary-dark); }

/* Card headings */
h2 {
  font-size: 1rem; font-weight: 700; color: var(--c-primary-dark);
  margin-bottom: 1.25rem; padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--c-bg);
  font-family: 'Playfair Display', serif;
}

/* Info grid */
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.info-item {
  border: 1.5px solid var(--c-primary-dark); border-radius: 12px;
  padding: 0.75rem 1rem; background: var(--c-white);
}
.info-item label {
  font-size: 0.65rem; font-weight: 700; color: #aaa;
  display: block; margin-bottom: 0.3rem;
  text-transform: uppercase; letter-spacing: 0.07em;
  font-family: 'Geist', monospace;
}
.info-item span {
  font-size: 0.92rem; font-weight: 500; color: var(--c-primary-dark);
  font-family: 'Geist', monospace;
}
.status-row { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; }
.sent-time { font-size: 0.78rem; color: #aaa; font-family: 'Geist', monospace; }

/* Email section */
.email-header { display: flex; align-items: baseline; justify-content: space-between; margin-bottom: 1.25rem; padding-bottom: 0.75rem; border-bottom: 1px solid var(--c-bg); }
.email-header h2 { margin: 0; padding: 0; border: none; }
.email-to { font-size: 0.8rem; color: #aaa; font-family: 'Geist', monospace; }

.email-editor {
  width: 100%; min-height: 380px; padding: 1rem;
  border: 2px solid var(--c-primary-dark); border-radius: 16px;
  font-family: 'Courier New', monospace; font-size: 0.83rem;
  line-height: 1.7; resize: vertical; background: var(--c-bg);
  color: var(--c-primary-dark); transition: all 0.15s;
}
.email-editor:focus { outline: none; background: var(--c-white); }
.email-editor[readonly] { opacity: 0.65; cursor: default; }

.action-row { display: flex; gap: 0.75rem; margin-top: 1rem; }

.sent-confirm {
  display: flex; align-items: center; gap: 0.5rem;
  margin-top: 1rem; font-size: 0.875rem; font-weight: 600; color: #3A7A00;
  font-family: 'Geist', monospace;
}
.sent-check {
  width: 24px; height: 24px; background: var(--c-accent); border-radius: 50%;
  display: inline-grid; place-items: center; font-size: 0.75rem; color: var(--c-primary-dark);
  border: 2px solid var(--c-primary-dark);
}

/* Custom Modal Styles */
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex; justify-content: center; align-items: center;
  z-index: 1000; backdrop-filter: blur(4px);
}
.modal-content {
  background: var(--c-white); border: 2px solid var(--c-primary-dark); border-radius: 16px;
  padding: 2rem; max-width: 450px; width: 90%;
  box-shadow: 0 10px 30px rgba(0,0,0,0.15);
  animation: modalIn 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.modal-content h3 {
  font-family: 'Playfair Display', serif; font-size: 1.25rem; font-weight: 700;
  color: var(--c-primary-dark); margin-bottom: 0.75rem;
}
.modal-content p {
  font-family: 'Geist', sans-serif; font-size: 0.95rem; color: #555;
  line-height: 1.5; margin-bottom: 1.5rem;
}
.modal-actions {
  display: flex; justify-content: flex-end; gap: 0.75rem;
}

@keyframes modalIn {
  from { opacity: 0; transform: translateY(10px) scale(0.98); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
</style>
