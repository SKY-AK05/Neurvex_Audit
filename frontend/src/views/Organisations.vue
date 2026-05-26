<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1>Organisations</h1>
        <p class="subtitle">Multi-respondent weighted scoring across all linked organisations.</p>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-state">Loading organisations…</div>

    <!-- Org list -->
    <div v-else>
      <div v-for="org in orgs" :key="org.id" class="org-card">
        <!-- Org header row -->
        <div class="org-header" @click="toggleOrg(org.id)">
          <div class="org-header-left">
            <span class="org-chevron">{{ expandedOrgs.has(org.id) ? '▾' : '▸' }}</span>
            <div>
              <span class="org-name">{{ org.name }}</span>
              <span class="org-meta">{{ org.respondent_count }} respondent{{ org.respondent_count !== 1 ? 's' : '' }}</span>
            </div>
          </div>
          <div class="org-header-right">
            <span v-if="org.org_avg !== null" class="org-score">{{ org.org_avg }}/20</span>
            <span v-if="org.org_level" :class="['level-badge', levelClass(org.org_level)]">{{ org.org_level }}</span>
            <span v-else class="org-score muted">No data</span>
            <button class="btn btn-primary btn-sm" @click.stop="openReportModal(org)" :disabled="!org.respondent_count">
              Send Org Report
            </button>
          </div>
        </div>

        <!-- Expanded respondents -->
        <div v-if="expandedOrgs.has(org.id)" class="org-detail">
          <div v-if="loadingDetail[org.id]" class="detail-loading">Loading…</div>
          <div v-else-if="orgDetails[org.id]">
            <!-- Live weighted avg bar -->
            <div class="live-avg-bar">
              <span class="live-avg-label">Weighted Avg</span>
              <span class="live-avg-value">{{ liveScores[org.id]?.org_avg ?? org.org_avg }}/20</span>
              <span :class="['level-badge', levelClass(liveScores[org.id]?.org_level ?? org.org_level)]">
                {{ liveScores[org.id]?.org_level ?? org.org_level }}
              </span>
            </div>

            <!-- Respondent table -->
            <table class="respondent-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Role</th>
                  <th>Score</th>
                  <th>Weight</th>
                  <th>Email</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in orgDetails[org.id].respondents" :key="r.id">
                  <td class="font-medium">{{ r.name }}</td>
                  <td class="text-muted">{{ r.designation }}</td>
                  <td class="score-cell">{{ r.overall_avg }}/20</td>
                  <td>
                    <select
                      :value="r.weight"
                      @change="updateWeight(org.id, r.id, $event.target.value)"
                      class="weight-select"
                    >
                      <option value="0.5">0.5×</option>
                      <option value="1">1×</option>
                      <option value="2">2×</option>
                      <option value="3">3×</option>
                    </select>
                  </td>
                  <td class="text-muted">{{ r.email }}</td>
                  <td>
                    <button class="btn-icon" title="Send message" @click="openMessageModal(org, r)">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,12 2,6"/></svg>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- Unlinked submissions -->
      <div class="org-card unlinked-card">
        <div class="org-header" @click="toggleUnlinked">
          <div class="org-header-left">
            <span class="org-chevron">{{ showUnlinked ? '▾' : '▸' }}</span>
            <div>
              <span class="org-name muted">Unlinked Submissions</span>
              <span class="org-meta">{{ unlinked.length }} submission{{ unlinked.length !== 1 ? 's' : '' }} not linked to any org</span>
            </div>
          </div>
        </div>

        <div v-if="showUnlinked" class="org-detail">
          <div v-if="loadingUnlinked" class="detail-loading">Loading…</div>
          <div v-else-if="unlinked.length === 0" class="empty-state">All submissions are linked.</div>
          <table v-else class="respondent-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Organisation</th>
                <th>Score</th>
                <th>Submitted</th>
                <th>Link to Org</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in unlinked" :key="s.id">
                <td class="font-medium">{{ s.name }}</td>
                <td class="text-muted">{{ s.company_name }}</td>
                <td class="score-cell">{{ s.overall_avg }}/20</td>
                <td class="text-muted">{{ formatDate(s.submitted_at) }}</td>
                <td>
                  <div class="link-row">
                    <select v-model="linkTargets[s.id]" class="org-select">
                      <option value="">— select org —</option>
                      <option v-for="o in orgs" :key="o.id" :value="o.id">{{ o.name }}</option>
                    </select>
                    <button
                      class="btn btn-primary btn-sm"
                      :disabled="!linkTargets[s.id]"
                      @click="linkSubmission(s.id, linkTargets[s.id])"
                    >Link</button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Send Org Report Modal -->
    <div v-if="reportModal.open" class="modal-overlay" @click.self="reportModal.open = false">
      <div class="modal-card">
        <h3>Send Org Report — {{ reportModal.org?.name }}</h3>
        <p class="modal-sub">Select recipients and confirm. Each will receive the full weighted summary.</p>

        <div class="recipient-list">
          <label class="check-all">
            <input type="checkbox" :checked="allRecipientsChecked" @change="toggleAllRecipients" />
            Select all
          </label>
          <label v-for="r in reportModal.respondents" :key="r.id" class="recipient-row">
            <input type="checkbox" :value="r" v-model="reportModal.selected" />
            <span>{{ r.name }} <span class="text-muted">— {{ r.email }}</span></span>
          </label>
        </div>

        <div class="field" style="margin-top:1rem;">
          <label>Subject</label>
          <input v-model="reportModal.subject" type="text" />
        </div>

        <div v-if="reportModal.error" class="error-msg">{{ reportModal.error }}</div>

        <div class="modal-actions">
          <button class="btn btn-secondary" @click="reportModal.open = false">Cancel</button>
          <button
            class="btn btn-primary"
            :disabled="!reportModal.selected.length || reportModal.sending"
            @click="sendOrgReport"
          >
            {{ reportModal.sending ? 'Sending…' : `Send to ${reportModal.selected.length} recipient${reportModal.selected.length !== 1 ? 's' : ''}` }}
          </button>
        </div>
      </div>
    </div>

    <!-- Send Message Modal -->
    <div v-if="msgModal.open" class="modal-overlay" @click.self="msgModal.open = false">
      <div class="modal-card">
        <h3>Message — {{ msgModal.recipient?.name }}</h3>
        <p class="modal-sub text-muted">{{ msgModal.recipient?.email }}</p>

        <div class="field">
          <label>Subject</label>
          <input v-model="msgModal.subject" type="text" placeholder="Subject…" />
        </div>
        <div class="field">
          <label>Message</label>
          <textarea v-model="msgModal.body" rows="5" placeholder="Write your message…"></textarea>
        </div>

        <div v-if="msgModal.error" class="error-msg">{{ msgModal.error }}</div>
        <div v-if="msgModal.success" class="success-msg">{{ msgModal.success }}</div>

        <div class="modal-actions">
          <button class="btn btn-secondary" @click="msgModal.open = false">Cancel</button>
          <button
            class="btn btn-primary"
            :disabled="!msgModal.subject || !msgModal.body || msgModal.sending"
            @click="sendMessage"
          >{{ msgModal.sending ? 'Sending…' : 'Send Message' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

function getAuthHeaders() {
  const token = sessionStorage.getItem('nd_auth_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ── State ──────────────────────────────────────────────────────────────────
const loading        = ref(true);
const orgs           = ref([]);
const expandedOrgs   = reactive(new Set());
const orgDetails     = reactive({});
const loadingDetail  = reactive({});
const liveScores     = reactive({});   // org_id → {org_avg, org_level}

const showUnlinked    = ref(false);
const loadingUnlinked = ref(false);
const unlinked        = ref([]);
const linkTargets     = reactive({});  // submission_id → org_id

// ── Modals ─────────────────────────────────────────────────────────────────
const reportModal = reactive({
  open: false, org: null, respondents: [], selected: [], subject: '', sending: false, error: '',
});
const msgModal = reactive({
  open: false, org: null, recipient: null, subject: '', body: '', sending: false, error: '', success: '',
});

// ── Fetch ──────────────────────────────────────────────────────────────────
async function fetchOrgs() {
  loading.value = true;
  try {
    const res = await fetch(`${API_BASE}/manage/orgs`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to load organisations');
    orgs.value = await res.json();
  } catch (e) {
    console.error(e);
  } finally {
    loading.value = false;
  }
}

async function fetchOrgDetail(orgId) {
  loadingDetail[orgId] = true;
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/${orgId}`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to load org detail');
    const data = await res.json();
    orgDetails[orgId] = data;
    liveScores[orgId] = data.scores;
  } catch (e) {
    console.error(e);
  } finally {
    loadingDetail[orgId] = false;
  }
}

async function fetchUnlinked() {
  loadingUnlinked.value = true;
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/unlinked`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to load unlinked');
    unlinked.value = await res.json();
  } catch (e) {
    console.error(e);
  } finally {
    loadingUnlinked.value = false;
  }
}

// ── Interactions ───────────────────────────────────────────────────────────
function toggleOrg(orgId) {
  if (expandedOrgs.has(orgId)) {
    expandedOrgs.delete(orgId);
  } else {
    expandedOrgs.add(orgId);
    if (!orgDetails[orgId]) fetchOrgDetail(orgId);
  }
}

function toggleUnlinked() {
  showUnlinked.value = !showUnlinked.value;
  if (showUnlinked.value && !unlinked.value.length) fetchUnlinked();
}

async function updateWeight(orgId, submissionId, weight) {
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/${orgId}/links/${submissionId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({ weight: parseFloat(weight) }),
    });
    if (!res.ok) throw new Error('Failed to update weight');
    const data = await res.json();
    // Update live scores
    liveScores[orgId] = data.scores;
    // Update the respondent's weight in the detail
    const detail = orgDetails[orgId];
    if (detail) {
      const r = detail.respondents.find(r => r.id === submissionId);
      if (r) r.weight = parseFloat(weight);
    }
    // Update summary row
    const org = orgs.value.find(o => o.id === orgId);
    if (org && data.scores) {
      org.org_avg   = data.scores.org_avg;
      org.org_level = data.scores.org_level;
    }
  } catch (e) {
    console.error(e);
  }
}

async function linkSubmission(submissionId, orgId) {
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/${orgId}/link`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({ submission_id: submissionId }),
    });
    if (!res.ok) throw new Error('Failed to link submission');
    // Refresh
    await fetchOrgs();
    await fetchUnlinked();
    if (expandedOrgs.has(orgId)) await fetchOrgDetail(orgId);
  } catch (e) {
    console.error(e);
  }
}

// ── Report modal ───────────────────────────────────────────────────────────
function openReportModal(org) {
  const detail = orgDetails[org.id];
  const respondents = detail?.respondents ?? [];
  reportModal.org        = org;
  reportModal.respondents = respondents;
  reportModal.selected   = [...respondents];
  reportModal.subject    = `${org.name} — NeuroMark Audit Organisation Summary`;
  reportModal.error      = '';
  reportModal.sending    = false;
  reportModal.open       = true;

  // Ensure detail is loaded
  if (!detail) fetchOrgDetail(org.id).then(() => {
    reportModal.respondents = orgDetails[org.id]?.respondents ?? [];
    reportModal.selected    = [...reportModal.respondents];
  });
}

const allRecipientsChecked = computed(() =>
  reportModal.respondents.length > 0 &&
  reportModal.selected.length === reportModal.respondents.length
);

function toggleAllRecipients(e) {
  reportModal.selected = e.target.checked ? [...reportModal.respondents] : [];
}

async function sendOrgReport() {
  reportModal.sending = true;
  reportModal.error   = '';
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/${reportModal.org.id}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({
        subject:       reportModal.subject,
        body:          '',
        recipients:    reportModal.selected.map(r => ({ email: r.email, name: r.name })),
        is_org_report: true,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to send');
    reportModal.open = false;
  } catch (e) {
    reportModal.error = e.message;
  } finally {
    reportModal.sending = false;
  }
}

// ── Message modal ──────────────────────────────────────────────────────────
function openMessageModal(org, recipient) {
  msgModal.org       = org;
  msgModal.recipient = recipient;
  msgModal.subject   = '';
  msgModal.body      = '';
  msgModal.error     = '';
  msgModal.success   = '';
  msgModal.sending   = false;
  msgModal.open      = true;
}

async function sendMessage() {
  msgModal.sending = true;
  msgModal.error   = '';
  msgModal.success = '';
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/${msgModal.org.id}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({
        subject:       msgModal.subject,
        body:          msgModal.body,
        recipients:    [{ email: msgModal.recipient.email, name: msgModal.recipient.name }],
        is_org_report: false,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to send');
    msgModal.success = 'Message sent successfully.';
    setTimeout(() => { msgModal.open = false; }, 1500);
  } catch (e) {
    msgModal.error = e.message;
  } finally {
    msgModal.sending = false;
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function levelClass(level) {
  if (!level) return '';
  if (level.includes('1')) return 'level-1';
  if (level.includes('2')) return 'level-2';
  return 'level-3';
}

function formatDate(d) {
  if (!d) return '—';
  return new Date(d).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

onMounted(fetchOrgs);
</script>

<style scoped>
.loading-state { padding: 3rem; text-align: center; color: #aaa; }

.org-card {
  background: #fff;
  border: 2px solid var(--c-primary-dark);
  border-radius: 12px;
  margin-bottom: 1rem;
  overflow: hidden;
}
.unlinked-card { border-color: #E2DDD4; }

.org-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 1rem 1.5rem;
  cursor: pointer;
  user-select: none;
  transition: background 0.1s;
}
.org-header:hover { background: #FAFAF8; }

.org-header-left { display: flex; align-items: center; gap: 0.75rem; }
.org-chevron { font-size: 0.9rem; color: #aaa; width: 16px; }
.org-name { font-weight: 700; font-size: 1rem; color: var(--c-primary-dark); margin-right: 0.75rem; }
.org-name.muted { color: #aaa; }
.org-meta { font-size: 0.8rem; color: #aaa; }

.org-header-right { display: flex; align-items: center; gap: 0.75rem; }
.org-score { font-size: 1.1rem; font-weight: 800; color: var(--c-primary-dark); }
.org-score.muted { color: #ccc; font-size: 0.9rem; }

.level-badge {
  font-size: 0.72rem; font-weight: 700; padding: 0.2rem 0.6rem;
  border-radius: 99px; text-transform: uppercase; letter-spacing: 0.04em;
}
.level-1 { background: #FEE2E2; color: #B91C1C; }
.level-2 { background: #FEF3C7; color: #92400E; }
.level-3 { background: #D1FAE5; color: #065F46; }

.org-detail { border-top: 1px solid #E2DDD4; padding: 1.25rem 1.5rem; }
.detail-loading { color: #aaa; font-size: 0.9rem; }

.live-avg-bar {
  display: flex; align-items: center; gap: 0.75rem;
  margin-bottom: 1rem; padding: 0.75rem 1rem;
  background: #F5F2EB; border-radius: 8px;
}
.live-avg-label { font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #aaa; }
.live-avg-value { font-size: 1.1rem; font-weight: 800; color: var(--c-primary-dark); }

.respondent-table {
  width: 100%; border-collapse: separate; border-spacing: 0;
}
.respondent-table th {
  text-align: left; padding: 0.6rem 0.75rem;
  font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em;
  color: #aaa; border-bottom: 2px solid #E2DDD4;
}
.respondent-table td {
  padding: 0.85rem 0.75rem; border-bottom: 1px solid #E2DDD4; vertical-align: middle;
}
.score-cell { font-weight: 700; color: var(--c-primary-dark); }
.font-medium { font-weight: 600; }
.text-muted { color: #888; font-size: 0.88rem; }

.weight-select {
  padding: 0.3rem 0.5rem; border: 2px solid #E2DDD4; border-radius: 6px;
  font-size: 0.85rem; font-weight: 700; cursor: pointer; background: #fff;
  color: var(--c-primary-dark);
}
.weight-select:focus { outline: none; border-color: var(--c-primary-dark); }

.btn-icon {
  background: none; border: none; cursor: pointer; padding: 0.4rem;
  border-radius: 6px; color: #888; transition: all 0.15s;
}
.btn-icon:hover { background: #F0F0F0; color: var(--c-primary-dark); }

.btn-sm { padding: 0.35rem 0.85rem; font-size: 0.8rem; }

/* Unlinked */
.link-row { display: flex; align-items: center; gap: 0.5rem; }
.org-select {
  padding: 0.3rem 0.5rem; border: 2px solid #E2DDD4; border-radius: 6px;
  font-size: 0.82rem; min-width: 160px;
}
.empty-state { color: #aaa; font-size: 0.9rem; padding: 0.5rem 0; }

/* Modals */
.modal-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.5);
  display: flex; align-items: center; justify-content: center; z-index: 1000;
}
.modal-card {
  background: #fff; border: 2px solid var(--c-primary-dark);
  border-radius: 16px; padding: 2rem; width: 480px; max-width: 95vw;
  box-shadow: 6px 6px 0 var(--c-primary-dark);
  max-height: 85vh; overflow-y: auto;
}
.modal-card h3 { font-family: 'Playfair Display', serif; font-size: 1.2rem; margin-bottom: 0.25rem; }
.modal-sub { font-size: 0.85rem; color: #888; margin-bottom: 1.25rem; }
.modal-actions { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; }

.recipient-list { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 0.5rem; }
.check-all { font-weight: 700; font-size: 0.85rem; display: flex; align-items: center; gap: 0.5rem; cursor: pointer; }
.recipient-row { display: flex; align-items: center; gap: 0.5rem; font-size: 0.88rem; cursor: pointer; }

.field { display: flex; flex-direction: column; gap: 0.35rem; margin-bottom: 0.75rem; }
.field label { font-size: 0.82rem; font-weight: 700; color: var(--c-primary-dark); }
.field input, .field textarea {
  padding: 0.6rem 0.75rem; border: 2px solid #E2DDD4; border-radius: 8px;
  font-family: inherit; font-size: 0.9rem; resize: vertical;
}
.field input:focus, .field textarea:focus { outline: none; border-color: var(--c-primary-dark); }

.error-msg { color: #EF4444; font-size: 0.85rem; margin-top: 0.5rem; }
.success-msg { color: #10B981; font-size: 0.85rem; margin-top: 0.5rem; }
</style>
