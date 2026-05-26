<template>
  <div class="orgs-shell">

    <!-- ── Left: org list ── -->
    <aside class="org-list">
      <div class="org-list-header">
        <h2>Organisations</h2>
        <p class="org-list-sub">{{ orgs.length }} total</p>
      </div>

      <div v-if="loading" class="list-loading">Loading…</div>

      <div v-else class="org-list-items">
        <button
          v-for="org in orgs"
          :key="org.id"
          :class="['org-list-item', { active: selectedOrg?.id === org.id, virtual: org.is_virtual }]"
          @click="selectOrg(org)"
        >
          <div class="oli-top">
            <span class="oli-name">{{ org.name }}</span>
            <span v-if="org.is_virtual" class="virtual-badge">unlinked</span>
          </div>
          <div class="oli-bottom">
            <span class="oli-score">{{ org.org_avg != null ? org.org_avg + '/20' : '—' }}</span>
            <span v-if="org.org_level" :class="['level-badge', levelClass(org.org_level)]">
              {{ shortLevel(org.org_level) }}
            </span>
            <span class="oli-count">{{ org.respondent_count }} resp.</span>
          </div>
        </button>
      </div>
    </aside>

    <!-- ── Right: detail panel ── -->
    <main class="org-detail-panel">

      <!-- Empty state -->
      <div v-if="!selectedOrg" class="detail-empty">
        <p>Select an organisation from the list to view details.</p>
      </div>

      <div v-else class="detail-content">

        <!-- Detail header -->
        <div class="detail-header">
          <div class="detail-header-left">
            <h2 class="detail-org-name">{{ selectedOrg.name }}</h2>
            <div class="detail-meta">
              <span v-if="selectedOrg.org_avg != null" class="detail-score">
                {{ liveScore?.org_avg ?? selectedOrg.org_avg }}/20
              </span>
              <span v-if="liveScore?.org_level || selectedOrg.org_level"
                :class="['level-badge', levelClass(liveScore?.org_level ?? selectedOrg.org_level)]">
                {{ liveScore?.org_level ?? selectedOrg.org_level }}
              </span>
              <span class="detail-count">{{ selectedOrg.respondent_count }} respondents</span>
            </div>
          </div>
          <div class="detail-header-right">
            <button v-if="selectedOrg.is_virtual"
              class="btn btn-secondary"
              @click="createOrg(selectedOrg)"
            >Create Org &amp; Link All</button>
            <button v-else
              class="btn btn-primary"
              :disabled="!selectedOrg.respondent_count"
              @click="reportOpen = !reportOpen"
            >{{ reportOpen ? 'Close Report ✕' : 'Send Org Report' }}</button>
          </div>
        </div>

        <!-- Loading detail -->
        <div v-if="loadingDetail" class="detail-loading">Loading respondents…</div>

        <template v-else-if="detail">

          <!-- Respondents table -->
          <div class="detail-section">
            <table class="respondent-table">
              <thead>
                <tr>
                  <th>Name</th><th>Role</th><th>Score</th>
                  <th v-if="!selectedOrg.is_virtual">Weight</th>
                  <th>Email</th>
                  <th v-if="!selectedOrg.is_virtual">Actions</th>
                </tr>
              </thead>
              <tbody>
                <template v-for="r in detail.respondents" :key="r.id">
                  <tr class="respondent-row" :class="{ 'expanded': expandedRespondentId === r.id }" @click="toggleRespondent(r.id)">
                    <td class="font-medium">
                      <span class="chevron" :class="{ 'rotated': expandedRespondentId === r.id }">▶</span>
                      {{ r.name }}
                    </td>
                    <td class="text-muted">{{ r.designation }}</td>
                    <td class="score-cell">{{ r.overall_avg }}/20</td>
                    <td v-if="!selectedOrg.is_virtual" @click.stop>
                      <select :value="r.weight" @change="updateWeight(r.id, $event.target.value)" class="weight-select">
                        <option value="0.5">0.5×</option>
                        <option value="1">1×</option>
                        <option value="2">2×</option>
                        <option value="3">3×</option>
                      </select>
                    </td>
                    <td class="text-muted">{{ r.email }}</td>
                    <td v-if="!selectedOrg.is_virtual" @click.stop>
                      <button class="btn-icon" title="Send message" @click="openMsgPanel(r)">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
                          <polyline points="22,6 12,12 2,6"/>
                        </svg>
                      </button>
                    </td>
                  </tr>
                  <tr v-if="expandedRespondentId === r.id" class="expanded-row">
                    <td :colspan="!selectedOrg.is_virtual ? 6 : 4" class="expanded-cell">
                      <div class="expanded-content">
                        <ScoreTable :data="r" />
                      </div>
                    </td>
                  </tr>
                </template>
              </tbody>
            </table>
          </div>

          <!-- Send Org Report panel (inline below table) -->
          <div v-if="reportOpen && !selectedOrg.is_virtual" class="report-panel">
            <div class="report-panel-inner">

              <!-- Left: recipients + subject + send -->
              <div class="rp-left">
                <p class="field-label">Recipients</p>
                <div class="recipient-list">
                  <label class="check-all">
                    <input type="checkbox" :checked="allChecked" @change="toggleAll" /> Select all
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
                <button
                  class="btn btn-primary"
                  style="margin-top:1rem;width:100%;"
                  :disabled="!report.selected.length || report.sending"
                  @click="sendOrgReport"
                >{{ report.sending ? 'Sending…' : `Send to ${report.selected.length} recipient${report.selected.length !== 1 ? 's' : ''}` }}</button>
              </div>

              <!-- Right: email preview -->
              <div class="rp-right">
                <p class="field-label">Email Preview</p>
                <div v-if="report.loadingPreview" class="preview-loading">Loading preview…</div>
                <div v-else-if="report.previewHtml" class="email-preview-frame">
                  <iframe :srcdoc="report.previewHtml" sandbox="allow-same-origin" class="email-iframe"></iframe>
                </div>
                <div v-else class="preview-empty">No preview available.</div>
              </div>
            </div>
          </div>

          <!-- Send Message panel -->
          <div v-if="msgPanel.open" class="msg-panel">
            <div class="msg-panel-header">
              <span class="field-label" style="margin:0;">Message — {{ msgPanel.recipient?.name }}</span>
              <span class="text-muted" style="font-size:0.8rem;">{{ msgPanel.recipient?.email }}</span>
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
              <div style="display:flex;gap:0.5rem;margin-top:0.75rem;">
                <button class="btn btn-secondary btn-sm" @click="msgPanel.open = false">Cancel</button>
                <button class="btn btn-primary btn-sm"
                  :disabled="!msgPanel.subject || !msgPanel.body || msgPanel.sending"
                  @click="sendMessage">{{ msgPanel.sending ? 'Sending…' : 'Send' }}</button>
              </div>
            </div>
          </div>

        </template>
      </div>
    </main>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import ScoreTable from '../components/ScoreTable.vue';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';
function getAuthHeaders() {
  const token = sessionStorage.getItem('nd_auth_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ── State ──────────────────────────────────────────────────────────────────
const loading      = ref(true);
const orgs         = ref([]);
const selectedOrg  = ref(null);
const detail       = ref(null);
const loadingDetail = ref(false);
const liveScore    = ref(null);
const reportOpen   = ref(false);
const expandedRespondentId = ref(null);

function toggleRespondent(id) {
  expandedRespondentId.value = expandedRespondentId.value === id ? null : id;
}

const report = reactive({
  respondents: [], selected: [], subject: '',
  sending: false, error: '', success: '',
  previewHtml: '', loadingPreview: false,
});

const msgPanel = reactive({
  open: false, recipient: null,
  subject: '', body: '', sending: false, error: '', success: '',
});

// ── Fetch ──────────────────────────────────────────────────────────────────
async function fetchOrgs() {
  loading.value = true;
  try {
    const res = await fetch(`${API_BASE}/manage/orgs`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed');
    orgs.value = await res.json();
    if (orgs.value.length > 0 && !selectedOrg.value) {
      selectOrg(orgs.value[0]);
    }
  } catch (e) { console.error(e); }
  finally { loading.value = false; }
}

async function fetchDetail(org) {
  loadingDetail.value = true;
  detail.value = null;
  liveScore.value = null;
  try {
    if (org.is_virtual) {
      const params = new URLSearchParams({ company_name: org.name });
      const res = await fetch(`${API_BASE}/manage/orgs/unlinked?${params}`, { headers: getAuthHeaders() });
      if (!res.ok) throw new Error('Failed');
      const subs = await res.json();
      detail.value = { respondents: subs.map(s => ({ ...s, weight: 1.0 })), scores: null };
    } else {
      const res = await fetch(`${API_BASE}/manage/orgs/${org.id}`, { headers: getAuthHeaders() });
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      detail.value = data;
      liveScore.value = data.scores;
    }
  } catch (e) { console.error(e); }
  finally { loadingDetail.value = false; }
}

async function fetchPreview(orgId) {
  report.loadingPreview = true;
  report.previewHtml = '';
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/${orgId}/report-preview`, { headers: getAuthHeaders() });
    if (!res.ok) throw new Error('Failed');
    const data = await res.json();
    report.previewHtml = data.html;
  } catch (e) { console.error(e); }
  finally { report.loadingPreview = false; }
}

// ── Select org ─────────────────────────────────────────────────────────────
async function selectOrg(org) {
  if (selectedOrg.value?.id === org.id) return;
  selectedOrg.value = org;
  reportOpen.value  = false;
  msgPanel.open     = false;
  report.error      = '';
  report.success    = '';
  await fetchDetail(org);
}

// ── Report ─────────────────────────────────────────────────────────────────
async function openReport() {
  const respondents = detail.value?.respondents ?? [];
  report.respondents = respondents;
  report.selected    = [...respondents];
  report.subject     = `${selectedOrg.value.name} — NeuroMark Audit Organisation Summary`;
  report.error       = '';
  report.success     = '';
  report.previewHtml = '';
  fetchPreview(selectedOrg.value.id);
}

// Watch reportOpen to load preview when opened
import { watch } from 'vue';
watch(reportOpen, (val) => { if (val) openReport(); });

const allChecked = computed(() =>
  report.respondents.length > 0 && report.selected.length === report.respondents.length
);
function toggleAll(e) {
  report.selected = e.target.checked ? [...report.respondents] : [];
}

async function sendOrgReport() {
  report.sending = true; report.error = ''; report.success = '';
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/${selectedOrg.value.id}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({
        subject: report.subject, body: '',
        recipients: report.selected.map(r => ({ email: r.email, name: r.name })),
        is_org_report: true,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed');
    report.success = `Sent to ${report.selected.length} recipient${report.selected.length !== 1 ? 's' : ''}.`;
    setTimeout(() => { reportOpen.value = false; }, 1800);
  } catch (e) { report.error = e.message; }
  finally { report.sending = false; }
}

// ── Weight ─────────────────────────────────────────────────────────────────
async function updateWeight(submissionId, weight) {
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/${selectedOrg.value.id}/links/${submissionId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({ weight: parseFloat(weight) }),
    });
    if (!res.ok) throw new Error('Failed');
    const data = await res.json();
    liveScore.value = data.scores;
    const r = detail.value?.respondents.find(r => r.id === submissionId);
    if (r) r.weight = parseFloat(weight);
    const org = orgs.value.find(o => o.id === selectedOrg.value.id);
    if (org && data.scores) { org.org_avg = data.scores.org_avg; org.org_level = data.scores.org_level; }
    selectedOrg.value = { ...selectedOrg.value, org_avg: data.scores?.org_avg, org_level: data.scores?.org_level };
  } catch (e) { console.error(e); }
}

// ── Message ────────────────────────────────────────────────────────────────
function openMsgPanel(recipient) {
  msgPanel.recipient = recipient;
  msgPanel.subject = ''; msgPanel.body = '';
  msgPanel.error = ''; msgPanel.success = '';
  msgPanel.sending = false; msgPanel.open = true;
  reportOpen.value = false;
}

async function sendMessage() {
  msgPanel.sending = true; msgPanel.error = ''; msgPanel.success = '';
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/${selectedOrg.value.id}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({
        subject: msgPanel.subject, body: msgPanel.body,
        recipients: [{ email: msgPanel.recipient.email, name: msgPanel.recipient.name }],
        is_org_report: false,
      }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed');
    msgPanel.success = 'Message sent.';
    setTimeout(() => { msgPanel.open = false; }, 1500);
  } catch (e) { msgPanel.error = e.message; }
  finally { msgPanel.sending = false; }
}

// ── Create org from virtual ────────────────────────────────────────────────
async function createOrg(org) {
  try {
    const res = await fetch(`${API_BASE}/manage/orgs/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({ company_name: org.name }),
    });
    if (!res.ok) throw new Error('Failed');
    selectedOrg.value = null;
    detail.value = null;
    await fetchOrgs();
  } catch (e) { console.error(e); }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function levelClass(level) {
  if (!level) return '';
  if (level.includes('1')) return 'level-1';
  if (level.includes('2')) return 'level-2';
  return 'level-3';
}
function shortLevel(level) {
  if (!level) return '';
  if (level.includes('1')) return 'L1';
  if (level.includes('2')) return 'L2';
  return 'L3';
}

onMounted(fetchOrgs);
</script>

<style scoped>
/* ── Shell: fixed-height split layout ── */
.orgs-shell {
  display: flex;
  flex: 1;
  min-height: 0; /* Important for flex-child scrolling */
  overflow: hidden;
  background: var(--c-white);
  border-radius: 12px;
  border: 2px solid var(--c-primary-dark);
  box-shadow: 4px 4px 0 var(--c-primary-dark);
  margin-top: 1rem;
}

/* ── Left list ── */
.org-list {
  width: 280px;
  flex-shrink: 0;
  border-right: 2px solid var(--c-primary-dark);
  display: flex;
  flex-direction: column;
  background: var(--c-white);
  overflow: hidden;
}
.org-list-header {
  padding: 1.25rem 1.25rem 0.75rem;
  border-bottom: 2px solid var(--c-primary-dark);
  flex-shrink: 0;
}
.org-list-header h2 {
  font-family: 'Playfair Display', serif;
  font-size: 1.1rem; font-weight: 700;
  color: var(--c-primary-dark); margin: 0 0 2px;
}
.org-list-sub { font-size: 0.75rem; color: #aaa; margin: 0; }

.org-list-items {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem 0;
}
.list-loading { padding: 1.5rem; color: #aaa; font-size: 0.88rem; }

.org-list-item {
  width: 100%;
  text-align: left;
  background: none;
  border: none;
  padding: 0.75rem 1.25rem;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: background 0.1s, border-color 0.1s;
}
.org-list-item:hover { background: #F0EDE8; }
.org-list-item.active {
  background: #fff;
  border-left-color: var(--c-primary-dark);
}
.org-list-item.virtual { opacity: 0.75; }

.oli-top {
  display: flex; align-items: center; gap: 0.4rem;
  margin-bottom: 0.25rem;
}
.oli-name {
  font-weight: 700; font-size: 0.88rem;
  color: var(--c-primary-dark);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  max-width: 140px;
}
.oli-bottom { display: flex; align-items: center; gap: 0.4rem; }
.oli-score  { font-size: 0.82rem; font-weight: 800; color: var(--c-primary-dark); }
.oli-count  { font-size: 0.72rem; color: #aaa; margin-left: auto; }

/* ── Right detail ── */
.org-detail-panel {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem 2rem;
  min-width: 0;
}

.detail-empty {
  height: 100%;
  display: flex; align-items: center; justify-content: center;
  color: #bbb; font-size: 0.9rem;
}

.detail-header {
  display: flex; align-items: flex-start; justify-content: space-between;
  margin-bottom: 1.25rem; gap: 1rem;
}
.detail-org-name {
  font-family: 'Playfair Display', serif;
  font-size: 1.4rem; font-weight: 700;
  color: var(--c-primary-dark); margin: 0 0 0.4rem;
}
.detail-meta { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; }
.detail-score { font-size: 1.1rem; font-weight: 800; color: var(--c-primary-dark); }
.detail-count { font-size: 0.8rem; color: #aaa; }
.detail-loading { color: #aaa; font-size: 0.9rem; padding: 1rem 0; }

/* ── Badges ── */
.level-badge {
  font-size: 0.68rem; font-weight: 700; padding: 0.18rem 0.55rem;
  border-radius: 99px; text-transform: uppercase; letter-spacing: 0.04em;
}
.level-1 { background: #FEE2E2; color: #B91C1C; }
.level-2 { background: #FEF3C7; color: #92400E; }
.level-3 { background: #D1FAE5; color: #065F46; }
.virtual-badge {
  font-size: 0.62rem; font-weight: 700; padding: 0.12rem 0.45rem;
  border-radius: 99px; background: #FEF3C7; color: #92400E;
  text-transform: uppercase; letter-spacing: 0.04em;
}

/* ── Respondent table ── */
.detail-section { margin-bottom: 1.5rem; }
.respondent-table { width: 100%; border-collapse: separate; border-spacing: 0; }
.respondent-table th {
  text-align: left;
  padding: 0.75rem 1rem;
  font-size: 0.7rem;
  font-weight: 700;
  color: #aaa;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid #E2DDD4;
}
.respondent-table td {
  padding: 1rem 1rem;
  border-bottom: 1px solid #eee;
  vertical-align: middle;
}
.respondent-row {
  cursor: pointer;
  transition: background 0.15s;
}
.respondent-row:hover {
  background: #fdfdfc;
}
.respondent-row.expanded {
  background: #FCFCFA;
}
.chevron {
  display: inline-block;
  font-size: 0.6rem;
  color: #aaa;
  margin-right: 0.4rem;
  transition: transform 0.2s;
}
.chevron.rotated {
  transform: rotate(90deg);
  color: var(--c-primary-dark);
}
.expanded-row {
  background: #FCFCFA;
}
.expanded-cell {
  padding: 0 !important;
  border-bottom: 2px solid var(--c-primary-dark) !important;
}
.expanded-content {
  padding: 1.5rem 2rem;
  border-left: 4px solid var(--c-accent);
}
.font-medium { font-weight: 600; color: var(--c-primary-dark); }
.text-muted  { color: #888; font-size: 0.85rem; }

.weight-select {
  padding: 0.28rem 0.45rem; border: 2px solid #E2DDD4; border-radius: 6px;
  font-size: 0.82rem; font-weight: 700; cursor: pointer;
  background: #fff; color: var(--c-primary-dark);
}
.weight-select:focus { outline: none; border-color: var(--c-primary-dark); }

.btn-icon {
  background: none; border: none; cursor: pointer; padding: 0.35rem;
  border-radius: 6px; color: #888; transition: all 0.12s;
}
.btn-icon:hover { background: #F0F0F0; color: var(--c-primary-dark); }
.btn-sm { padding: 0.32rem 0.8rem; font-size: 0.78rem; }

/* ── Report panel ── */
.report-panel {
  border: 2px solid var(--c-primary-dark);
  border-radius: 12px;
  background: #FAFAF8;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}
.report-panel-inner { display: flex; gap: 1.5rem; align-items: flex-start; }
.rp-left  { flex: 0 0 240px; display: flex; flex-direction: column; }
.rp-right { flex: 1; min-width: 0; }

.field-label {
  font-size: 0.7rem; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.06em; color: #aaa; margin-bottom: 0.5rem;
}
.recipient-list { display: flex; flex-direction: column; gap: 0.35rem; }
.check-all { font-weight: 700; font-size: 0.8rem; display: flex; align-items: center; gap: 0.4rem; cursor: pointer; }
.recipient-row { display: flex; align-items: center; gap: 0.4rem; font-size: 0.82rem; cursor: pointer; }

.field { display: flex; flex-direction: column; gap: 0.3rem; margin-bottom: 0.6rem; }
.field label { font-size: 0.76rem; font-weight: 700; color: var(--c-primary-dark); }
.field input, .field textarea {
  padding: 0.5rem 0.7rem; border: 2px solid #E2DDD4; border-radius: 8px;
  font-family: inherit; font-size: 0.86rem; resize: vertical; background: #fff;
}
.field input:focus, .field textarea:focus { outline: none; border-color: var(--c-primary-dark); }

.preview-loading { color: #aaa; font-size: 0.85rem; padding: 0.5rem 0; }
.preview-empty   { color: #ccc; font-size: 0.85rem; padding: 0.5rem 0; }
.email-preview-frame { border: 2px solid #E2DDD4; border-radius: 8px; overflow: hidden; height: 460px; }
.email-iframe { width: 100%; height: 100%; border: none; display: block; }

/* ── Message panel ── */
.msg-panel {
  border: 2px solid #E2DDD4;
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
  background: #fff;
  max-width: 520px;
}
.msg-panel-header {
  display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem;
}
.msg-panel-body {}

.error-msg   { color: #EF4444; font-size: 0.8rem; margin-top: 0.3rem; }
.success-msg { color: #10B981; font-size: 0.8rem; margin-top: 0.3rem; }
</style>
