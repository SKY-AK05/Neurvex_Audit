<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Analytics</h1>
        <p>Patterns and insights across all audit submissions.</p>
      </div>
    </div>

    <p v-if="loading" class="loading">Loading analytics…</p>
    <p v-else-if="!submissions.length" class="loading">No submissions yet — analytics will appear once audits are submitted.</p>

    <template v-else>

      <!-- Row 1: Radar + Donut -->
      <div class="charts-row-2">
        <div class="card chart-card">
          <div class="chart-head">
            <span class="chart-title">Average Score by Section</span>
            <span class="chart-sub">Across all {{ submissions.length }} submissions</span>
          </div>
          <div class="radar-wrap">
            <canvas ref="radarChart"></canvas>
          </div>
        </div>
        <div class="card chart-card">
          <div class="chart-head">
            <span class="chart-title">Maturity Level Breakdown</span>
            <span class="chart-sub">Portfolio distribution</span>
          </div>
          <div class="donut-wrap">
            <canvas ref="donutChart"></canvas>
          </div>
          <div class="donut-legend">
            <div v-for="(item, i) in levelLegend" :key="i" class="legend-item">
              <span class="legend-dot" :style="{ background: item.color }"></span>
              <span class="legend-label">{{ item.label }}</span>
              <span class="legend-val">{{ item.count }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Row 2: Section bar chart -->
      <div class="card chart-card-full">
        <div class="chart-head">
          <span class="chart-title">Section Scores — Weakest to Strongest</span>
          <span class="chart-sub">Average score out of 20 per section</span>
        </div>
        <canvas ref="barChart" height="100"></canvas>
      </div>

      <!-- Row 3: Score trend -->
      <div class="card chart-card-full">
        <div class="chart-head">
          <span class="chart-title">Average Score Trend</span>
          <span class="chart-sub">Monthly average overall score</span>
        </div>
        <canvas ref="trendChart" height="100"></canvas>
      </div>

      <!-- Row 4: Top & bottom orgs -->
      <div class="charts-row-2">
        <div class="card">
          <div class="chart-head">
            <span class="chart-title">Top Performing Organisations</span>
            <span class="chart-sub">Highest overall score</span>
          </div>
          <div class="rank-list">
            <div v-for="(s, i) in topOrgs" :key="s.id" class="rank-row" @click="$router.push(`/admin/submissions/${s.id}`)">
              <span class="rank-num">{{ i + 1 }}</span>
              <div class="rank-info">
                <div class="rank-name">{{ s.company_name }}</div>
                <div class="rank-meta">{{ s.name }}</div>
              </div>
              <div class="rank-score-bar">
                <div class="rank-bar-fill" :style="{ width: (parseFloat(s.overall_avg) / 20 * 100) + '%' }"></div>
              </div>
              <span class="rank-score">{{ s.overall_avg }}/20</span>
            </div>
          </div>
        </div>
        <div class="card">
          <div class="chart-head">
            <span class="chart-title">Needs Most Support</span>
            <span class="chart-sub">Lowest overall score</span>
          </div>
          <div class="rank-list">
            <div v-for="(s, i) in bottomOrgs" :key="s.id" class="rank-row" @click="$router.push(`/admin/submissions/${s.id}`)">
              <span class="rank-num low">{{ i + 1 }}</span>
              <div class="rank-info">
                <div class="rank-name">{{ s.company_name }}</div>
                <div class="rank-meta">{{ s.name }}</div>
              </div>
              <div class="rank-score-bar">
                <div class="rank-bar-fill low" :style="{ width: (parseFloat(s.overall_avg) / 20 * 100) + '%' }"></div>
              </div>
              <span class="rank-score">{{ s.overall_avg }}/20</span>
            </div>
          </div>
        </div>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from "vue";
import { Chart, registerables } from "chart.js";
import { getSubmissions } from "../api";
import { getISTMonthKey } from "../utils/datetime";

Chart.register(...registerables);

const loading = ref(true);
const submissions = ref([]);

const radarChart = ref(null);
const donutChart = ref(null);
const barChart   = ref(null);
const trendChart = ref(null);

const SECTIONS = [
  { key: "lc_score", label: "Leadership" },
  { key: "ro_score", label: "Recruitment" },
  { key: "we_score", label: "Workplace" },
  { key: "be_score", label: "Sensory" },
  { key: "tm_score", label: "Talent" },
  { key: "ca_score", label: "Comms" },
  { key: "pc_score", label: "Products" },
  { key: "sp_score", label: "Suppliers" },
];

const LEVEL_COLORS = {
  "1": "#E2DDD4",
  "2": "#E2E8F0",
  "3": "#CBD5E1",
  "4": "#161057",
};

const levelLegend = ref([]);

const topOrgs = computed(() =>
  [...submissions.value].sort((a, b) => parseFloat(b.overall_avg) - parseFloat(a.overall_avg)).slice(0, 5)
);
const bottomOrgs = computed(() =>
  [...submissions.value].sort((a, b) => parseFloat(a.overall_avg) - parseFloat(b.overall_avg)).slice(0, 5)
);

onMounted(async () => {
  try {
    const subs = await getSubmissions();
    submissions.value = subs;
    if (!subs.length) { loading.value = false; return; }

    // Wait for v-else template to render canvas elements
    loading.value = false;
    await nextTick();

    // Section averages — scores are out of 20 (5 questions × 4 points max)
    const sectionAvgs = SECTIONS.map(s => {
      const vals = subs.map(sub => parseFloat(sub[s.key] || 0));
      return vals.length ? (vals.reduce((a, b) => a + b, 0) / vals.length).toFixed(1) : 0;
    });

    // Sort sections for bar chart (weakest first)
    const sorted = SECTIONS.map((s, i) => ({ label: s.label, avg: parseFloat(sectionAvgs[i]) }))
      .sort((a, b) => a.avg - b.avg);
    // Level counts
    const levelCounts = { "1": 0, "2": 0, "3": 0, "4": 0 };
    subs.forEach(s => {
      const lvl = (s.overall_level || "").match(/\d/)?.[0];
      if (lvl && levelCounts[lvl] !== undefined) levelCounts[lvl]++;
    });
    levelLegend.value = [
      { label: "Level 1 — Foundational", color: LEVEL_COLORS["1"], count: levelCounts["1"] },
      { label: "Level 2 — Early Progress", color: LEVEL_COLORS["2"], count: levelCounts["2"] },
      { label: "Level 3 — Developing",    color: LEVEL_COLORS["3"], count: levelCounts["3"] },
      { label: "Level 4 — Leading",       color: LEVEL_COLORS["4"], count: levelCounts["4"] },
    ];

    // Monthly trend (grouped by IST calendar month)
    const monthData = {};
    subs.forEach(s => {
      const { key, label } = getISTMonthKey(s.submitted_at);
      if (!monthData[key]) monthData[key] = { label, scores: [] };
      monthData[key].scores.push(parseFloat(s.overall_avg || 0));
    });
    const trendEntries = Object.values(monthData).slice(-8);
    const trendLabels = trendEntries.map(e => e.label);
    const trendData   = trendEntries.map(e => (e.scores.reduce((a, b) => a + b, 0) / e.scores.length).toFixed(1));

    // Draw radar
    new Chart(radarChart.value, {
      type: "radar",
      data: {
        labels: SECTIONS.map(s => s.label),
        datasets: [{
          data: sectionAvgs,
          backgroundColor: "rgba(226,232,240,0.4)",
          borderColor: "#161057",
          borderWidth: 2,
          pointBackgroundColor: "#161057",
          pointBorderColor: "#161057",
          pointRadius: 4,
        }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          r: {
            min: 0, max: 20,
            ticks: { stepSize: 5, color: "#aaa", font: { size: 10 } },
            grid: { color: "#E2DDD4" },
            pointLabels: { color: "#161057", font: { size: 11, weight: "600" } },
          },
        },
      },
    });

    // Draw donut
    new Chart(donutChart.value, {
      type: "doughnut",
      data: {
        labels: ["Level 1", "Level 2", "Level 3", "Level 4"],
        datasets: [{
          data: [levelCounts["1"], levelCounts["2"], levelCounts["3"], levelCounts["4"]],
          backgroundColor: Object.values(LEVEL_COLORS),
          borderWidth: 2,
          borderColor: "#fff",
        }],
      },
      options: {
        cutout: "65%",
        plugins: { legend: { display: false } },
      },
    });

    // Draw bar (sorted weakest to strongest)
    new Chart(barChart.value, {
      type: "bar",
      data: {
        labels: sorted.map(s => s.label),
        datasets: [{
          data: sorted.map(s => s.avg),
          backgroundColor: sorted.map(s =>
            s.avg < 8 ? "#FFF0F0" : s.avg < 14 ? "#E2E8F0" : "#4A5A89"
          ),
          borderColor: "#161057",
          borderWidth: 1.5,
          borderRadius: 8,
        }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          y: { min: 0, max: 20, grid: { color: "#f0f0f0" }, ticks: { color: "#aaa" } },
          x: { grid: { display: false }, ticks: { color: "#555", font: { weight: "600" } } },
        },
      },
    });

    // Draw trend
    new Chart(trendChart.value, {
      type: "line",
      data: {
        labels: trendLabels,
        datasets: [{
          data: trendData,
          borderColor: "#161057",
          backgroundColor: "rgba(226,232,240,0.4)",
          fill: true, tension: 0.4, pointRadius: 5,
          pointBackgroundColor: "#161057",
          pointBorderColor: "#161057",
          pointBorderWidth: 2,
        }],
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          y: { min: 0, max: 20, grid: { color: "#f0f0f0" }, ticks: { color: "#aaa" } },
          x: { grid: { display: false }, ticks: { color: "#aaa" } },
        },
      },
    });

  } catch (e) {
    console.error(e);
    loading.value = false;
  }
});
</script>

<style scoped>
.page-header { margin-bottom: 1.75rem; }
.page-header h1 { font-size: 2rem; font-weight: 800; color: var(--c-primary-dark); letter-spacing: -0.03em; font-family: 'Fraunces', serif; }
.page-header p  { color: #888; font-size: 0.875rem; margin-top: 0.3rem; }
.loading { color: #aaa; padding: 3rem; text-align: center; font-size: 0.9rem; }

.charts-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }
.chart-card { padding: 1.5rem; }
.chart-card-full { padding: 1.5rem; margin-bottom: 1rem; }

.chart-head { margin-bottom: 1.25rem; }
.chart-title { display: block; font-size: 0.95rem; font-weight: 800; color: var(--c-primary-dark); font-family: 'Fraunces', serif; }
.chart-sub { display: block; font-size: 0.78rem; color: #aaa; margin-top: 0.2rem; }

.radar-wrap { max-width: 340px; margin: 0 auto; }
.donut-wrap { max-width: 200px; margin: 0 auto 1rem; }

.donut-legend { display: flex; flex-direction: column; gap: 0.4rem; }
.legend-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; border: 1px solid #ddd; }
.legend-label { flex: 1; color: #555; }
.legend-val { font-weight: 700; color: var(--c-primary-dark); }

/* Rank lists */
.rank-list { display: flex; flex-direction: column; gap: 0.6rem; }
.rank-row { display: flex; align-items: center; gap: 0.75rem; cursor: pointer; padding: 0.4rem 0.25rem; border-radius: 8px; transition: background 0.15s; }
.rank-row:hover { background: var(--c-bg); }
.rank-num { width: 22px; height: 22px; border-radius: 50%; background: var(--c-primary-dark); color: var(--c-accent); font-size: 0.7rem; font-weight: 800; display: grid; place-items: center; flex-shrink: 0; }
.rank-num.low { background: #FFF0F0; color: #C0392B; }
.rank-info { flex: 1; min-width: 0; }
.rank-name { font-size: 0.85rem; font-weight: 700; color: var(--c-primary-dark); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rank-meta { font-size: 0.72rem; color: #aaa; }
.rank-score-bar { width: 60px; height: 6px; background: #E2DDD4; border-radius: 99px; overflow: hidden; flex-shrink: 0; }
.rank-bar-fill { height: 100%; background: var(--c-primary-dark); border-radius: 99px; }
.rank-bar-fill.low { background: #C0392B; }
.rank-score { font-size: 0.78rem; font-weight: 700; color: var(--c-primary-dark); white-space: nowrap; }

@media (max-width: 900px) {
  .charts-row-2 { grid-template-columns: 1fr; }
}
</style>
