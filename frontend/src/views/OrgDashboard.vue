<template>
  <div class="dashboard-page">
    <header class="dashboard-header">
      <div>
        <h1>Dashboard</h1>
        <p>Maturity score history and reports over time.</p>
      </div>
      <div class="actions">
        <button class="btn btn-primary" @click="$router.push('/')">Re-Audit Organisation</button>
        <button class="btn btn-secondary" @click="handleLogout">Logout</button>
      </div>
    </header>

    <div v-if="loading" class="loading">Loading dashboard...</div>
    <div v-else-if="error" class="alert alert-error">{{ error }}</div>
    <div v-else class="dashboard-grid">
      <!-- Left: Level and Line Chart -->
      <div class="main-card card">
        <div class="level-indicator">
          <h3>Current Maturity Status</h3>
          <span class="badge badge-sent">{{ currentLevel }}</span>
          <p class="last-date" v-if="lastAuditDate">Last Audited: {{ fmtDate(lastAuditDate) }}</p>
        </div>

        <div class="chart-container">
          <h4>Progress Over Time</h4>
          <!-- Render custom SVG Line Chart -->
          <svg viewBox="0 0 500 200" class="svg-chart" v-if="history.length > 0">
            <!-- Grid Lines -->
            <line x1="40" y1="20" x2="480" y2="20" stroke="#eee" />
            <line x1="40" y1="80" x2="480" y2="80" stroke="#eee" />
            <line x1="40" y1="140" x2="480" y2="140" stroke="#eee" />
            <line x1="40" y1="170" x2="480" y2="170" stroke="#ccc" stroke-width="2" />

            <!-- Y Axis Label -->
            <text x="10" y="25" class="axis-text">20</text>
            <text x="10" y="85" class="axis-text">10</text>
            <text x="10" y="145" class="axis-text">0</text>

            <!-- Line Path -->
            <path :d="chartPath" fill="none" stroke="var(--c-primary-dark)" stroke-width="3" />

            <!-- Plot points -->
            <circle
              v-for="(point, index) in chartPoints"
              :key="index"
              :cx="point.x"
              :cy="point.y"
              r="5"
              fill="var(--c-accent-retro)"
              stroke="var(--c-primary-dark)"
              stroke-width="2"
            />
          </svg>
          <p v-else class="empty-chart">Submit your first audit to see progress.</p>
        </div>
      </div>

      <!-- Right: Submissions List -->
      <div class="side-card card">
        <h3>Audit Submissions</h3>
        <div v-if="submissions.length === 0" class="empty-list">No audits submitted yet.</div>
        <div v-else class="audit-list">
          <div v-for="s in submissions" :key="s.id" class="audit-item">
            <div class="audit-meta">
              <span class="audit-date">{{ fmtDate(s.submitted_at) }}</span>
              <span class="audit-score"><strong>{{ s.overall_avg }}/20</strong></span>
            </div>
            <div class="audit-level">{{ s.overall_level }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const loading = ref(true);
const error = ref("");
const submissions = ref([]);
const history = ref([]);
const currentLevel = ref("");
const lastAuditDate = ref("");

onMounted(async () => {
  const token = localStorage.getItem("org_token");
  if (!token) {
    error.value = "Unauthorized access. Please log in.";
    loading.value = false;
    return;
  }

  try {
    const API_BASE = import.meta.env.VITE_API_BASE || "/api";
    const res = await fetch(`${API_BASE}/org/dashboard`, {
      headers: { "Authorization": `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Failed to load dashboard data.");
    const data = await res.json();
    submissions.value = data.submissions;
    history.value = data.history;
    currentLevel.value = data.current_level;
    lastAuditDate.value = data.last_audit_date;
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
});

function handleLogout() {
  localStorage.removeItem("org_token");
  localStorage.removeItem("org_name");
  localStorage.removeItem("org_user_email");
  router.push("/org/login");
}

function fmtDate(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

// Convert history points to SVG Coordinates
const chartPoints = computed(() => {
  if (history.value.length === 0) return [];
  const points = [];
  const startX = 50;
  const endX = 470;
  const width = endX - startX;
  const steps = history.value.length;

  history.value.forEach((h, index) => {
    const x = steps > 1 ? startX + (index / (steps - 1)) * width : startX + width / 2;
    // Map score (0-20) to SVG height (170 down to 20)
    const y = 170 - (h.score / 20) * 150;
    points.push({ x, y });
  });
  return points;
});

const chartPath = computed(() => {
  return chartPoints.value.map((p, index) => `${index === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(" ");
});
</script>

<style scoped>
.dashboard-page { padding: 2rem 3rem; background: var(--c-bg); min-height: 100vh; }
.dashboard-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
.dashboard-header h1 { font-family: 'Playfair Display', serif; font-size: 2rem; color: var(--c-primary-dark); }
.actions { display: flex; gap: 0.5rem; }
.dashboard-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem; }
.level-indicator { margin-bottom: 1.5rem; }
.last-date { font-size: 0.8rem; color: #888; margin-top: 0.5rem; }
.chart-container h4 { font-family: 'Playfair Display', serif; margin-bottom: 1rem; }
.svg-chart { width: 100%; height: auto; background: #faf9f6; border-radius: 8px; border: 1.5px solid var(--c-primary-dark); }
.axis-text { font-size: 10px; font-weight: bold; fill: #aaa; }
.audit-list { display: flex; flex-direction: column; gap: 0.75rem; }
.audit-item { padding: 0.75rem 1rem; border: 1.5px solid var(--c-primary-dark); border-radius: 8px; background: #faf9f6; }
.audit-meta { display: flex; justify-content: space-between; margin-bottom: 0.25rem; font-size: 0.85rem; }
.audit-level { font-size: 0.8rem; color: #666; }
.empty-chart, .empty-list { font-size: 0.9rem; color: #888; text-align: center; padding: 2rem; }
</style>
