<template>
  <div class="super-dashboard-container">
    <!-- Header with Breadcrumbs, Live Status & Manual Refresh -->
    <header class="dash-header">
      <div class="dash-title-block">
        <div class="super-badge-row">
          <span class="super-badge">Super Admin Fleet</span>
          <span class="status-indicator-pill" :class="{ 'polling-active': isTabVisible, 'polling-paused': !isTabVisible }">
            <span class="pulse-dot"></span>
            {{ isTabVisible ? 'Auto-refresh active (2m)' : 'Polling paused (Tab hidden)' }}
          </span>
        </div>
        <h1 class="dash-title">Super Admin Operations Dashboard</h1>
        <p class="dash-subtitle">
          Real-time request ingestion queue, processing latency benchmarks, and background worker fleet status.
        </p>
      </div>

      <div class="dash-actions">
        <div class="last-updated-text" v-if="lastUpdated">
          <span>Last updated:</span>
          <strong>{{ lastUpdatedFormatted }}</strong>
          <span class="cache-pill" title="Aggregations are cached for 2 minutes to protect database load">Cached (2m)</span>
        </div>

        <button
          type="button"
          class="btn-refresh"
          :disabled="loading"
          @click="fetchDashboard(true)"
          title="Force refresh current statistics"
        >
          <svg class="refresh-icon" :class="{ spinning: loading }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
          </svg>
          <span>{{ loading ? 'Refreshing…' : 'Refresh Now' }}</span>
        </button>
      </div>
    </header>

    <!-- Error Banner -->
    <div v-if="error" class="alert-banner alert-error">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      <div class="alert-content">
        <strong>Failed to load operations dashboard:</strong> {{ error }}
      </div>
      <button class="btn-retry" @click="fetchDashboard(true)">Retry</button>
    </div>

    <!-- MAIN CONTENT -->
    <main v-if="stats" class="dash-body">
      <!-- 1. HIGHLIGHT: PENDING REQUESTS HERO BANNER -->
      <section class="pending-hero-card" :class="{ 'has-pending': pendingCount > 0, 'queue-clear': pendingCount === 0 }">
        <div class="hero-left">
          <div class="hero-icon-wrap">
            <svg v-if="pendingCount > 0" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            <svg v-else width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
          </div>
          <div class="hero-meta">
            <span class="hero-tag">{{ pendingCount > 0 ? 'Queue Ingestion Alert' : 'Queue Health Nominal' }}</span>
            <div class="hero-count-row">
              <span class="hero-big-num">{{ pendingCount }}</span>
              <span class="hero-label">Pending Requests Awaiting Processing</span>
            </div>
            <p class="hero-desc" v-if="pendingCount > 0">
              {{ pendingCount }} submission{{ pendingCount === 1 ? '' : 's' }} currently in queue.
              <span v-if="stats.analytics?.oldest_pending_request">
                Oldest request has been waiting for
                <strong>{{ stats.analytics.oldest_pending_request.waiting_time_formatted }}</strong>
                (ID: <code>{{ stats.analytics.oldest_pending_request.submission_id.substring(0, 8) }}…</code>).
              </span>
            </p>
            <p class="hero-desc" v-else>
              Ingestion queue is clear. All incoming respondent submissions have been ingested and processed into final scores.
            </p>
          </div>
        </div>

        <div class="hero-right">
          <div class="hero-stat-pill">
            <span class="pill-label">Total Ingested</span>
            <span class="pill-val">{{ stats.request_overview?.total_requests || 0 }}</span>
          </div>
          <div class="hero-stat-pill" v-if="stats.analytics?.oldest_pending_request">
            <span class="pill-label">Max Queue Wait</span>
            <span class="pill-val text-amber">{{ stats.analytics.oldest_pending_request.waiting_time_formatted }}</span>
          </div>
        </div>
      </section>

      <!-- 1b. REQUEST OVERVIEW METRIC TILES -->
      <section class="section-block">
        <h2 class="section-title">Request Overview</h2>
        <div class="metrics-grid">
          <!-- Pending Tile -->
          <div class="metric-card metric-pending">
            <div class="metric-header">
              <span class="metric-title">Pending</span>
              <span class="metric-badge badge-amber">Received</span>
            </div>
            <div class="metric-value text-amber">{{ stats.request_overview?.pending || 0 }}</div>
            <div class="metric-subtext">Waiting in raw queue</div>
          </div>

          <!-- In Progress Tile -->
          <div class="metric-card metric-progress">
            <div class="metric-header">
              <span class="metric-title">In Progress</span>
              <span class="metric-badge badge-blue">Processing</span>
            </div>
            <div class="metric-value text-blue">{{ stats.request_overview?.in_progress || 0 }}</div>
            <div class="metric-subtext">Worker jobs active</div>
          </div>

          <!-- Completed Tile -->
          <div class="metric-card metric-completed">
            <div class="metric-header">
              <span class="metric-title">Completed</span>
              <span class="metric-badge badge-green">Scored &amp; Linked</span>
            </div>
            <div class="metric-value text-green">{{ stats.request_overview?.completed || 0 }}</div>
            <div class="metric-subtext">Successfully finalized</div>
          </div>

          <!-- Failed / DLQ Tile -->
          <div class="metric-card metric-failed">
            <div class="metric-header">
              <span class="metric-title">Failed / Dead-Letter</span>
              <span class="metric-badge" :class="failedCount > 0 ? 'badge-red' : 'badge-slate'">
                {{ failedCount > 0 ? 'Needs Attention' : 'Zero' }}
              </span>
            </div>
            <div class="metric-value" :class="failedCount > 0 ? 'text-red' : 'text-slate'">{{ failedCount }}</div>
            <div class="metric-subtext">{{ failedCount > 0 ? 'Exceeded retries' : 'Clean pipeline' }}</div>
          </div>
        </div>
      </section>

      <!-- 2. REQUEST ANALYTICS -->
      <section class="section-block">
        <div class="section-header-row">
          <div>
            <h2 class="section-title">Request Analytics &amp; Throughput</h2>
            <p class="section-subtitle">Real-time throughput trends, pipeline success rates, and latency measurements.</p>
          </div>

          <!-- Timeline interval switch -->
          <div class="tab-pill-group">
            <button
              type="button"
              class="tab-pill"
              :class="{ active: timelineMode === '24h' }"
              @click="timelineMode = '24h'"
            >
              Last 24 Hours (Hourly)
            </button>
            <button
              type="button"
              class="tab-pill"
              :class="{ active: timelineMode === '7d' }"
              @click="timelineMode = '7d'"
            >
              Last 7 Days (Daily)
            </button>
          </div>
        </div>

        <!-- 3 KPI Cards for Analytics -->
        <div class="analytics-kpi-grid">
          <div class="kpi-card">
            <div class="kpi-icon-row">
              <div class="kpi-icon icon-emerald">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
              </div>
              <span class="kpi-label">Success Rate</span>
            </div>
            <div class="kpi-value-row">
              <span class="kpi-value">{{ stats.analytics?.success_rate || 0 }}%</span>
              <span class="kpi-rate-bar-wrap">
                <span class="kpi-rate-bar" :style="{ width: (stats.analytics?.success_rate || 0) + '%' }"></span>
              </span>
            </div>
            <div class="kpi-subtext">
              Failure rate: <strong>{{ stats.analytics?.failure_rate || 0 }}%</strong>
            </div>
          </div>

          <div class="kpi-card">
            <div class="kpi-icon-row">
              <div class="kpi-icon icon-blue">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              </div>
              <span class="kpi-label">Avg. Processing Time</span>
            </div>
            <div class="kpi-value-row">
              <span class="kpi-value">{{ stats.analytics?.average_processing_time_formatted || '0s' }}</span>
            </div>
            <div class="kpi-subtext">
              Across completed audits (past 7 days)
            </div>
          </div>

          <div class="kpi-card">
            <div class="kpi-icon-row">
              <div class="kpi-icon icon-amber">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              </div>
              <span class="kpi-label">Oldest Pending Request</span>
            </div>
            <div class="kpi-value-row">
              <span class="kpi-value" :class="stats.analytics?.oldest_pending_request ? 'text-amber' : 'text-slate'">
                {{ stats.analytics?.oldest_pending_request ? stats.analytics.oldest_pending_request.waiting_time_formatted : 'None' }}
              </span>
            </div>
            <div class="kpi-subtext" v-if="stats.analytics?.oldest_pending_request">
              Arrived {{ formatTime(stats.analytics.oldest_pending_request.created_at) }}
            </div>
            <div class="kpi-subtext" v-else>
              No pending jobs delayed in queue
            </div>
          </div>
        </div>

        <!-- Throughput Chart Block -->
        <div class="chart-container-card">
          <div class="chart-header">
            <h3 class="chart-title">
              {{ timelineMode === '24h' ? 'Hourly Ingestion Volume (Last 24 Hours)' : 'Daily Ingestion Volume (Last 7 Days)' }}
            </h3>
            <span class="chart-badge">{{ currentTimelineData.length }} Data Points</span>
          </div>

          <div v-if="currentTimelineData.length" class="chart-bars-wrap">
            <div class="bar-column" v-for="(item, idx) in currentTimelineData" :key="idx">
              <div class="bar-fill-track">
                <div
                  class="bar-fill"
                  :style="{ height: getBarHeight(item.count) }"
                  :title="`${item.bucket}: ${item.count} submissions`"
                >
                  <span class="bar-tooltip">{{ item.count }}</span>
                </div>
              </div>
              <span class="bar-x-label">{{ item.label }}</span>
            </div>
          </div>
          <div v-else class="chart-empty-state">
            <p>No submission volume recorded during this interval.</p>
          </div>
        </div>
      </section>

      <!-- 3. WORKER PROGRESS & FLEET MONITORING -->
      <section class="section-block">
        <div class="section-header-row">
          <div>
            <h2 class="section-title">Background Worker Fleet Progress</h2>
            <p class="section-subtitle">
              Active processes, task state, and heartbeat health. Workers are automatically marked <strong>Offline</strong> if no heartbeat is received within 3 minutes.
            </p>
          </div>

          <!-- Fleet Counter Pills -->
          <div class="fleet-summary-strip">
            <div class="fleet-pill pill-total">
              <span class="fp-dot"></span>
              <span>Total: <strong>{{ stats.worker_progress?.total_workers || 0 }}</strong></span>
            </div>
            <div class="fleet-pill pill-active">
              <span class="fp-dot dot-active"></span>
              <span>Active: <strong>{{ stats.worker_progress?.active_workers || 0 }}</strong></span>
            </div>
            <div class="fleet-pill pill-idle">
              <span class="fp-dot dot-idle"></span>
              <span>Idle: <strong>{{ stats.worker_progress?.idle_workers || 0 }}</strong></span>
            </div>
            <div class="fleet-pill pill-offline">
              <span class="fp-dot dot-offline"></span>
              <span>Offline: <strong>{{ stats.worker_progress?.offline_workers || 0 }}</strong></span>
            </div>
          </div>
        </div>

        <!-- Worker Table -->
        <div class="table-card">
          <table class="worker-table" v-if="stats.worker_progress?.workers?.length">
            <thead>
              <tr>
                <th>Status</th>
                <th>Worker ID</th>
                <th>Type</th>
                <th>Current Task</th>
                <th>Jobs Completed</th>
                <th>Last Heartbeat</th>
                <th>Started</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="w in stats.worker_progress.workers" :key="w.worker_id">
                <td>
                  <span
                    class="status-tag"
                    :class="{
                      'tag-active': w.status === 'active',
                      'tag-idle': w.status === 'idle',
                      'tag-offline': w.status === 'offline'
                    }"
                  >
                    <span class="tag-dot"></span>
                    {{ w.status === 'offline' ? 'Offline (>3m)' : (w.status === 'active' ? 'Active' : 'Idle') }}
                  </span>
                </td>
                <td>
                  <strong class="worker-id-code">{{ w.worker_id }}</strong>
                </td>
                <td>
                  <span class="worker-type-badge">{{ w.worker_type }}</span>
                </td>
                <td>
                  <span class="worker-task-text" :title="w.current_task">{{ w.current_task }}</span>
                </td>
                <td>
                  <span class="worker-jobs-num">{{ w.jobs_completed }}</span>
                </td>
                <td>
                  <span class="heartbeat-badge" :class="{ 'hb-stale': w.status === 'offline' }">
                    {{ w.last_heartbeat_formatted }}
                  </span>
                </td>
                <td class="worker-date-col">
                  {{ formatTime(w.started_at) }}
                </td>
              </tr>
            </tbody>
          </table>

          <div v-else class="workers-empty-box">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
              <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
              <line x1="6" y1="6" x2="6.01" y2="6"></line>
              <line x1="6" y1="18" x2="6.01" y2="18"></line>
            </svg>
            <h3>No Active Background Workers Registered</h3>
            <p>
              Workers update the fleet directory on their 30–60 second heartbeat schedule. When background worker daemons or outbox pollers are started, they will populate here automatically.
            </p>
          </div>
        </div>
      </section>
    </main>

    <!-- Initial Loading State -->
    <div v-else class="initial-loading-wrap">
      <div class="loading-spinner"></div>
      <p>Loading Super Admin Operations Snapshot…</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { getSuperAdminDashboard } from '../api';

const stats = ref(null);
const loading = ref(false);
const error = ref(null);
const lastUpdated = ref(null);
const isTabVisible = ref(true);
const timelineMode = ref('24h');

let pollIntervalId = null;
let lastFetchTimestamp = 0;

// Computed metrics
const pendingCount = computed(() => stats.value?.request_overview?.pending || 0);
const failedCount = computed(() => stats.value?.request_overview?.failed || 0);

const lastUpdatedFormatted = computed(() => {
  if (!lastUpdated.value) return 'Never';
  return new Date(lastUpdated.value).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
});

const currentTimelineData = computed(() => {
  if (!stats.value?.analytics) return [];
  return timelineMode.value === '24h'
    ? stats.value.analytics.hourly_timeline_24h || []
    : stats.value.analytics.daily_timeline_7d || [];
});

const maxTimelineCount = computed(() => {
  const data = currentTimelineData.value;
  if (!data.length) return 1;
  const max = Math.max(...data.map(d => d.count || 0));
  return max > 0 ? max : 1;
});

function getBarHeight(count) {
  if (!count) return '6px';
  const pct = Math.max(8, Math.round((count / maxTimelineCount.value) * 100));
  return `${pct}%`;
}

function formatTime(isoString) {
  if (!isoString) return '—';
  try {
    const d = new Date(isoString);
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' }) + ' ' +
           d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return isoString;
  }
}

// Fetch dashboard data
async function fetchDashboard(forceRefresh = false) {
  if (loading.value) return;
  loading.value = true;
  error.value = null;

  try {
    const data = await getSuperAdminDashboard(forceRefresh);
    stats.value = data;
    lastUpdated.value = data.timestamp || new Date().toISOString();
    lastFetchTimestamp = Date.now();
  } catch (err) {
    console.error('Error fetching Super Admin Dashboard:', err);
    error.value = err.message || 'Failed to communicate with operations API';
  } finally {
    loading.value = false;
  }
}

// Requirement 4: Auto-refresh every 2 minutes (120,000 ms) + Tab visibility detection
function startPolling() {
  stopPolling();
  pollIntervalId = setInterval(() => {
    if (document.visibilityState === 'visible') {
      fetchDashboard(false);
    }
  }, 120000); // 2 minutes
}

function stopPolling() {
  if (pollIntervalId) {
    clearInterval(pollIntervalId);
    pollIntervalId = null;
  }
}

function handleVisibilityChange() {
  const visible = document.visibilityState === 'visible';
  isTabVisible.value = visible;

  if (visible) {
    // Tab resumed: if more than 2 minutes have elapsed since last fetch, refresh immediately
    const elapsed = Date.now() - lastFetchTimestamp;
    if (elapsed >= 120000) {
      fetchDashboard(false);
    }
    startPolling();
  } else {
    // Tab hidden: pause polling to save resources
    stopPolling();
  }
}

onMounted(() => {
  // Ensure user is Super Admin
  const role = sessionStorage.getItem('nd_role');
  if (role !== 'super') {
    error.value = 'Super administrator privileges required to access this dashboard.';
    return;
  }

  fetchDashboard(false);
  document.addEventListener('visibilitychange', handleVisibilityChange);
  startPolling();
});

onUnmounted(() => {
  stopPolling();
  document.removeEventListener('visibilitychange', handleVisibilityChange);
});
</script>

<style scoped>
.super-dashboard-container {
  max-width: 1320px;
  margin: 0 auto;
  padding: 28px 24px 60px;
  color: #0f172a;
  font-family: inherit;
}

/* Header */
.dash-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 20px;
  flex-wrap: wrap;
}

.super-badge-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.super-badge {
  background: #0f172a;
  color: #38bdf8;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  padding: 3px 10px;
  border-radius: 9999px;
  border: 1px solid rgba(56, 189, 248, 0.3);
}

.status-indicator-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 9999px;
  background: #f1f5f9;
  color: #475569;
}

.status-indicator-pill.polling-active {
  background: #ecfdf5;
  color: #065f46;
}

.status-indicator-pill.polling-paused {
  background: #fef3c7;
  color: #92400e;
}

.pulse-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.9); }
  100% { opacity: 1; transform: scale(1); }
}

.dash-title {
  font-size: 1.75rem;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 6px 0;
  letter-spacing: -0.02em;
}

.dash-subtitle {
  font-size: 0.92rem;
  color: #64748b;
  margin: 0;
  max-width: 680px;
  line-height: 1.45;
}

.dash-actions {
  display: flex;
  align-items: center;
  gap: 14px;
}

.last-updated-text {
  font-size: 0.8rem;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 6px;
}

.cache-pill {
  font-size: 0.68rem;
  font-weight: 600;
  background: #e2e8f0;
  color: #334155;
  padding: 2px 7px;
  border-radius: 6px;
}

.btn-refresh {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #0f172a;
  color: #ffffff;
  border: none;
  font-size: 0.84rem;
  font-weight: 600;
  padding: 9px 18px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.btn-refresh:hover:not(:disabled) {
  background: #1e293b;
  transform: translateY(-1px);
}

.btn-refresh:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.refresh-icon.spinning {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

/* Alert Banner */
.alert-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border-radius: 10px;
  margin-bottom: 24px;
}

.alert-error {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

.alert-content {
  flex: 1;
  font-size: 0.88rem;
}

.btn-retry {
  background: #991b1b;
  color: #fff;
  border: none;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
}

/* Pending Hero Banner */
.pending-hero-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px;
  border-radius: 14px;
  margin-bottom: 28px;
  transition: all 0.2s ease;
  flex-wrap: wrap;
  gap: 20px;
}

.pending-hero-card.has-pending {
  background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
  border: 1.5px solid #fde68a;
  box-shadow: 0 4px 14px rgba(217, 119, 6, 0.08);
}

.pending-hero-card.has-pending .hero-icon-wrap {
  background: #f59e0b;
  color: #ffffff;
}

.pending-hero-card.queue-clear {
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  border: 1.5px solid #bbf7d0;
  box-shadow: 0 4px 14px rgba(16, 185, 129, 0.06);
}

.pending-hero-card.queue-clear .hero-icon-wrap {
  background: #10b981;
  color: #ffffff;
}

.hero-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.hero-icon-wrap {
  width: 58px;
  height: 58px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hero-tag {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #92400e;
}

.pending-hero-card.queue-clear .hero-tag {
  color: #065f46;
}

.hero-count-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin: 3px 0 4px;
}

.hero-big-num {
  font-size: 2.4rem;
  font-weight: 900;
  line-height: 1;
  color: #0f172a;
}

.hero-label {
  font-size: 1.05rem;
  font-weight: 700;
  color: #1e293b;
}

.hero-desc {
  font-size: 0.85rem;
  color: #475569;
  margin: 0;
  line-height: 1.4;
}

.hero-desc code {
  background: rgba(255, 255, 255, 0.8);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.82rem;
}

.hero-right {
  display: flex;
  gap: 12px;
}

.hero-stat-pill {
  background: #ffffff;
  padding: 10px 18px;
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.pill-label {
  font-size: 0.72rem;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
}

.pill-val {
  font-size: 1.25rem;
  font-weight: 800;
  color: #0f172a;
}

/* Sections */
.section-block {
  margin-bottom: 32px;
}

.section-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 16px;
  gap: 16px;
  flex-wrap: wrap;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0 0 4px 0;
}

.section-subtitle {
  font-size: 0.86rem;
  color: #64748b;
  margin: 0;
}

/* Metrics Grid */
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 16px;
}

.metric-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px 22px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.06);
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.metric-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: #475569;
}

.metric-badge {
  font-size: 0.68rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  text-transform: uppercase;
}

.badge-amber { background: #fef3c7; color: #b45309; }
.badge-blue { background: #e0f2fe; color: #0369a1; }
.badge-green { background: #dcfce7; color: #15803d; }
.badge-red { background: #fee2e2; color: #b91c1c; }
.badge-slate { background: #f1f5f9; color: #64748b; }

.metric-value {
  font-size: 2.1rem;
  font-weight: 800;
  line-height: 1.1;
  margin-bottom: 6px;
}

.text-amber { color: #d97706; }
.text-blue { color: #0284c7; }
.text-green { color: #16a34a; }
.text-red { color: #dc2626; }
.text-slate { color: #475569; }

.metric-subtext {
  font-size: 0.78rem;
  color: #94a3b8;
}

/* Analytics KPIs */
.analytics-kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.kpi-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
}

.kpi-icon-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.kpi-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-emerald { background: #d1fae5; color: #059669; }
.icon-blue { background: #e0f2fe; color: #0284c7; }
.icon-amber { background: #fef3c7; color: #d97706; }

.kpi-label {
  font-size: 0.82rem;
  font-weight: 600;
  color: #475569;
}

.kpi-value-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 1.7rem;
  font-weight: 800;
  color: #0f172a;
}

.kpi-rate-bar-wrap {
  flex: 1;
  height: 8px;
  background: #fee2e2;
  border-radius: 4px;
  overflow: hidden;
}

.kpi-rate-bar {
  display: block;
  height: 100%;
  background: #10b981;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.kpi-subtext {
  font-size: 0.78rem;
  color: #64748b;
}

/* Tab Pills */
.tab-pill-group {
  display: inline-flex;
  background: #f1f5f9;
  padding: 3px;
  border-radius: 8px;
}

.tab-pill {
  border: none;
  background: transparent;
  color: #64748b;
  font-size: 0.78rem;
  font-weight: 600;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.tab-pill.active {
  background: #ffffff;
  color: #0f172a;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

/* Throughput Chart */
.chart-container-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 22px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.chart-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0;
}

.chart-badge {
  font-size: 0.72rem;
  background: #f1f5f9;
  color: #475569;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 6px;
}

.chart-bars-wrap {
  display: flex;
  align-items: flex-end;
  height: 180px;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.bar-column {
  flex: 1;
  min-width: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.bar-fill-track {
  width: 100%;
  max-width: 28px;
  height: 150px;
  display: flex;
  align-items: flex-end;
  background: #f8fafc;
  border-radius: 6px 6px 0 0;
}

.bar-fill {
  width: 100%;
  background: linear-gradient(180deg, #38bdf8 0%, #0284c7 100%);
  border-radius: 6px 6px 0 0;
  position: relative;
  transition: height 0.3s ease;
}

.bar-fill:hover {
  background: linear-gradient(180deg, #0ea5e9 0%, #0369a1 100%);
}

.bar-tooltip {
  display: none;
  position: absolute;
  top: -26px;
  left: 50%;
  transform: translateX(-50%);
  background: #0f172a;
  color: #ffffff;
  font-size: 0.68rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
}

.bar-fill:hover .bar-tooltip {
  display: block;
}

.bar-x-label {
  font-size: 0.68rem;
  color: #64748b;
  margin-top: 8px;
  text-align: center;
  white-space: nowrap;
}

.chart-empty-state {
  text-align: center;
  color: #94a3b8;
  padding: 40px 0;
  font-size: 0.9rem;
}

/* Worker Fleet Summary */
.fleet-summary-strip {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.fleet-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.78rem;
  padding: 5px 12px;
  border-radius: 9999px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
}

.fp-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #94a3b8;
}

.dot-active { background: #10b981; }
.dot-idle { background: #0284c7; }
.dot-offline { background: #ef4444; }

/* Worker Table */
.table-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
}

.worker-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.84rem;
}

.worker-table th {
  background: #f8fafc;
  color: #475569;
  font-weight: 600;
  padding: 12px 18px;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.worker-table td {
  padding: 14px 18px;
  border-bottom: 1px solid #f1f5f9;
  color: #1e293b;
  vertical-align: middle;
}

.worker-table tr:last-child td {
  border-bottom: none;
}

.status-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 9999px;
}

.tag-active {
  background: #dcfce7;
  color: #15803d;
}

.tag-idle {
  background: #e0f2fe;
  color: #0369a1;
}

.tag-offline {
  background: #fee2e2;
  color: #b91c1c;
}

.tag-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.worker-id-code {
  font-family: monospace;
  font-size: 0.82rem;
  color: #0f172a;
}

.worker-type-badge {
  font-size: 0.72rem;
  font-weight: 600;
  background: #f1f5f9;
  color: #475569;
  padding: 3px 8px;
  border-radius: 6px;
}

.worker-task-text {
  max-width: 240px;
  display: inline-block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #334155;
}

.worker-jobs-num {
  font-weight: 700;
  color: #0f172a;
}

.heartbeat-badge {
  font-size: 0.75rem;
  color: #059669;
  font-weight: 600;
}

.heartbeat-badge.hb-stale {
  color: #dc2626;
}

.worker-date-col {
  font-size: 0.75rem;
  color: #64748b;
}

.workers-empty-box {
  padding: 48px 24px;
  text-align: center;
  color: #64748b;
}

.workers-empty-box svg {
  margin-bottom: 12px;
  stroke: #94a3b8;
}

.workers-empty-box h3 {
  font-size: 1.05rem;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 6px 0;
}

.workers-empty-box p {
  font-size: 0.84rem;
  max-width: 520px;
  margin: 0 auto;
  line-height: 1.5;
}

/* Loading Wrap */
.initial-loading-wrap {
  text-align: center;
  padding: 80px 20px;
  color: #64748b;
}

.loading-spinner {
  width: 38px;
  height: 38px;
  border: 3px solid #e2e8f0;
  border-top-color: #0284c7;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 0 auto 16px;
}
</style>
