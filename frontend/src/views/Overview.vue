<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Dashboard Overview</h1>
        <p>High-level insights into your organization's neuro-inclusion maturity.</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-outline" @click="copyAuditLink">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
          {{ linkCopied ? 'Link Copied!' : 'Copy Audit Link' }}
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
          <span class="stat-badge green">+12%</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div>
        <div class="stat-label">Pending Reviews</div>
        <div class="stat-bottom">
          <div class="stat-value">{{ stats.pending }}</div>
          <span class="stat-badge red">Action Needed</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg></div>
        <div class="stat-label">Emails Sent</div>
        <div class="stat-bottom">
          <div class="stat-value">{{ stats.sent }}</div>
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

    <!-- Charts row -->
    <div class="charts-row">
      <div class="card chart-card">
        <div class="chart-header">
          <span class="chart-title">Submissions Trend</span>
          <button class="icon-btn-sm">···</button>
        </div>
        <canvas ref="trendChart" height="200"></canvas>
      </div>
      <div class="card chart-card">
        <div class="chart-header">
          <span class="chart-title">Score Distribution</span>
          <button class="icon-btn-sm">⇅</button>
        </div>
        <canvas ref="distChart" height="200"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { Chart, registerables } from "chart.js";
import { getSubmissions } from "../api";

Chart.register(...registerables);

const trendChart = ref(null);
const distChart  = ref(null);
const stats = ref({ total: 0, pending: 0, sent: 0, avgScore: 0 });
const downloading = ref(false);
const linkCopied = ref(false);

function copyAuditLink() {
  const url = "https://neurvex.orchvate.in/#/";
  navigator.clipboard.writeText(url).then(() => {
    linkCopied.value = true;
    setTimeout(() => { linkCopied.value = false; }, 2000);
  });
}

function downloadReport() {
  downloading.value = true;
  try {
    const subs = allSubmissions.value;
    if (!subs.length) { downloading.value = false; return; }

    const headers = [
      "ID","Name","Designation","Organisation","Email","Submitted",
      "Overall Score","Overall Level","Status",
      "Leadership","Recruitment","Workplace","Sensory","Talent","Comms","Products","Suppliers"
    ];
    const rows = subs.map(s => [
      s.id, s.name, s.designation, s.company_name, s.email,
      s.submitted_at ? new Date(s.submitted_at).toLocaleDateString("en-GB") : "",
      s.overall_avg, s.overall_level, s.status,
      s.lc_score, s.ro_score, s.we_score, s.be_score,
      s.tm_score, s.ca_score, s.pc_score, s.sp_score
    ]);

    const csv = [headers, ...rows]
      .map(r => r.map(v => `"${String(v ?? "").replace(/"/g, '""')}"`).join(","))
      .join("\n");

    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `neurvex-report-${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  } finally {
    downloading.value = false;
  }
}

const allSubmissions = ref([]);

onMounted(async () => {
  let submissions = [];
  try { submissions = await getSubmissions(); } catch {}
  allSubmissions.value = submissions;

  // Compute stats
  stats.value.total   = submissions.length;
  stats.value.pending = submissions.filter(s => s.status === "pending").length;
  stats.value.sent    = submissions.filter(s => s.status === "sent").length;
  const avg = submissions.length
    ? (submissions.reduce((a, s) => a + parseFloat(s.overall_avg || 0), 0) / submissions.length).toFixed(1)
    : 0;
  stats.value.avgScore = avg;

  // Trend chart — group by month
  const months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const counts  = Array(12).fill(0);
  submissions.forEach(s => {
    const m = new Date(s.submitted_at).getMonth();
    counts[m]++;
  });
  const now = new Date().getMonth();
  const trendLabels = months.slice(0, now + 1);
  const trendData   = counts.slice(0, now + 1);

  new Chart(trendChart.value, {
    type: "line",
    data: {
      labels: trendLabels,
      datasets: [{
        data: trendData,
        borderColor: "var(--c-primary-dark)",
        backgroundColor: "rgba(200,241,53,0.15)",
        fill: true, tension: 0.4, pointRadius: 4,
        pointBackgroundColor: "var(--c-accent)",
        pointBorderColor: "var(--c-primary-dark)",
        pointBorderWidth: 2,
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: "var(--c-bg)" }, ticks: { color: "#bbb" } },
        x: { grid: { display: false }, ticks: { color: "#bbb" } },
      },
    },
  });

  const l1 = submissions.filter(s => s.overall_level?.includes("1")).length;
  const l2 = submissions.filter(s => s.overall_level?.includes("2")).length;
  const l3 = submissions.filter(s => s.overall_level?.includes("3")).length;

  new Chart(distChart.value, {
    type: "bar",
    data: {
      labels: ["Level 1\n(Foundational)", "Level 2\n(Early Progress)", "Level 3\n(Developing)"],
      datasets: [{
        data: [l1, l2, l3],
        backgroundColor: ["#E2DDD4", "var(--c-accent)", "var(--c-primary-dark)"],
        borderRadius: 8,
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: {
        y: { beginAtZero: true, grid: { color: "var(--c-bg)" }, ticks: { color: "#bbb" } },
        x: { grid: { display: false }, ticks: { color: "#bbb" } },
      },
    },
  });
});
</script>

<style scoped>
.page-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 1.75rem; }
.page-header h1 { font-size: 2rem; font-weight: 800; color: var(--c-primary-dark); letter-spacing: -0.03em; font-family: 'Playfair Display', serif; }
.page-header p  { color: #888; font-size: 0.875rem; margin-top: 0.3rem; }
.header-actions { display: flex; gap: 0.6rem; flex-wrap: wrap; align-items: flex-start; }

.stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.25rem; }
.stat-card {
  background: var(--c-white); border-radius: 20px; padding: 1.1rem 1.25rem;
  border: 2px solid var(--c-primary-dark); box-shadow: none;
  position: relative; transition: all 0.15s;
}
.stat-card:hover { background: #FDFAF5; }
.stat-icon {
  position: absolute; top: 1rem; right: 1rem;
  color: #ddd; line-height: 0;
}
.stat-label {
  font-size: 0.68rem; color: #aaa; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.07em;
  font-family: 'Geist', sans-serif; margin-bottom: 0.5rem;
}
.stat-bottom {
  display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;
}
.stat-value {
  font-size: 2rem; font-weight: 700; color: var(--c-primary-dark);
  letter-spacing: -0.03em; font-family: 'Playfair Display', serif;
  line-height: 1;
}
.stat-unit { font-size: 0.9rem; font-weight: 400; color: #bbb; font-family: 'Geist', sans-serif; }
.stat-badge {
  display: inline-flex; align-items: center;
  font-size: 0.7rem; font-weight: 700; padding: 0.18rem 0.55rem;
  border-radius: 99px; border: 1.5px solid currentColor;
  font-family: 'Geist', sans-serif; white-space: nowrap;
}
.stat-badge.green { background: #EDFFD4; color: #3A7A00; }
.stat-badge.red   { background: #FFF0F0; color: #C0392B; }

.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.chart-card { padding: 1.25rem 1.5rem; }
.chart-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.25rem; }
.chart-title { font-weight: 800; font-size: 1rem; color: var(--c-primary-dark); font-family: 'Playfair Display', serif; }
.icon-btn-sm { background: none; border: none; cursor: pointer; color: #ccc; font-size: 1.1rem; letter-spacing: 2px; }
</style>
