<template>
  <div>
    <div class="page-header">
      <div class="header-left">
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
    </div>

    <!-- Stat cards -->
    <div class="stat-grid">
      <div class="stat-card" :class="{ 'skeleton-card': loading }">
        <div class="stat-icon" :class="{ skeleton: loading }"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div>
        <div class="stat-label">Total Submissions</div>
        <div class="stat-bottom">
          <div v-if="loading" class="skeleton-text" style="height: 2rem; width: 3rem;"></div>
          <template v-else>
            <div class="stat-value">{{ stats.total }}</div>
            <span v-if="stats.weekNew > 0" class="stat-badge green">+{{ stats.weekNew }} this week</span>
          </template>
        </div>
      </div>
      <div class="stat-card urgent" :class="{ 'skeleton-card': loading }">
        <div class="stat-icon" :class="{ skeleton: loading }"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
        <div class="stat-label">Pending Review</div>
        <div class="stat-bottom">
          <div v-if="loading" class="skeleton-text" style="height: 2rem; width: 3rem;"></div>
          <template v-else>
            <div class="stat-value">{{ stats.pending }}</div>
            <span v-if="stats.pending > 0" class="stat-badge red">Action Needed</span>
          </template>
        </div>
      </div>
      <div class="stat-card" :class="{ 'skeleton-card': loading }">
        <div class="stat-icon" :class="{ skeleton: loading }"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg></div>
        <div class="stat-label">Emails Sent</div>
        <div class="stat-bottom">
          <div v-if="loading" class="skeleton-text" style="height: 2rem; width: 4rem;"></div>
          <template v-else>
            <div class="stat-value">{{ stats.sent }}</div>
            <span class="stat-unit">of {{ stats.total }}</span>
          </template>
        </div>
      </div>
      <div class="stat-card" :class="{ 'skeleton-card': loading }">
        <div class="stat-icon" :class="{ skeleton: loading }"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg></div>
        <div class="stat-label">Avg. Maturity Score</div>
        <div class="stat-bottom">
          <div v-if="loading" class="skeleton-text" style="height: 2rem; width: 4rem;"></div>
          <template v-else>
            <div class="stat-value">{{ stats.avgScore }}</div>
            <span class="stat-unit">/ 20</span>
          </template>
        </div>
      </div>
    </div>

    <!-- This week vs last week -->
    <div class="card week-card" style="margin-bottom: 1rem;">
      <div class="card-head">
        <span class="card-title">This week vs last week</span>
      </div>
      <div class="week-grid">
        <div class="week-stat">
          <div class="week-label">New submissions this week</div>
          <div v-if="loading" class="skeleton-text" style="height: 2rem; width: 3rem; margin: 0 auto;"></div>
          <div v-else class="week-val">{{ stats.weekNew }}</div>
        </div>
        <div class="week-stat">
          <div class="week-label">New submissions last week</div>
          <div v-if="loading" class="skeleton-text" style="height: 2rem; width: 3rem; margin: 0 auto;"></div>
          <div v-else class="week-val">{{ stats.weekPrev }}</div>
        </div>
        <div class="week-stat">
          <div class="week-label">Emails sent this week</div>
          <div v-if="loading" class="skeleton-text" style="height: 2rem; width: 3rem; margin: 0 auto;"></div>
          <div v-else class="week-val">{{ stats.weekSent }}</div>
        </div>
        <div class="week-stat">
          <div class="week-label">Avg score this week</div>
          <div v-if="loading" class="skeleton-text" style="height: 2rem; width: 4rem; margin: 0 auto;"></div>
          <div v-else class="week-val">{{ stats.weekAvg }}<span class="week-unit">/20</span></div>
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
        <div v-if="loading" class="action-list">
          <div v-for="i in 3" :key="i" class="action-row skeleton-card">
            <div class="action-info">
              <div class="skeleton-text" style="width: 70%;"></div>
              <div class="skeleton-text" style="width: 40%; height: 0.75rem;"></div>
            </div>
            <div class="skeleton-text" style="width: 3rem;"></div>
          </div>
        </div>
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
        <div v-if="loading" class="recent-list">
          <div v-for="i in 4" :key="i" class="recent-row skeleton-card">
            <div class="skeleton-avatar"></div>
            <div class="recent-info">
              <div class="skeleton-text" style="width: 60%;"></div>
              <div class="skeleton-text" style="width: 40%; height: 0.75rem;"></div>
            </div>
            <div class="recent-right">
              <div class="skeleton-text" style="width: 4rem; margin-bottom: 0;"></div>
              <div class="skeleton-text" style="width: 2rem;"></div>
            </div>
          </div>
        </div>
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

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { getSubmissions } from "../api";
import {
  formatDateShort as fmtDate,
  formatDate,
  startOfISTWeek,
  todayISTDateString,
} from "../utils/datetime";

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

function cap(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : ""; }
function initials(name) {
  if (!name) return "?";
  const p = name.trim().split(" ");
  return p.length >= 2 ? (p[0][0] + p[1][0]).toUpperCase() : name.substring(0, 2).toUpperCase();
}

function copyAuditLink() {
  const url = import.meta.env.VITE_APP_URL || "https://NIWI.orchvate.in/";
  navigator.clipboard.writeText(url).then(() => {
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
    const rows = subs.map(s => [s.id, s.name, s.designation, s.company_name, s.email, s.submitted_at ? formatDate(s.submitted_at) : "", s.overall_avg, s.overall_level, s.status, s.lc_score, s.ro_score, s.we_score, s.be_score, s.tm_score, s.ca_score, s.pc_score, s.sp_score]);
    const csv = [headers, ...rows].map(r => r.map(v => `"${String(v ?? "").replace(/"/g, '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = `NIWI-report-${todayISTDateString()}.csv`; a.click();
    URL.revokeObjectURL(url);
  } finally { downloading.value = false; }
}

onMounted(async () => {
  try {
    const subs = await getSubmissions();
    allSubmissions.value = subs;

    const startOfWeek = startOfISTWeek();
    const startOfLastWeek = new Date(startOfWeek.getTime() - 7 * 24 * 60 * 60 * 1000);

    const thisWeek = subs.filter(s => new Date(s.submitted_at) >= startOfWeek);
    const lastWeek = subs.filter(
      s => new Date(s.submitted_at) >= startOfLastWeek && new Date(s.submitted_at) < startOfWeek
    );

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
.page-header { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 24px; }
.header-left { display: flex; align-items: flex-end; gap: 2rem; flex: 1; }
.page-header h1 { font-size: 2.25rem; font-weight: 800; color: var(--c-primary-dark, #161057); letter-spacing: -0.03em; font-family: 'Fraunces', serif; margin-bottom: 0; line-height: 1; }
.page-header p  { color: #64748B; font-size: 0.9rem; margin-top: 0.35rem; margin-bottom: 0; }
.header-actions { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 2px; }
.header-actions .btn { padding: 0.55rem 1.25rem; font-size: 0.825rem; border-radius: 99px; font-weight: 600; }

/* Stat cards */
.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
.stat-card {
  background: var(--c-white, #FFFFFF); border-radius: 16px; padding: 22px 24px;
  border: 1px solid rgba(22, 16, 87, 0.08); position: relative; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 10px rgba(22, 16, 87, 0.03);
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(22, 16, 87, 0.06);
}
.stat-card.urgent { border-color: #FCA5A5; background: #FFFDFD; }
.stat-icon { position: absolute; top: 18px; right: 20px; color: #94A3B8; }
.stat-label { font-size: 0.7rem; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 10px; }
.stat-bottom { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.stat-value { font-size: 2.5rem; font-weight: 800; color: var(--c-primary-dark, #161057); letter-spacing: -0.04em; font-family: 'Fraunces', serif; line-height: 1; }
.stat-unit { font-size: 1rem; color: #94A3B8; font-weight: 500; }
.stat-badge { display: inline-flex; align-items: center; font-size: 0.725rem; font-weight: 700; padding: 0.25rem 0.65rem; border-radius: 99px; white-space: nowrap; }
.stat-badge.green { background: #DCFCE7; color: #166534; }
.stat-badge.red   { background: #FEE2E2; color: #991B1B; }

/* Two col layout */
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; }

.card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.card-title { font-size: 1.05rem; font-weight: 800; color: var(--c-primary-dark, #161057); font-family: 'Fraunces', serif; letter-spacing: -0.015em; }
.count-badge { background: #FEE2E2; color: #991B1B; font-size: 0.7rem; font-weight: 800; padding: 0.2rem 0.6rem; border-radius: 99px; }
.see-all { font-size: 0.8rem; color: #64748B; text-decoration: none; font-weight: 600; transition: color 0.15s; }
.see-all:hover { color: var(--c-primary-dark, #161057); }

.empty-msg { color: #94A3B8; font-size: 0.875rem; text-align: center; padding: 32px 0; }
.empty-msg.all-good { color: var(--c-accent, #04907C); display: flex; align-items: center; justify-content: center; gap: 0.4rem; font-weight: 600; }

/* Pending action list */
.action-list { display: flex; flex-direction: column; gap: 10px; }
.action-row { display: flex; align-items: center; gap: 12px; padding: 14px 16px; border-radius: 12px; background: #FAFAF8; border: 1px solid rgba(22, 16, 87, 0.06); transition: all 0.15s; }
.action-row:hover { background: #F1F4F9; }
.action-info { flex: 1; cursor: pointer; }
.action-info:hover .action-name { text-decoration: underline; }
.action-name { font-size: 0.9rem; font-weight: 700; color: var(--c-primary-dark, #161057); }
.action-meta { font-size: 0.78rem; color: #64748B; margin-top: 0.15rem; }
.action-score { font-size: 0.85rem; font-weight: 700; color: var(--c-primary-dark, #161057); white-space: nowrap; }
.btn-send { background: var(--c-primary-dark, #161057); color: #FFFFFF; border: none; border-radius: 99px; padding: 0.45rem 1.1rem; font-size: 0.8rem; font-weight: 700; cursor: pointer; white-space: nowrap; transition: all 0.15s; box-shadow: 0 2px 8px rgba(22, 16, 87, 0.2); }
.btn-send:hover { background: #0f0a42; transform: translateY(-1px); }

/* Recent list */
.recent-list { display: flex; flex-direction: column; gap: 8px; }
.recent-row { display: flex; align-items: center; gap: 12px; padding: 12px 10px; border-radius: 12px; cursor: pointer; transition: background 0.15s; }
.recent-row:hover { background: #FAFAF8; }
.recent-avatar { width: 40px; height: 40px; border-radius: 50%; background: var(--c-primary-dark, #161057); color: #FFFFFF; display: grid; place-items: center; font-size: 0.78rem; font-weight: 800; flex-shrink: 0; }
.recent-info { flex: 1; min-width: 0; }
.recent-name { font-size: 0.9rem; font-weight: 700; color: var(--c-primary-dark, #161057); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.recent-meta { font-size: 0.78rem; color: #64748B; margin-top: 2px; }
.recent-right { display: flex; flex-direction: column; align-items: flex-end; gap: 4px; }
.recent-score { font-size: 0.78rem; font-weight: 700; color: #64748B; }

/* Week card */
.week-card { margin-bottom: 20px; }
.week-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.week-stat { text-align: center; padding: 18px 16px; background: #FAFAF8; border-radius: 14px; border: 1px solid rgba(22, 16, 87, 0.05); }
.week-label { font-size: 0.7rem; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; }
.week-val { font-size: 2rem; font-weight: 800; color: var(--c-primary-dark, #161057); font-family: 'Fraunces', serif; line-height: 1; }
.week-unit { font-size: 0.9rem; font-weight: 400; color: #94A3B8; }

@media (max-width: 900px) {
  .stat-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .two-col { grid-template-columns: 1fr; gap: 12px; }
  .week-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .page-header { flex-direction: column; align-items: flex-start; gap: 16px; }
  .header-left { flex-direction: column; align-items: flex-start; gap: 8px; }
  .header-actions { width: 100%; justify-content: stretch; }
  .header-actions .btn { flex: 1; }
}
</style>
