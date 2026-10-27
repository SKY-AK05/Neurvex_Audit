<template>
  <div class="dashboard-page">
    <!-- Top Brand Navbar matching Reference Standard -->
    <header class="org-topbar">
      <div class="topbar-left">
        <router-link to="/" class="topbar-brand">
          <img src="/logonew1.png" alt="NIWI" class="brand-logo" />
          <span class="brand-name">Neuro-Inclusive<br/>Workplace Index</span>
        </router-link>
      </div>
      <div class="topbar-right">
        <div class="topbar-powered">
          <span class="powered-label">Powered by</span>
          <img src="/logo_orchvate.png" alt="Orchvate" class="powered-logo" />
        </div>
      </div>
    </header>

    <div class="dashboard-content">
      <header class="dashboard-header">
        <div class="header-titles">
          <h1>Organisation Dashboard</h1>
          <p>Maturity score history and reports over time.</p>
        </div>
        <div class="actions">
          <button class="btn-primary-pill" @click="$router.push('/')">Re-Audit Organisation</button>
          <button class="btn-ghost-pill" @click="handleLogout">Logout</button>
        </div>
      </header>

      <div v-if="loading" class="loading">Loading dashboard...</div>
      <div v-else-if="error" class="alert-error">{{ error }}</div>
      <div v-else class="dashboard-grid">
        <!-- Left: Level and Line Chart -->
        <div class="main-card card">
          <div class="level-indicator">
            <span class="section-tag">OVERVIEW</span>
            <h3>Current Maturity Status</h3>
            <div class="status-badge-wrap">
              <span class="badge-status">{{ currentLevel || 'In Progress' }}</span>
              <span class="last-date" v-if="lastAuditDate">Last Audited: {{ fmtDate(lastAuditDate) }}</span>
            </div>
          </div>

          <div class="chart-container">
            <h4>Progress Over Time</h4>
            <!-- Render custom SVG Line Chart -->
            <svg viewBox="0 0 500 200" class="svg-chart" v-if="history.length > 0">
              <!-- Grid Lines -->
              <line x1="40" y1="20" x2="480" y2="20" stroke="rgba(22, 16, 87, 0.06)" />
              <line x1="40" y1="80" x2="480" y2="80" stroke="rgba(22, 16, 87, 0.06)" />
              <line x1="40" y1="140" x2="480" y2="140" stroke="rgba(22, 16, 87, 0.06)" />
              <line x1="40" y1="170" x2="480" y2="170" stroke="rgba(22, 16, 87, 0.12)" stroke-width="1.5" />

              <!-- Y Axis Label -->
              <text x="12" y="24" class="axis-text">20</text>
              <text x="12" y="84" class="axis-text">10</text>
              <text x="12" y="144" class="axis-text">0</text>

              <!-- Line Path -->
              <path :d="chartPath" fill="none" stroke="#161057" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />

              <!-- Plot points -->
              <circle
                v-for="(point, index) in chartPoints"
                :key="index"
                :cx="point.x"
                :cy="point.y"
                r="5"
                fill="#04907C"
                stroke="#FFFFFF"
                stroke-width="2.5"
              />
            </svg>
            <p v-else class="empty-chart">Submit your first audit to see progress over time.</p>
          </div>
        </div>

        <!-- Right: Submissions List -->
        <div class="side-card card">
          <div class="side-header">
            <h3>Audit Submissions</h3>
            <span class="count-badge" v-if="submissions.length">{{ submissions.length }}</span>
          </div>
          <div v-if="submissions.length === 0" class="empty-list">No audits submitted yet.</div>
          <div v-else class="audit-list">
            <div v-for="s in submissions" :key="s.id" class="audit-item">
              <div class="audit-meta">
                <span class="audit-date">{{ fmtDate(s.submitted_at) }}</span>
                <span class="audit-score"><strong>{{ s.overall_avg }}</strong><span class="score-denom">/20</span></span>
              </div>
              <div class="audit-level-badge">{{ s.overall_level }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { formatDate as fmtDate } from "../utils/datetime";

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
.dashboard-page {
  flex: 1;
  min-height: 100vh;
  min-height: 100dvh;
  overflow-y: auto;
  background: var(--bg, #FAFAF8);
  font-family: var(--font-body, 'Geist', 'Inter', sans-serif);
  color: var(--primary, #161057);
  display: flex;
  flex-direction: column;
}

.org-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 2.5rem;
  border-bottom: 1px solid rgba(22, 16, 87, 0.08);
  background: #FFFFFF;
  position: sticky;
  top: 0;
  z-index: 100;
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
}

.topbar-brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
}

.brand-logo {
  height: 32px;
  width: auto;
  border-radius: 6px;
  object-fit: contain;
}

.brand-name {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--primary, #161057);
  line-height: 1.2;
}

.topbar-right {
  display: flex;
  align-items: center;
}

.topbar-powered {
  display: flex;
  align-items: center;
  gap: 0.45rem;
}

.powered-label {
  font-size: 0.6rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #9CA3AF;
}

.powered-logo {
  height: 20px;
  width: auto;
  object-fit: contain;
}

.dashboard-content {
  padding: 2.25rem 2.5rem 4rem;
  max-width: 1240px;
  margin: 0 auto;
  width: 100%;
  box-sizing: border-box;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 2rem;
  flex-wrap: wrap;
  gap: 1.25rem;
}

.header-titles h1 {
  font-family: 'Fraunces', serif;
  font-size: 2rem;
  font-weight: 800;
  color: var(--primary, #161057);
  letter-spacing: -0.025em;
  margin-bottom: 0.35rem;
}

.header-titles p {
  color: #64748B;
  font-size: 0.95rem;
}

.actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.btn-primary-pill {
  background: var(--primary, #161057);
  color: #FFFFFF;
  border: none;
  border-radius: 99px;
  padding: 0.7rem 1.6rem;
  font-size: 0.9rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 0 4px 14px rgba(22, 16, 87, 0.2);
  transition: transform 0.2s, box-shadow 0.2s, background 0.2s;
}

.btn-primary-pill:hover {
  background: #0f0a42;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(22, 16, 87, 0.28);
}

.btn-ghost-pill {
  background: transparent;
  color: #64748B;
  border: 1px solid rgba(22, 16, 87, 0.14);
  border-radius: 99px;
  padding: 0.68rem 1.4rem;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.btn-ghost-pill:hover {
  background: rgba(22, 16, 87, 0.04);
  color: var(--primary, #161057);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
}

.card {
  background: #FFFFFF;
  border: 1px solid rgba(22, 16, 87, 0.08);
  border-radius: 16px;
  padding: 1.75rem;
  box-shadow: 0 2px 12px rgba(22, 16, 87, 0.03);
}

.section-tag {
  display: inline-block;
  background: #CCFBF1;
  color: #0F766E;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 0.2rem 0.55rem;
  border-radius: 99px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 0.5rem;
}

.level-indicator h3 {
  font-family: 'Fraunces', serif;
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--primary, #161057);
  letter-spacing: -0.015em;
  margin-bottom: 0.75rem;
}

.status-badge-wrap {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 1.75rem;
}

.badge-status {
  background: #EDE9FE;
  color: #6D28D9;
  font-size: 0.8rem;
  font-weight: 700;
  padding: 0.35rem 0.85rem;
  border-radius: 99px;
}

.last-date {
  font-size: 0.825rem;
  color: #94A3B8;
}

.chart-container h4 {
  font-family: 'Fraunces', serif;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--primary, #161057);
  margin-bottom: 1rem;
}

.svg-chart {
  width: 100%;
  height: auto;
  background: #FAFAF8;
  border-radius: 12px;
  border: 1px solid rgba(22, 16, 87, 0.06);
  padding: 0.5rem 0;
}

.axis-text {
  font-size: 11px;
  font-weight: 600;
  fill: #94A3B8;
  font-family: var(--font-body, sans-serif);
}

.side-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}

.side-header h3 {
  font-family: 'Fraunces', serif;
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--primary, #161057);
  letter-spacing: -0.015em;
}

.count-badge {
  background: #EDE9FE;
  color: #6D28D9;
  font-size: 0.725rem;
  font-weight: 700;
  padding: 0.2rem 0.55rem;
  border-radius: 99px;
}

.audit-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.audit-item {
  padding: 0.9rem 1.1rem;
  border: 1px solid rgba(22, 16, 87, 0.08);
  border-radius: 12px;
  background: #FAFAF8;
  transition: transform 0.15s, box-shadow 0.15s, background 0.15s;
}

.audit-item:hover {
  background: #FFFFFF;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(22, 16, 87, 0.05);
}

.audit-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.35rem;
}

.audit-date {
  font-size: 0.85rem;
  font-weight: 600;
  color: #1E293B;
}

.audit-score {
  font-size: 0.95rem;
  color: var(--primary, #161057);
}

.score-denom {
  font-size: 0.75rem;
  color: #94A3B8;
}

.audit-level-badge {
  display: inline-block;
  font-size: 0.75rem;
  color: #0F766E;
  background: #CCFBF1;
  padding: 0.15rem 0.55rem;
  border-radius: 99px;
  font-weight: 600;
}

.empty-chart, .empty-list {
  font-size: 0.875rem;
  color: #94A3B8;
  text-align: center;
  padding: 2.5rem 1rem;
}

.loading {
  text-align: center;
  padding: 3rem;
  color: #64748B;
  font-size: 0.95rem;
}

.alert-error {
  background: #FEE2E2;
  color: #991B1B;
  border: 1px solid #FCA5A5;
  padding: 0.85rem 1.25rem;
  border-radius: 10px;
  font-size: 0.9rem;
}

@media (max-width: 900px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  .dashboard-content {
    padding: 1.5rem 1.25rem 3rem;
  }
}
</style>
