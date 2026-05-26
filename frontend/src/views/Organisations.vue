<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1>Organisations</h1>
        <p class="subtitle">Multi-respondent weighted scoring across all linked organisations.</p>
      </div>
    </div>

    <div v-if="loading" class="loading-state">Loading organisations…</div>

    <div v-else>
      <div v-for="org in orgs" :key="org.id" class="org-card">

        <!-- ── Org header row ── -->
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
            <button
              class="btn btn-primary btn-sm"
              @click.stop="toggleReport(org)"
              :disabled="!org.respondent_count"
            >
              {{ reportOpenFor === org.id ? 'Close Report ✕' : 'Send Org Report' }}
            </button>
          </div>
        </div>

        <!-- ── Respondents (expanded) ── -->
        <div v-if="expandedOrgs.has(org.id)" class="org-detail">
          <div v-if="loadingDetail[org.id]" class="detail-loading">Loading…</div>
          <div v-else-if="orgDetails[org.id]">
            <div class="live-avg-bar">
              <span class="live-avg-label">Weighted Avg</span>
              <span class="live-avg-value">{{ liveScores[org.id]?.org_avg ?? org.org_avg }}/20</span>
              <span :class="['level-badge', levelClass(liveScores[org.id]?.org_level ?? org.org_level)]">
                {{ liveScores[org.id]?.org_level ?? org.org_level }}
              </span>
            </div>

            <table class="respondent-table">
              <thead>
                <tr>
                  <th>Name</th><th>Role</th><th>Score</th><th>Weight</th><th>Email</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in orgDetails[org.id].respondents" :key="r.id">
                  <td class="font-medium">{{ r.name }}</td>
                  <td class="text-muted">{{ r.designation }}</td>
                  <td class="score-cell">{{ r.overall_avg }}/20</td>
                  <td>
                    <select :value="r.weight" @change="updateWeight(org.id, r.id, $event.target.value)" class="weight-select">
                      <option value="0.5">0.5×</option>
                      <option value="1">1×</option>
                      <option value="2">2×</option>
                      <option value="3">3×</option>
                    </select>
                  </td>
                  <td class="text-muted">{{ r.email }}</td>
                  <td>
                    <button class="btn-icon" title="Send message" @click="openMsgPanel(org, r)">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                        <polyline points="22,6 12,12 2,6"/>
                      </svg>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- ── Send Org Report panel (inline, below respondents) ── -->
        <div v-if="reportOpenFor === org.id" class="inline-panel">
          <div class="inline-panel-header">
            <span class="inline-panel-title">Send Org Report</span>
            <button class="btn-icon" @click="reportOpenFor = null">✕</button>
          </div>

          <div class="inline-panel-body">
            <!-- Left col: recipients + subject + actions -->
            <div class="inline-panel-left">
              <p class="field-label">Recipients</p>
              <div class="recipient-list">
                <label class="check-all">
                  <input type="checkbox" :checked="allRecipientsChecked" @change="toggleAllRecipients" />
                  Select all
                </label>
                <label v-for="r in report.respondents" :key="r.id" class="recipient-row">
                  <input type="checkbox" :value="r" v-model="report.selected" />
                  <span>{{ r.name }} <span class="text-muted">— {{ r.email }}</span></span>
                </label>
              </div>

              <div class="field" style="margin-top:1rem;">
                <label>Subject</label>
                <input v-model="report.subject" type="text" />
              </div>

              <div v-if="report.error"   class="error-msg">{{ report.error }}</div>
              <div v-if="report.success" class="success-msg">{{ report.success }}</div>

              <div class="panel-actions">
                <button
                  class="btn btn-primary"
                  :disabled="!report.selected.length || report.sending"
                  @click="sendOrgReport(org)"
                >
                  {{ report.sending
                    ? 'Sending…'
                    : `Send to ${report.selected.length} recipient${report.selected.length !== 1 ? 's' : ''}` }}
                </button>
              </div>
            </div>

            <!-- Right col: email preview -->
            <div class="inline-panel-right">
              <p class="field-label">Email Preview</p>
              <div v-if="report.loadingPreview" class="preview-loading">Loading preview…</div>
              <div v-else-if="report.previewHtml" class="email-preview-frame">
                <iframe :srcdoc="report.previewHtml" sandbox="allow-same-origin" class="email-iframe"></iframe>
              </div>
              <div v-else class="preview-empty">No preview available.</div>
            </div>
          </div>
        </div>

        <!-- ── Send Message panel (inline, per respondent) ── -->
        <div v-if="msgPanel.orgId === org.id && msgPanel.open" class="inline-panel inline-panel--msg">
          <div class="inline-panel-header">
            <span class="inline-panel-title">Message — {{ msgPanel.recipient?.name }}</span>
            <span class="text-muted" style="font-size:0.82rem;">{{ msgPanel.recipient?.email }}</span>
            <button class="btn-icon" @click="msgPanel.open = false">✕</button>
          </div>
          <div class="msg-panel-body">
            <div class="field">
              <label>Subject</label>
              <input v-model="msgPanel.subject" type="text" placeholder="Subject…" />
            </div>
            <div class="field">
              <label>Message</label>
              <textarea v-model="msgPanel.body" rows="4" placeholder="Write your message…"></textarea>
            </div>
            <div v-if="msgPanel.error"   class="error-msg">{{ msgPanel.error }}</div>
            <div v-if="msgPanel.success" class="success-msg">{{ msgPanel.success }}</div>
            <div class="panel-actions">
              <button class="btn btn-secondary btn-sm" @click="msgPanel.open = false">Cancel</button>
              <button
                class="btn btn-primary btn-sm"
                :disabled="!msgPanel.subject || !msgPanel.body || msgPanel.sending"
                @click="sendMessage(org)"
              >{{ msgPanel.sending ? 'Sending…' : 'Send Message' }}</button>
            </div>
          </div>
        </div>

      </div><!-- end org loop -->

      <!-- ── Unlinked submissions ── -->
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
              <tr><th>Name</th><th>Organisation</th><th>Score</th><th>Submitted</th><th>Link to Org</th></tr>
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
                    <button class="btn btn-primary btn-sm" :disabled="!linkTargets[s.id]" @click="linkSubmission(s.id, linkTargets[s.id])">
                      Link
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
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
const loading       = ref(true);
const orgs          = ref([]);
const expandedOrgs  = reactive(new Set());
const orgDetails    = reactive({});
const loadingDetail = reactive({});
const liveScores    = reactive({});

const showUnlinked    = ref(false);
const loadingUnlinked = ref(false);
const unlinked        = ref([]);
const linkTargets     = reactive({});

// Which org has the report panel open (only one at a time)
const reportOpenFor = ref(null);

// Report panel state
const report = reactive({
  respondents: [], selected: [], subject: '',
  sending: false, error: '', success: '',
  previewHtml: '', loadingPreview: false,
});

// Message panel state
const msgPanel = reactive({
  open: false, orgId: null, recipient: null,
  subject: '', body: '', sending: false, error: '', success: '',
});

// ── Fetch ──────────────────────────────────────────────────────────────────
async function fetchOrgs() {
  loading.value = true;
  try {
    const res = await fetch(`${API_BASE}/manage/orgs`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to load organisations');
    orgs.value = await res.json();
  } catch (e) { console.error(e); }
  finally { loading.value = false; }
}

async function fetchOrgDetail(orgId) {
  loadingDetail[orgId] = true;
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/${orgId}`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to load org detail');
    const data = await res.json();
    orgDetails[orgId] = data;
    liveScores[orgId] = data.scores;
  } catch (e) { console.error(e); }
  finally { loadingDetail[orgId] = false; }
}

async function fetchUnlinked() {
  loadingUnlinked.value = true;
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/unlinked`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed to load unlinked');
    unlinked.value = await res.json();
  } catch (e) { console.error(e); }
  finally { loadingUnlinked.value = false; }
}

async function fetchReportPreview(orgId) {
  report.loadingPreview = true;
  report.previewHtml    = '';
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/${orgId}/report-preview`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Preview failed');
    const data = await res.json();
    report.previewHtml = data.html;
  } catch (e) { console.error(e); }
  finally { report.loadingPreview = false; }
}

// ── Interactions ───────────────────────────────────────────────────────────
function toggleOrg(orgId) {
  if (expandedOrgs.has(orgId)) { expandedOrgs.delete(orgId); }
  else {
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
    liveScores[orgId] = data.scores;
    const detail = orgDetails[orgId];
    if (detail) { const r = detail.respondents.find(r => r.id === submissionId); if (r) r.weight = parseFloat(weight); }
    const org = orgs.value.find(o => o.id === orgId);
    if (org && data.scores) { org.org_avg = data.scores.org_avg; org.org_level = data.scores.org_level; }
  } catch (e) { console.error(e); }
}

async function linkSubmission(submissionId, orgId) {
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/${orgId}/link`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({ submission_id: submissionId }),
    });
    if (!res.ok) throw new Error('Failed to link submission');
    await fetchOrgs();
    await fetchUnlinked();
    if (expandedOrgs.has(orgId)) await fetchOrgDetail(orgId);
  } catch (e) { console.error(e); }
}

// ── Report panel ───────────────────────────────────────────────────────────
async function toggleReport(org) {
  if (reportOpenFor.value === org.id) { reportOpenFor.value = null; return; }

  reportOpenFor.value   = org.id;
  report.error          = '';
  report.success        = '';
  report.sending        = false;
  report.previewHtml    = '';

  // Ensure detail loaded first, then populate recipients
  if (!orgDetails[org.id]) await fetchOrgDetail(org.id);
  const respondents = orgDetails[org.id]?.respondents ?? [];
  report.respondents = respondents;
  report.selected    = [...respondents];
  report.subject     = `${org.name} — NeuroMark Audit Organisation Summary`;

  fetchReportPreview(org.id);
}

const allRecipientsChecked = computed(() =>
  report.respondents.length > 0 && report.selected.length === report.respondents.length
);
function toggleAllRecipients(e) {
  report.selected = e.target.checked ? [...report.respondents] : [];
}

async function sendOrgReport(org) {
  report.sending = true;
  report.error   = '';
  report.success = '';
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/${org.id}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({
        subject:       report.subject,
        body:          '',
        recipients:    report.selected.map(r => ({ email: r.email, name: r.name })),
        is_org_report: true,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to send');
    report.success = `Sent to ${report.selected.length} recipient${report.selected.length !== 1 ? 's' : ''}.`;
    setTimeout(() => { reportOpenFor.value = null; }, 1800);
  } catch (e) {
    report.error = e.message;
  } finally {
    report.sending = false;
  }
}

// ── Message panel ──────────────────────────────────────────────────────────
function openMsgPanel(org, recipient) {
  msgPanel.orgId     = org.id;
  msgPanel.recipient = recipient;
  msgPanel.subject   = '';
  msgPanel.body      = '';
  msgPanel.error     = '';
  msgPanel.success   = '';
  msgPanel.sending   = false;
  msgPanel.open      = true;
}

async function sendMessage(org) {
  msgPanel.sending = true;
  msgPanel.error   = '';
  msgPanel.success = '';
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/${org.id}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({
        subject:       msgPanel.subject,
        body:          msgPanel.body,
        recipients:    [{ email: msgPanel.recipient.email, name: msgPanel.recipient.name }],
        is_org_report: false,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to send');
    msgPanel.success = 'Message sent.';
    setTimeout(() => { msgPanel.open = false; }, 1500);
  } catch (e) {
    msgPanel.error = e.message;
  } finally {
    msgPanel.sending = false;
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

/* ── Org card ── */
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
  padding: 1rem 1.5rem; cursor: pointer; user-select: none; transition: background 0.1s;
}
.org-header:hover { background: #FAFAF8; }
.org-header-left  { display: flex; align-items: center; gap: 0.75rem; }
.org-header-right { display: flex; align-items: center; gap: 0.75rem; }
.org-chevron { font-size: 0.9rem; color: #aaa; width: 16px; }
.org-name { font-weight: 700; font-size: 1rem; color: var(--c-primary-dark); margin-right: 0.75rem; }
.org-name.muted { color: #aaa; }
.org-meta  { font-size: 0.8rem; color: #aaa; }
.org-score { font-size: 1.1rem; font-weight: 800; color: var(--c-primary-dark); }
.org-score.muted { color: #ccc; font-size: 0.9rem; }

.level-badge {
  font-size: 0.72rem; font-weight: 700; padding: 0.2rem 0.6rem;
  border-radius: 99px; text-transform: uppercase; letter-spacing: 0.04em;
}
.level-1 { background: #FEE2E2; color: #B91C1C; }
.level-2 { background: #FEF3C7; color: #92400E; }
.level-3 { background: #D1FAE5; color: #065F46; }

/* ── Respondent detail ── */
.org-detail { border-top: 1px solid #E2DDD4; padding: 1.25rem 1.5rem; }
.detail-loading { color: #aaa; font-size: 0.9rem; }

.live-avg-bar {
  display: flex; align-items: center; gap: 0.75rem;
  margin-bottom: 1rem; padding: 0.75rem 1rem;
  background: #F5F2EB; border-radius: 8px;
}
.live-avg-label { font-size: 0.78rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; color: #aaa; }
.live-avg-value { font-size: 1.1rem; font-weight: 800; color: var(--c-primary-dark); }

.respondent-table { width: 100%; border-collapse: separate; border-spacing: 0; }
.respondent-table th {
  text-align: left; padding: 0.6rem 0.75rem;
  font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em;
  color: #aaa; border-bottom: 2px solid #E2DDD4;
}
.respondent-table td { padding: 0.85rem 0.75rem; border-bottom: 1px solid #E2DDD4; vertical-align: middle; }
.score-cell  { font-weight: 700; color: var(--c-primary-dark); }
.font-medium { font-weight: 600; }
.text-muted  { color: #888; font-size: 0.88rem; }

.weight-select {
  padding: 0.3rem 0.5rem; border: 2px solid #E2DDD4; border-radius: 6px;
  font-size: 0.85rem; font-weight: 700; cursor: pointer; background: #fff; color: var(--c-primary-dark);
}
.weight-select:focus { outline: none; border-color: var(--c-primary-dark); }

.btn-icon {
  background: none; border: none; cursor: pointer; padding: 0.4rem;
  border-radius: 6px; color: #888; transition: all 0.15s;
}
.btn-icon:hover { background: #F0F0F0; color: var(--c-primary-dark); }
.btn-sm { padding: 0.35rem 0.85rem; font-size: 0.8rem; }

/* ── Inline panels ── */
.inline-panel {
  border-top: 2px solid var(--c-primary-dark);
  background: #FAFAF8;
  padding: 1.5rem;
}
.inline-panel--msg { background: #fff; }

.inline-panel-header {
  display: flex; align-items: center; gap: 1rem; margin-bottom: 1.25rem;
}
.inline-panel-title {
  font-family: 'Playfair Display', serif;
  font-size: 1rem; font-weight: 700; color: var(--c-primary-dark);
  flex: 1;
}

/* Report panel: two columns */
.inline-panel-body {
  display: flex; gap: 1.5rem; align-items: flex-start;
}
.inline-panel-left  { flex: 0 0 260px; display: flex; flex-direction: column; }
.inline-panel-right { flex: 1; min-width: 0; }

.field-label {
  font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.06em; color: #aaa; margin-bottom: 0.5rem;
}

.recipient-list { display: flex; flex-direction: column; gap: 0.4rem; }
.check-all { font-weight: 700; font-size: 0.82rem; display: flex; align-items: center; gap: 0.5rem; cursor: pointer; }
.recipient-row { display: flex; align-items: center; gap: 0.5rem; font-size: 0.85rem; cursor: pointer; }

.field { display: flex; flex-direction: column; gap: 0.3rem; margin-bottom: 0.75rem; }
.field label { font-size: 0.78rem; font-weight: 700; color: var(--c-primary-dark); }
.field input, .field textarea {
  padding: 0.55rem 0.75rem; border: 2px solid #E2DDD4; border-radius: 8px;
  font-family: inherit; font-size: 0.88rem; resize: vertical; background: #fff;
}
.field input:focus, .field textarea:focus { outline: none; border-color: var(--c-primary-dark); }

.panel-actions { display: flex; gap: 0.5rem; margin-top: 1rem; justify-content: flex-start; }

/* Message panel body */
.msg-panel-body { max-width: 520px; }

/* Email preview */
.preview-loading { color: #aaa; font-size: 0.88rem; padding: 1rem 0; }
.preview-empty   { color: #ccc; font-size: 0.88rem; padding: 1rem 0; }
.email-preview-frame {
  border: 2px solid #E2DDD4; border-radius: 8px; overflow: hidden; height: 520px;
}
.email-iframe { width: 100%; height: 100%; border: none; display: block; }

/* Unlinked */
.link-row { display: flex; align-items: center; gap: 0.5rem; }
.org-select { padding: 0.3rem 0.5rem; border: 2px solid #E2DDD4; border-radius: 6px; font-size: 0.82rem; min-width: 160px; }
.empty-state { color: #aaa; font-size: 0.9rem; padding: 0.5rem 0; }

.error-msg   { color: #EF4444; font-size: 0.82rem; margin-top: 0.4rem; }
.success-msg { color: #10B981; font-size: 0.82rem; margin-top: 0.4rem; }
</style>
