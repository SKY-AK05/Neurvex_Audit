<template>
  <div>
    <!-- Header -->
    <div class="page-header">
      <div>
        <h1>Dashboard</h1>
        <p>What needs your attention today.</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-outline" @click="copyAuditLink">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
          {{ linkCopied ? 'Copied!' : 'Copy Audit Link' }}
        </button>
        <button class="btn btn-primary" @click="downloadReport" :disabled="downloading">
          {{ downloading ? 'Preparing…' : '⬇ Download Report' }}
        </button>
      </div>
    </div>

    <!-- Stat cards -->
    <div class="stat-grid">
      <div class="stat-card">
        <div class="stat-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>
        <div class="stat-label">Total Submissions</div>
        <div class="stat-bottom">
          <div class="stat-value">{{ stats.total }}</div>
          <span v-if="stats.weekNew > 0" class="stat-badge green">+{{ stats.weekNew }} this week</span>
        </div>
      </div>
      <div class="stat-card urgent">
        <div class="stat-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
        <div class="stat-label">Pending Review</div>
        <div class="stat-bottom">
          <div class="stat-value">{{ stats.pending }}</div>
          <span v-if="stats.pending > 0" class="stat-badge red">Action Needed</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg></div>
        <div class="stat-label">Emails Sent</div>
        <div class="stat-bottom">
          <div class="stat-value">{{ stats.sent }}</div>
          <span class="stat-unit">of {{ stats.total }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg></div>
        <div class="stat-label">Avg. Maturity Score</div>
        <div class="stat-bottom">
          <div class="stat-value">{{ stats.avgScore }}</div>
          <span class="stat-unit">/ 20</span>
        </div>
      </div>
    </div>

    <!-- Two column: pending actions + recent -->
    <div class="two-col">

      <!-- Pending actions -->
      <div class="card action-card">
        <div class="card-head">
          <span class="card-title">Pending Actions</span>
          <span class="count-badge" v-if="pendingList.length">{{ pendingList.length }}</span>
        </div>
        <p v-if="loading" class="empty-msg">Loading…</p>
        <p v-else-if="!pendingList.length" class="empty-msg all-good">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
          All caught up — no pending submissions
        </p>
        <div v-else class="action-list">
          <div v-for="s in pendingList" :key="s.id" class="action-row">
            <div class="action-info" @click="$router.push(`/admin/submissions/${s.id}`)">
              <div class="action-name">{{ s.name }}</div>
              <div class="action-meta">{{ s.company_name }} · {{ fmtDate(s.submitted_at) }}</div>
            </div>
            <div class="action-score">{{ s.overall_avg }}/20</div>
            <button class="btn-send" @click="$router.push(`/admin/submissions/${s.id}`)">
              Review →
            </button>
          </div>
        </div>
      </div>

      <!-- Recent submissions -->
      <div class="card recent-card">
        <div class="card-head">
          <span class="card-title">Recent Submissions</span>
          <router-link to="/admin/submissions" class="see-all">See all →</router-link>
        </div>
        <p v-if="loading" class="empty-msg">Loading…</p>
        <p v-else-if="!recentList.length" class="empty-msg">No submissions yet.</p>
        <div v-else class="recent-list">
          <div v-for="s in recentList" :key="s.id" class="recent-row" @click="$router.push(`/admin/submissions/${s.id}`)">
            <div class="recent-avatar">{{ initials(s.name) }}</div>
            <div class="recent-info">
              <div class="recent-name">{{ s.name }}</div>
              <div class="recent-meta">{{ s.company_name }}</div>
            </div>
            <div class="recent-right">
              <span :class="`badge badge-${s.status}`">{{ cap(s.status) }}</span>
              <div class="recent-score">{{ s.overall_avg }}/20</div>
            </div>
          </div>
        </div>
      </div>

    </div>

    <!-- This week vs last week -->
    <div class="card week-card">
      <div class="card-head">
        <span class="card-title">This week vs last week</span>
      </div>
      <div class="week-grid">
        <div class="week-stat">
          <div class="week-label">New submissions this week</div>
          <div class="week-val">{{ stats.weekNew }}</div>
        </div>
        <div class="week-stat">
          <div class="week-label">New submissions last week</div>
          <div class="week-val">{{ stats.weekPrev }}</div>
        </div>
        <div class="week-stat">
          <div class="week-label">Emails sent this week</div>
          <div class="week-val">{{ stats.weekSent }}</div>
        </div>
        <div class="week-stat">
          <div class="week-label">Avg score this week</div>
          <div class="week-val">{{ stats.weekAvg }}<span class="week-unit">/20</span></div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { getSubmissions } from "../api";

const loading = ref(true);
const allSubmissions = ref([]);
const downloading = ref(false);
const linkCopied = ref(false);

const stats = ref({ total: 0, pending: 0, sent: 0, avgScore: 0, weekNew: 0, weekPrev: 0, weekSent: 0, weekAvg: 0 });

const pendingList = computed(() =>
  allSubmissions.value
    .filter(s => s.status === "pending")
    .sort((a, b) => new Date(a.submitted_at) - new Date(b.submitted_at))
);

const recentList = computed(() =>
  allSubmissions.value.slice(0, 6)
);

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}
function cap(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : ""; }
function initials(name) {
  if (!name) return "?";
  const p = name.trim().split(" ");
  return p.length >= 2 ? (p[0][0] + p[1][0]).toUpperCase() : name.substring(0, 2).toUpperCase();
}

function copyAuditLink() {
  navigator.clipboard.writeText("https://neurvex.orchvate.in/#/").then(() => {
    linkCopied.value = true;
    setTimeout(() => { linkCopied.value = false; }, 2000);
  });
}

function downloadReport() {
  downloading.value = true;
  try {
    const subs = allSubmissions.value;
    if (!subs.length) return;
    const headers = ["ID","Name","Designation","Organisation","Email","Submitted","Overall Score","Overall Level","Status","Leadership","Recruitment","Workplace","Sensory","Talent","Comms","Products","Suppliers"];
    const rows = subs.map(s => [s.id, s.name, s.designation, s.company_name, s.email, s.submitted_at ? new Date(s.submitted_at).toLocaleDateString("en-GB") : "", s.overall_avg, s.overall_level, s.status, s.lc_score, s.ro_score, s.we_score, s.be_score, s.tm_score, s.ca_score, s.pc_score, s.sp_score]);
    const csv = [headers, ...rows].map(r => r.map(v => `"${String(v ?? "").replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `neurvex-report-${new Date().toISOString().slice(0,10)}.csv`; a.click();
    URL.revokeObjectURL(url);
  } finally { downloading.value = false; }
}

onMounted(async () => {
  try {
    const subs = await getSubmissions();
    allSubmissions.value = subs;

    const now = new Date();
    const startOfWeek = new Date(now); startOfWeek.setDate(now.getDate() - now.getDay());
    const startOfLastWeek = new Date(startOfWeek); startOfLastWeek.setDate(startOfWeek.getDate() - 7);

    const thisWeek = subs.filter(s => new Date(s.submitted_at) >= startOfWeek);
    const lastWeek = subs.filter(s => new Date(s.submitted_at) >= startOfLastWeek && new Date(s.submitted_at) < startOfWeek);

    const avg = subs.length ? (subs.reduce((a, s) => a + parseFloat(s.overall_avg || 0), 0) / subs.length).toFixed(1) : 0;
    const weekAvg = thisWeek.length ? (thisWeek.reduce((a, s) => a + parseFloat(s.overall_avg || 0), 0) / thisWeek.length).toFixed(1) : 0;

    stats.value = {
      total: subs.length,
      pending: subs.filter(s => s.status === "pending").length,
      sent: subs.filter(s => s.status === "sent").length,
      avgScore: avg,
      weekNew: thisWeek.length,
      weekPrev: lastWeek.length,
      weekSent: thisWeek.filter(s => s.status === "sent").length,
      weekAvg,
    };
  } catch {}
  loading.value = false;
});
</script>

<style scoped>
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 1.75rem; }
.page-header h1 { font-size: 2rem; font-weight: 800; color: var(--c-primary-dark); letter-spacing: -0.03em; font-family: 'Playfair Display', serif; }
.page-header p  { color: #888; font-size: 0.875rem; margin-top: 0.3rem; }
.header-actions { display: flex; gap: 0.6rem; align-items: flex-start; }

/* Stat cards */
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.25rem; }
.stat-card {
  background: var(--c-white); border-radius: 16px; padding: 1.1rem 1.25rem;
  border: 2px solid var(--c-primary-dark); position: relative; transition: all 0.15s;
}
.stat-card.urgent { border-color: #C0392B; }
.stat-icon { position: absolute; top: 1rem; right: 1rem; color: #ddd; }
.stat-label { font-size: 0.68rem; color: #aaa; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 0.5rem; }
.stat-bottom { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.stat-value { font-size: 2rem; font-weight: 700; color: var(--c-primary-dark); letter-spacing: -0.03em; font-family: 'Playfair Display', serif; line-height: 1; }
.stat-unit { font-size: 0.9rem; color: #bbb; }
.stat-badge { display: inline-flex; align-items: center; font-size: 0.7rem; font-weight: 700; padding: 0.18rem 0.55rem; border-radius: 99px; border: 1.5px solid currentColor; white-space: nowrap; }
.stat-badge.green { background: #EDFFD4; color: #3A7A00; }
.stat-badge.red   { background: #FFF0F0; color: #C0392B; }

/* Two col layout */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }

.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.card-title { font-size: 0.95rem; font-weight: 800; color: var(--c-primary-dark); font-family: 'Playfair Display', serif; }
.count-badge { background: #C0392B; color: #fff; font-size: 0.72rem; font-weight: 800; padding: 0.15rem 0.55rem; border-radius: 99px; }
.see-all { font-size: 0.8rem; color: #aaa; text-decoration: none; font-weight: 600; }
.see-all:hover { color: var(--c-primary-dark); }

.empty-msg { color: #bbb; font-size: 0.875rem; text-align: center; padding: 1.5rem 0; }
.empty-msg.all-good { color: #3A7A00; display: flex; align-items: center; justify-content: center; gap: 0.4rem; }

/* Pending action list */
.action-list { display: flex; flex-direction: column; gap: 0.6rem; }
.action-row { display: flex; align-items: center; gap: 0.75rem; padding: 0.65rem 0.75rem; border-radius: 10px; background: var(--c-bg); border: 1px solid #E2DDD4; }
.action-info { flex: 1; cursor: pointer; }
.action-info:hover .action-name { text-decoration: underline; }
.action-name { font-size: 0.875rem; font-weight: 700; color: var(--c-primary-dark); }
.action-meta { font-size: 0.75rem; color: #888; margin-top: 0.1rem; }
.action-score { font-size: 0.8rem; font-weight: 700; color: var(--c-primary-dark); white-space: nowrap; }
.btn-send { background: var(--c-primary-dark); color: var(--c-white); border: none; border-radius: 99px; padding: 0.35rem 0.85rem; font-size: 0.78rem; font-weight: 700; cursor: pointer; white-space: nowrap; transition: opacity 0.15s; }
.btn-send:hover { opacity: 0.8; }

/* Recent list */
.recent-list { display: flex; flex-direction: column; gap: 0.5rem; }
.recent-row { display: flex; align-items: center; gap: 0.75rem; padding: 0.6rem 0.5rem; border-radius: 10px; cursor: pointer; transition: background 0.15s; }
.recent-row:hover { background: var(--c-bg); }
.recent-avatar { width: 34px; height: 34px; border-radius: 50%; background: var(--c-primary-dark); color: var(--c-accent); display: grid; place-items: center; font-size: 0.72rem; font-weight: 800; flex-shrink: 0; }
.recent-info { flex: 1; min-width: 0; }
.recent-name { font-size: 0.875rem; font-weight: 700; color: var(--c-primary-dark); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.recent-meta { font-size: 0.75rem; color: #888; }
.recent-right { display: flex; flex-direction: column; align-items: flex-end; gap: 0.2rem; }
.recent-score { font-size: 0.75rem; font-weight: 700; color: #888; }

/* Week card */
.week-card { margin-bottom: 0; }
.week-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
.week-stat { text-align: center; padding: 0.75rem; background: var(--c-bg); border-radius: 10px; }
.week-label { font-size: 0.72rem; color: #888; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.4rem; }
.week-val { font-size: 1.6rem; font-weight: 800; color: var(--c-primary-dark); font-family: 'Playfair Display', serif; }
.week-unit { font-size: 0.85rem; font-weight: 400; color: #bbb; }

@media (max-width: 900px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); }
  .two-col { grid-template-columns: 1fr; }
  .week-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
