<template>
  <div class="dashboard-page animate-in super-engine-page">
    <!-- Hero / Title Header Banner matching Overview & Analytics design language -->
    <section class="hero-section" aria-label="Operations Engine Header">
      <div class="hero-content">
        <div class="super-kicker-pill">
          <span class="kicker-tag">Restricted • Super Admin</span>
          <span class="kicker-divider">•</span>
          <span class="kicker-status" :class="{ 'live-on': isTabVisible, 'live-paused': !isTabVisible }">
            <span class="pulse-indicator"></span>
            {{ isTabVisible ? 'Auto-refresh Active (2m)' : 'Polling Paused (Tab Hidden)' }}
          </span>
        </div>

        <h1 class="hero-title">Platform Operations Command</h1>
        <p class="hero-subtitle">
          Real-time ingestion telemetry, processing latency benchmarks, and background worker fleet coordination.
        </p>

        <!-- Top Controls Strip: Cache indicator, Last updated & Manual Refresh Button -->
        <div class="engine-top-controls">
          <div class="control-meta-pill">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            <span>Updated: <strong>{{ lastUpdatedFormatted }}</strong></span>
            <span class="cache-badge" title="Snapshot is cached for 2 minutes to eliminate database overhead">Cached (2m)</span>
          </div>

          <button
            type="button"
            class="hero-search-btn btn-refresh-engine"
            :disabled="loading"
            @click="fetchDashboard(true)"
            title="Force recompute cached operational snapshot"
          >
            <svg class="refresh-spinner" :class="{ spinning: loading }" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3">
              <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
            </svg>
            <span>{{ loading ? 'Recomputing…' : 'Force Refresh' }}</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Error Alert Banner -->
    <div v-if="error" class="alert-banner-error">
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      <div class="alert-text">
        <strong>Operations Error:</strong> {{ error }}
      </div>
      <button class="btn-retry-engine" @click="fetchDashboard(true)">Retry</button>
    </div>

    <!-- MAIN BODY -->
    <main v-if="stats" class="engine-body">
      <!-- 1. HIGHLIGHT: PENDING QUEUE HERO CARD -->
      <section class="card hero-pending-card" :class="{ 'pending-alert': pendingCount > 0, 'pending-clear': pendingCount === 0 }">
        <div class="hpc-left">
          <div class="hpc-icon-box">
            <svg v-if="pendingCount > 0" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            <svg v-else width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22 4 12 14.01 9 11.01"></polyline>
            </svg>
          </div>
          <div class="hpc-text-wrap">
            <div class="hpc-badge-row">
              <span class="hpc-kicker">{{ pendingCount > 0 ? 'INGESTION QUEUE ACTIVE' : 'PIPELINE NOMINAL' }}</span>
              <span v-if="stats.analytics?.oldest_pending_request" class="hpc-wait-pill">
                Max Wait: {{ stats.analytics.oldest_pending_request.waiting_time_formatted }}
              </span>
            </div>
            <div class="hpc-count-row">
              <span class="hpc-big-val">{{ pendingCount }}</span>
              <h2 class="hpc-count-label">Pending Submissions in Ingestion Queue</h2>
            </div>
            <p class="hpc-explanation" v-if="pendingCount > 0">
              {{ pendingCount }} submission{{ pendingCount === 1 ? '' : 's' }} accepted via <code>POST /api/submit</code> awaiting scoring and outbox dispatch.
              <span v-if="stats.analytics?.oldest_pending_request">
                Oldest record waiting: <strong>{{ stats.analytics.oldest_pending_request.waiting_time_formatted }}</strong>
                (ID: <code>{{ stats.analytics.oldest_pending_request.submission_id.substring(0, 8) }}…</code>).
              </span>
            </p>
            <p class="hpc-explanation" v-else>
              Ingestion queue is fully cleared. All incoming audit submissions have been consumed, scored, and linked.
            </p>
          </div>
        </div>

        <div class="hpc-right">
          <div class="hpc-stat-box">
            <span class="hpc-stat-label">Total Ingested</span>
            <span class="hpc-stat-val">{{ stats.request_overview?.total_requests || 0 }}</span>
          </div>
          <div class="hpc-stat-box" v-if="stats.analytics?.average_processing_time_formatted">
            <span class="hpc-stat-label">Avg. Latency</span>
            <span class="hpc-stat-val">{{ stats.analytics.average_processing_time_formatted }}</span>
          </div>
        </div>
      </section>

      <!-- 1b. REQUEST OVERVIEW 4-GRID -->
      <section class="engine-section">
        <div class="results-header-bar sub-header-bar">
          <div class="results-header-left">
            <h2 class="results-title">Queue Status Breakdown</h2>
            <span class="results-count-pill">{{ stats.request_overview?.total_requests || 0 }} total requests</span>
          </div>
        </div>

        <div class="metric-tiles-grid">
          <!-- Pending Tile -->
          <div class="card metric-tile tile-pending">
            <div class="mt-header">
              <span class="mt-title">Pending</span>
              <span class="pill-badge pill-amber">Awaiting Processing</span>
            </div>
            <div class="mt-value text-amber">{{ stats.request_overview?.pending || 0 }}</div>
            <div class="mt-subtext">Received into staging queue</div>
          </div>

          <!-- In Progress Tile -->
          <div class="card metric-tile tile-progress">
            <div class="mt-header">
              <span class="mt-title">In Progress</span>
              <span class="pill-badge pill-blue">Worker Active</span>
            </div>
            <div class="mt-value text-blue">{{ stats.request_overview?.in_progress || 0 }}</div>
            <div class="mt-subtext">Currently executing scoring job</div>
          </div>

          <!-- Completed Tile -->
          <div class="card metric-tile tile-completed">
            <div class="mt-header">
              <span class="mt-title">Completed</span>
              <span class="pill-badge pill-green">Finalized</span>
            </div>
            <div class="mt-value text-green">{{ stats.request_overview?.completed || 0 }}</div>
            <div class="mt-subtext">Scored, linked &amp; archived</div>
          </div>

          <!-- Failed Tile -->
          <div class="card metric-tile tile-failed">
            <div class="mt-header">
              <span class="mt-title">Failed / Dead-Letter</span>
              <span class="pill-badge" :class="failedCount > 0 ? 'pill-red' : 'pill-slate'">
                {{ failedCount > 0 ? 'Action Required' : '0 Failures' }}
              </span>
            </div>
            <div class="mt-value" :class="failedCount > 0 ? 'text-red' : 'text-slate'">{{ failedCount }}</div>
            <div class="mt-subtext">{{ failedCount > 0 ? 'Exceeded DLQ retries' : 'Clean audit trail' }}</div>
          </div>
        </div>
      </section>

      <!-- 2. REQUEST ANALYTICS -->
      <section class="engine-section">
        <div class="results-header-bar sub-header-bar">
          <div class="results-header-left">
            <h2 class="results-title">Ingestion Analytics &amp; Throughput</h2>
            <span class="results-count-pill">{{ stats.analytics?.success_rate || 0 }}% reliability</span>
          </div>

          <div class="view-toggle-group">
            <button
              type="button"
              class="view-btn"
              :class="{ active: timelineMode === '24h' }"
              @click="timelineMode = '24h'"
            >
              Last 24h (Hourly)
            </button>
            <button
              type="button"
              class="view-btn"
              :class="{ active: timelineMode === '7d' }"
              @click="timelineMode = '7d'"
            >
              Last 7d (Daily)
            </button>
          </div>
        </div>

        <!-- 3 KPI Cards -->
        <div class="kpi-cards-grid">
          <div class="card kpi-card">
            <div class="kpi-top">
              <span class="kpi-icon-pill icon-pill-emerald">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><polyline points="20 6 9 17 4 12"/></svg>
              </span>
              <span class="kpi-card-label">Success Rate</span>
            </div>
            <div class="kpi-main-val">{{ stats.analytics?.success_rate || 0 }}%</div>
            <div class="kpi-bar-track">
              <div class="kpi-bar-fill" :style="{ width: (stats.analytics?.success_rate || 0) + '%' }"></div>
            </div>
            <div class="kpi-footer-note">Failure rate: <strong>{{ stats.analytics?.failure_rate || 0 }}%</strong></div>
          </div>

          <div class="card kpi-card">
            <div class="kpi-top">
              <span class="kpi-icon-pill icon-pill-blue">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
              </span>
              <span class="kpi-card-label">Average Processing Time</span>
            </div>
            <div class="kpi-main-val">{{ stats.analytics?.average_processing_time_formatted || '0s' }}</div>
            <div class="kpi-footer-note">End-to-end scoring &amp; database commitment</div>
          </div>

          <div class="card kpi-card">
            <div class="kpi-top">
              <span class="kpi-icon-pill icon-pill-amber">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
              </span>
              <span class="kpi-card-label">Oldest Pending Request</span>
            </div>
            <div class="kpi-main-val" :class="stats.analytics?.oldest_pending_request ? 'text-amber' : 'text-slate'">
              {{ stats.analytics?.oldest_pending_request ? stats.analytics.oldest_pending_request.waiting_time_formatted : 'None' }}
            </div>
            <div class="kpi-footer-note" v-if="stats.analytics?.oldest_pending_request">
              Arrived {{ formatTime(stats.analytics.oldest_pending_request.created_at) }}
            </div>
            <div class="kpi-footer-note" v-else>
              Queue running at zero backlog
            </div>
          </div>
        </div>

        <!-- Volume Chart Card -->
        <div class="card chart-card">
          <div class="chart-top-bar">
            <div>
              <h3 class="chart-heading">
                {{ timelineMode === '24h' ? 'Submission Ingestion Velocity (Past 24 Hours)' : 'Daily Submission Aggregates (Past 7 Days)' }}
              </h3>
              <p class="chart-sub">Volume of assessment payloads accepted into the durable staging buffer.</p>
            </div>
            <span class="results-count-pill">{{ currentTimelineData.length }} time buckets</span>
          </div>

          <div v-if="currentTimelineData.length" class="chart-histogram">
            <div class="hist-col" v-for="(item, idx) in currentTimelineData" :key="idx">
              <div class="hist-track">
                <div
                  class="hist-bar"
                  :style="{ height: getBarHeight(item.count) }"
                  :title="`${item.bucket}: ${item.count} submissions`"
                >
                  <span class="hist-tip">{{ item.count }}</span>
                </div>
              </div>
              <span class="hist-label">{{ item.label }}</span>
            </div>
          </div>
          <div v-else class="chart-empty">
            <p>No submission activity recorded in this time range.</p>
          </div>
        </div>
      </section>

      <!-- 3. WORKER FLEET COORDINATION -->
      <section class="engine-section">
        <div class="results-header-bar sub-header-bar">
          <div class="results-header-left">
            <h2 class="results-title">Background Worker Fleet</h2>
            <span class="results-count-pill">{{ stats.worker_progress?.total_workers || 0 }} registered processes</span>
          </div>

          <div class="fleet-badges-strip">
            <span class="fleet-tag tag-active">
              <span class="ft-dot ft-green"></span>
              Active: <strong>{{ stats.worker_progress?.active_workers || 0 }}</strong>
            </span>
            <span class="fleet-tag tag-idle">
              <span class="ft-dot ft-blue"></span>
              Idle: <strong>{{ stats.worker_progress?.idle_workers || 0 }}</strong>
            </span>
            <span class="fleet-tag tag-offline">
              <span class="ft-dot ft-red"></span>
              Offline (>3m): <strong>{{ stats.worker_progress?.offline_workers || 0 }}</strong>
            </span>
          </div>
        </div>

        <div class="card table-card-wrap">
          <table class="engine-table" v-if="stats.worker_progress?.workers?.length">
            <thead>
              <tr>
                <th>Status</th>
                <th>Worker ID</th>
                <th>Process Type</th>
                <th>Current Task</th>
                <th>Jobs Completed</th>
                <th>Heartbeat</th>
                <th>Uptime Started</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="w in stats.worker_progress.workers" :key="w.worker_id">
                <td>
                  <span
                    class="worker-state-pill"
                    :class="{
                      'state-active': w.status === 'active',
                      'state-idle': w.status === 'idle',
                      'state-offline': w.status === 'offline'
                    }"
                  >
                    <span class="state-dot"></span>
                    {{ w.status === 'offline' ? 'Offline (>3m)' : (w.status === 'active' ? 'Active' : 'Idle') }}
                  </span>
                </td>
                <td>
                  <code class="worker-code">{{ w.worker_id }}</code>
                </td>
                <td>
                  <span class="worker-type-pill">{{ w.worker_type }}</span>
                </td>
                <td>
                  <span class="worker-task-desc" :title="w.current_task">{{ w.current_task }}</span>
                </td>
                <td>
                  <strong class="jobs-num">{{ w.jobs_completed }}</strong>
                </td>
                <td>
                  <span class="hb-indicator" :class="{ 'hb-delayed': w.status === 'offline' }">
                    {{ w.last_heartbeat_formatted }}
                  </span>
                </td>
                <td class="date-text">
                  {{ formatTime(w.started_at) }}
                </td>
              </tr>
            </tbody>
          </table>

          <div v-else class="engine-empty-table">
            <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
              <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
              <line x1="6" y1="6" x2="6.01" y2="6"></line>
              <line x1="6" y1="18" x2="6.01" y2="18"></line>
            </svg>
            <h3>No Background Worker Processes Registered</h3>
            <p>
              Background workers (Service Bus consumers, DB outbox pollers) dispatch telemetry every 30–60 seconds. Active daemons will populate automatically.
            </p>
          </div>
        </div>
      </section>

      <!-- 4. DEAD-LETTER QUEUE (DLQ) & FAILURE INSPECTOR -->
      <section class="engine-section">
        <div class="results-header-bar sub-header-bar">
          <div class="results-header-left">
            <h2 class="results-title">Dead-Letter Queue &amp; Failure Inspector</h2>
            <span class="results-count-pill" :class="{ 'pill-alert': dlqItems.length > 0 }">
              {{ dlqItems.length }} item{{ dlqItems.length === 1 ? '' : 's' }}
            </span>
          </div>

          <div class="header-action-wrap" v-if="dlqItems.length">
            <button
              type="button"
              class="hero-search-btn btn-replay-all"
              :disabled="replayingAll"
              @click="handleReplayAll"
              title="Re-arm and reprocess all dead-lettered submissions"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/></svg>
              <span>{{ replayingAll ? 'Replaying All…' : 'Reprocess All DLQ' }}</span>
            </button>
          </div>
        </div>

        <div class="card table-card-wrap">
          <table class="engine-table" v-if="dlqItems.length">
            <thead>
              <tr>
                <th>Status</th>
                <th>Submission ID</th>
                <th>Organisation</th>
                <th>Recipient / User</th>
                <th>Retries</th>
                <th>Failure Root Cause</th>
                <th>Last Attempt</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in dlqItems" :key="item.submission_id">
                <td>
                  <span class="worker-state-pill state-offline">
                    <span class="state-dot"></span>
                    {{ item.status }}
                  </span>
                </td>
                <td>
                  <code class="worker-code">{{ item.submission_id.substring(0, 8) }}…</code>
                </td>
                <td class="bold-text">
                  {{ item.organization_name || 'Direct' }}
                </td>
                <td class="email-text">
                  {{ item.user_email || '—' }}
                </td>
                <td>
                  <span class="retry-pill">{{ item.retry_count }}</span>
                </td>
                <td>
                  <span class="error-msg-box" :title="item.last_error">{{ item.last_error || 'Exceeded retry ceiling' }}</span>
                </td>
                <td class="date-text">
                  {{ formatTime(item.updated_at) }}
                </td>
                <td>
                  <button
                    type="button"
                    class="btn-row-replay"
                    :disabled="replayingId === item.submission_id"
                    @click="handleReplayOne(item.submission_id)"
                  >
                    {{ replayingId === item.submission_id ? 'Re-arming…' : 'Replay' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>

          <div v-else class="engine-empty-table green-empty">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#22C55E" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
            <h3>All Systems Nominal — 0 Dead-Letter Submissions</h3>
            <p>Every ingested submission has been successfully processed, scored, and archived with zero unhandled errors.</p>
          </div>
        </div>
      </section>
    </main>

    <!-- Initial Loading State matching Overview skeleton -->
    <div v-else class="engine-loading-skeleton">
      <div class="skeleton-shimmer" style="height: 140px; margin-bottom: 24px; border-radius: 12px;"></div>
      <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px;">
        <div class="skeleton-shimmer" style="height: 120px; border-radius: 12px;"></div>
        <div class="skeleton-shimmer" style="height: 120px; border-radius: 12px;"></div>
        <div class="skeleton-shimmer" style="height: 120px; border-radius: 12px;"></div>
        <div class="skeleton-shimmer" style="height: 120px; border-radius: 12px;"></div>
      </div>
      <div class="skeleton-shimmer" style="height: 260px; border-radius: 12px;"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { getSuperAdminDashboard, getDeadLetteredSubmissions, replaySubmission, replayAllDeadLetteredSubmissions } from '../api';

const stats = ref(null);
const loading = ref(false);
const error = ref(null);
const lastUpdated = ref(null);
const dlqItems = ref([]);
const replayingId = ref(null);
const replayingAll = ref(false);
const isTabVisible = ref(true);
const timelineMode = ref('24h');

let pollIntervalId = null;
let lastFetchTimestamp = 0;

// Computed metric helpers
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

async function fetchDashboard(forceRefresh = false) {
  if (loading.value) return;
  loading.value = true;
  error.value = null;

  try {
    const data = await getSuperAdminDashboard(forceRefresh);
    stats.value = data;
    lastUpdated.value = data.timestamp || new Date().toISOString();
    lastFetchTimestamp = Date.now();

    try {
      const dlqData = await getDeadLetteredSubmissions();
      dlqItems.value = dlqData.dead_lettered_submissions || [];
    } catch (e) {
      console.warn('Could not load DLQ submissions:', e);
    }
  } catch (err) {
    console.error('Error fetching operations dashboard:', err);
    error.value = err.message || 'Failed to connect to operations endpoint';
  } finally {
    loading.value = false;
  }
}

// Requirement 4: Auto-refresh every 2 minutes with Tab Visibility pause
async function handleReplayOne(id) {
  if (replayingId.value) return;
  replayingId.value = id;
  try {
    await replaySubmission(id);
    await fetchDashboard(true);
  } catch (e) {
    alert('Failed to re-arm submission: ' + e.message);
  } finally {
    replayingId.value = null;
  }
}

async function handleReplayAll() {
  if (replayingAll.value) return;
  replayingAll.value = true;
  try {
    await replayAllDeadLetteredSubmissions();
    await fetchDashboard(true);
  } catch (e) {
    alert('Failed to re-arm submissions: ' + e.message);
  } finally {
    replayingAll.value = false;
  }
}

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
    const elapsed = Date.now() - lastFetchTimestamp;
    if (elapsed >= 120000) {
      fetchDashboard(false);
    }
    startPolling();
  } else {
    stopPolling();
  }
}

onMounted(() => {
  const role = sessionStorage.getItem('nd_role');
  if (role !== 'super') {
    error.value = 'Super administrator privileges required to access Platform Operations Command.';
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
/* Page Root & NIWI Warm Canvas */
.super-engine-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  color: var(--primary, #161057);
  max-width: 1400px;
  margin: 0 auto;
  padding: 16px 24px 60px;
}

/* ==========================================================================
   HERO / SEARCH BANNER (Matches Overview.vue Neo-Modern Serif Style)
   ========================================================================== */
.hero-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 24px 0 16px;
}

.hero-content {
  max-width: 880px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.super-kicker-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #FAF9F5;
  border: 1.5px solid var(--primary, #161057);
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.12);
  padding: 4px 14px;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 700;
  margin-bottom: 14px;
}

.kicker-tag {
  color: var(--primary, #161057);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.kicker-divider {
  color: #94a3b8;
}

.kicker-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
}

.kicker-status.live-on {
  color: #15803d;
}

.kicker-status.live-paused {
  color: #b45309;
}

.pulse-indicator {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: currentColor;
  animation: pulse-ring 2s infinite;
}

@keyframes pulse-ring {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(0.85); opacity: 0.4; }
  100% { transform: scale(1); opacity: 1; }
}

.hero-title {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 2.35rem;
  font-weight: 800;
  color: var(--primary, #161057);
  letter-spacing: -0.03em;
  margin: 0 0 8px 0;
  line-height: 1.18;
}

.hero-subtitle {
  font-family: var(--font-body);
  font-size: 0.95rem;
  color: #64748B;
  max-width: 620px;
  margin: 0 0 20px 0;
  line-height: 1.5;
}

/* Engine Controls Strip */
.engine-top-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 12px;
  box-shadow: 3px 3px 0px rgba(22, 16, 87, 0.12);
  padding: 8px 14px;
}

.control-meta-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.82rem;
  color: #475569;
}

.control-meta-pill svg {
  color: var(--primary, #161057);
}

.cache-badge {
  font-size: 0.7rem;
  font-weight: 700;
  background: #FAF9F5;
  border: 1px solid var(--primary, #161057);
  color: var(--primary, #161057);
  padding: 2px 8px;
  border-radius: 6px;
}

.btn-refresh-engine {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--primary, #161057);
  color: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 8px;
  padding: 6px 14px;
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.2);
}

.btn-refresh-engine:hover:not(:disabled) {
  background: var(--primary-hover, #0F0A42);
  transform: translateY(-1px);
  box-shadow: 3px 3px 0px rgba(22, 16, 87, 0.25);
}

.btn-refresh-engine:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.refresh-spinner.spinning {
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}

/* Error Banner */
.alert-banner-error {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #FFF5F5;
  border: 1.5px solid #E53E3E;
  color: #C53030;
  padding: 14px 20px;
  border-radius: 12px;
  box-shadow: 2px 2px 0px rgba(229, 62, 62, 0.15);
}

.alert-text {
  flex: 1;
  font-size: 0.88rem;
}

.btn-retry-engine {
  background: #C53030;
  color: #fff;
  border: none;
  font-weight: 700;
  font-size: 0.8rem;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
}

/* ==========================================================================
   CARDS & SECTION CONTAINERS (Exact NIWI Card Aesthetic)
   ========================================================================== */
.card {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 12px;
  box-shadow: 3px 3px 0px rgba(22, 16, 87, 0.12);
  transition: all 0.2s ease;
}

.card:hover {
  box-shadow: 4px 4px 0px rgba(22, 16, 87, 0.18);
}

/* Results header bar (Shared with Overview.vue) */
.results-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.results-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.results-title {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--primary, #161057);
  margin: 0;
}

.results-count-pill {
  font-family: var(--font-body);
  font-size: 0.78rem;
  font-weight: 700;
  background: #FAF9F5;
  border: 1.5px solid var(--primary, #161057);
  color: var(--primary, #161057);
  padding: 3px 10px;
  border-radius: 9999px;
  box-shadow: 1px 1px 0px rgba(22, 16, 87, 0.1);
}

/* 1. PENDING HERO CARD */
.hero-pending-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 28px;
  margin-bottom: 28px;
  flex-wrap: wrap;
  gap: 20px;
}

.hero-pending-card.pending-alert {
  background: #FFFDF7;
  border-color: #D97706;
  box-shadow: 3px 3px 0px rgba(217, 119, 6, 0.2);
}

.hero-pending-card.pending-alert .hpc-icon-box {
  background: #D97706;
  color: #FFFFFF;
}

.hero-pending-card.pending-clear {
  background: #F8FCF9;
  border-color: #15803D;
  box-shadow: 3px 3px 0px rgba(21, 128, 61, 0.15);
}

.hero-pending-card.pending-clear .hpc-icon-box {
  background: #15803D;
  color: #FFFFFF;
}

.hpc-left {
  display: flex;
  align-items: center;
  gap: 22px;
}

.hpc-icon-box {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: 1.5px solid var(--primary, #161057);
}

.hpc-badge-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.hpc-kicker {
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--primary, #161057);
}

.hpc-wait-pill {
  font-size: 0.72rem;
  font-weight: 700;
  background: #FEF3C7;
  color: #B45309;
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid #FDE68A;
}

.hpc-count-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 6px;
}

.hpc-big-val {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 2.5rem;
  font-weight: 800;
  line-height: 1;
  color: var(--primary, #161057);
}

.hpc-count-label {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--primary, #161057);
  margin: 0;
}

.hpc-explanation {
  font-size: 0.85rem;
  color: #64748B;
  margin: 0;
  max-width: 620px;
  line-height: 1.45;
}

.hpc-explanation code {
  background: #FAF9F5;
  border: 1px solid #e2ddd4;
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 0.82rem;
  color: var(--primary, #161057);
}

.hpc-right {
  display: flex;
  gap: 14px;
}

.hpc-stat-box {
  background: #FAF9F5;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 10px;
  padding: 10px 18px;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.08);
}

.hpc-stat-label {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #64748B;
}

.hpc-stat-val {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.35rem;
  font-weight: 800;
  color: var(--primary, #161057);
}

/* Metric Tiles Grid */
.engine-section {
  margin-bottom: 32px;
}

.metric-tiles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
}

.metric-tile {
  padding: 20px;
}

.mt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.mt-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--primary, #161057);
}

.pill-badge {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid currentColor;
}

.pill-amber { background: #FEF3C7; color: #B45309; }
.pill-blue { background: #E0F2FE; color: #0369A1; }
.pill-green { background: #DCFCE7; color: #15803D; }
.pill-red { background: #FEE2E2; color: #B91C1C; }
.pill-slate { background: #F1F5F9; color: #64748B; }

.mt-value {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 2.2rem;
  font-weight: 800;
  line-height: 1.1;
  margin-bottom: 6px;
}

.text-amber { color: #D97706; }
.text-blue { color: #0284C7; }
.text-green { color: #15803D; }
.text-red { color: #DC2626; }
.text-slate { color: #475569; }

.mt-subtext {
  font-size: 0.78rem;
  color: #64748B;
}

/* KPI Cards */
.kpi-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 18px;
}

.kpi-card {
  padding: 20px;
}

.kpi-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.kpi-icon-pill {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1.5px solid var(--primary, #161057);
}

.icon-pill-emerald { background: #DCFCE7; color: #15803D; }
.icon-pill-blue { background: #E0F2FE; color: #0284C7; }
.icon-pill-amber { background: #FEF3C7; color: #D97706; }

.kpi-card-label {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--primary, #161057);
}

.kpi-main-val {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.85rem;
  font-weight: 800;
  color: var(--primary, #161057);
  margin-bottom: 8px;
}

.kpi-bar-track {
  width: 100%;
  height: 8px;
  background: #FEE2E2;
  border: 1px solid var(--primary, #161057);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.kpi-bar-fill {
  height: 100%;
  background: #15803D;
  transition: width 0.3s ease;
}

.kpi-footer-note {
  font-size: 0.78rem;
  color: #64748B;
}

/* View Switchers (Matches Overview.vue view-toggle-group) */
.view-toggle-group {
  display: inline-flex;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.1);
}

.view-btn {
  background: #FAF9F5;
  border: none;
  color: var(--primary, #161057);
  padding: 6px 14px;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.view-btn.active {
  background: var(--primary, #161057);
  color: #FFFFFF;
}

/* Chart Container */
.chart-card {
  padding: 24px;
}

.chart-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.chart-heading {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--primary, #161057);
  margin: 0 0 4px 0;
}

.chart-sub {
  font-size: 0.84rem;
  color: #64748B;
  margin: 0;
}

.chart-histogram {
  display: flex;
  align-items: flex-end;
  height: 180px;
  gap: 12px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.hist-col {
  flex: 1;
  min-width: 32px;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.hist-track {
  width: 100%;
  max-width: 28px;
  height: 150px;
  display: flex;
  align-items: flex-end;
  background: #FAF9F5;
  border-radius: 6px 6px 0 0;
  border: 1px solid #e2ddd4;
}

.hist-bar {
  width: 100%;
  background: var(--primary, #161057);
  border-radius: 4px 4px 0 0;
  position: relative;
  transition: height 0.3s ease;
}

.hist-bar:hover {
  background: #2b237c;
}

.hist-tip {
  display: none;
  position: absolute;
  top: -26px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--primary, #161057);
  color: #FFFFFF;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  white-space: nowrap;
}

.hist-bar:hover .hist-tip {
  display: block;
}

.hist-label {
  font-size: 0.68rem;
  color: #64748B;
  margin-top: 8px;
  text-align: center;
  white-space: nowrap;
  font-weight: 600;
}

.chart-empty {
  text-align: center;
  color: #94a3b8;
  padding: 40px 0;
  font-size: 0.88rem;
}

/* Fleet Strip */
.fleet-badges-strip {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.fleet-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 9999px;
  border: 1.5px solid var(--primary, #161057);
  background: #FAF9F5;
}

.ft-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.ft-green { background: #15803D; }
.ft-blue { background: #0284C7; }
.ft-red { background: #DC2626; }

/* Table Styling (Matches Overview.vue & Organisations.vue) */
.table-card-wrap {
  overflow: hidden;
}

.engine-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.85rem;
}

.engine-table th {
  background: #F8F7F4;
  color: var(--primary, #161057);
  font-weight: 700;
  padding: 12px 18px;
  border-bottom: 1.5px solid var(--primary, #161057);
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.engine-table td {
  padding: 14px 18px;
  border-bottom: 1px solid #e2ddd4;
  color: var(--primary, #161057);
  vertical-align: middle;
}

.engine-table tr:hover td {
  background: #FAF9F5;
}

.engine-table tr:last-child td {
  border-bottom: none;
}

.worker-state-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 3px 10px;
  border-radius: 9999px;
  border: 1px solid currentColor;
}

.state-active { background: #DCFCE7; color: #15803D; }
.state-idle { background: #E0F2FE; color: #0369A1; }
.state-offline { background: #FEE2E2; color: #B91C1C; }

.state-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.worker-code {
  font-family: monospace;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--primary, #161057);
}

.worker-type-pill {
  font-size: 0.72rem;
  font-weight: 600;
  background: #FAF9F5;
  border: 1px solid #e2ddd4;
  color: #475569;
  padding: 2px 8px;
  border-radius: 6px;
}

.worker-task-desc {
  max-width: 240px;
  display: inline-block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #475569;
}

.jobs-num {
  font-weight: 800;
  color: var(--primary, #161057);
}

.hb-indicator {
  font-size: 0.78rem;
  font-weight: 700;
  color: #15803D;
}

.hb-indicator.hb-delayed {
  color: #DC2626;
}

.date-text {
  font-size: 0.75rem;
  color: #64748B;
}

.engine-empty-table {
  padding: 48px 24px;
  text-align: center;
  color: #64748B;
}

.engine-empty-table svg {
  color: var(--primary, #161057);
  margin-bottom: 12px;
}

.engine-empty-table h3 {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--primary, #161057);
  margin: 0 0 6px 0;
}

.engine-empty-table p {
  font-size: 0.85rem;
  max-width: 520px;
  margin: 0 auto;
  line-height: 1.5;
}

/* Skeleton Loading (matches Overview.vue skeleton) */
.engine-loading-skeleton {
  padding: 20px 0;
}

.skeleton-shimmer {
  background: linear-gradient(90deg, #ece9e6 25%, #f7f6f4 50%, #ece9e6 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.btn-replay-all {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--primary, #161057);
  color: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 99px;
  padding: 6px 14px;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-replay-all:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}
.btn-row-replay {
  background: #FFFFFF;
  color: var(--primary, #161057);
  border: 1.5px solid var(--primary, #161057);
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}
.btn-row-replay:hover:not(:disabled) {
  background: rgba(22, 16, 87, 0.08);
}
.error-msg-box {
  display: inline-block;
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-family: var(--font-mono, monospace);
  font-size: 0.78rem;
  color: #DC2626;
  background: rgba(239, 68, 68, 0.08);
  padding: 2px 6px;
  border-radius: 4px;
}
.retry-pill {
  display: inline-block;
  padding: 2px 8px;
  font-size: 0.78rem;
  font-weight: 700;
  border-radius: 99px;
  background: #F1F5F9;
  color: #475569;
}
.green-empty {
  border-color: rgba(34, 197, 94, 0.2) !important;
}
.bold-text {
  font-weight: 600;
  color: #1E293B;
}
.email-text {
  font-size: 0.82rem;
  color: #64748B;
}

</style>
