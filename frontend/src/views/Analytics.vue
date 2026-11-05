<template>
  <div class="analytics-page animate-in">
    <!-- Hero / Header Section matching Organisations / Overview -->
    <section class="hero-section" aria-label="Analytics Banner">
      <div class="hero-content">
        <div class="hero-header-row">
          <div>
            <h1 class="hero-title">Cross-Organisation Analytics &amp; Benchmarks</h1>
            <p class="hero-subtitle">
              Aggregate patterns, compare workplace inclusion maturity across organisations and demographic segments, and identify priority intervention areas.
            </p>
          </div>
          <div class="hero-actions">
            <button class="btn btn-outline" @click="loadData" :disabled="loading" title="Refresh all analytics data">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" :class="{ 'spin-icon': loading }">
                <path d="M23 4v6h-6M1 20v-6h6"></path>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
              </svg>
              {{ loading ? 'Updating…' : 'Refresh Data' }}
            </button>
          </div>
        </div>

        <!-- Integrated Filter Controls Bar -->
        <div class="search-banner-card">
          <!-- Organisation Filter -->
          <div class="filter-item-wrap">
            <label class="filter-label" for="org-select">Organisation:</label>
            <div class="filter-select-inner">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">
                <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
                <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
              </svg>
              <select id="org-select" v-model="selectedOrgFilter" aria-label="Filter by Organisation">
                <option value="all">All Organisations ({{ uniqueOrgNames.length }})</option>
                <option v-for="orgName in uniqueOrgNames" :key="orgName" :value="orgName">
                  {{ orgName }}
                </option>
              </select>
            </div>
          </div>

          <div class="search-divider"></div>

          <!-- Date Range Preset Filter -->
          <div class="filter-item-wrap">
            <label class="filter-label" for="date-range-select">Time Period:</label>
            <div class="filter-select-inner">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">
                <rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect>
                <line x1="16" y1="2" x2="16" y2="6"></line>
                <line x1="8" y1="2" x2="8" y2="6"></line>
                <line x1="3" y1="10" x2="21" y2="10"></line>
              </svg>
              <select id="date-range-select" v-model="dateRangePreset" aria-label="Filter by Time Period">
                <option value="all">All Time</option>
                <option value="30d">Last 30 Days</option>
                <option value="90d">Last 90 Days</option>
                <option value="year">Past 12 Months</option>
                <option value="custom">Custom Date Range</option>
              </select>
            </div>
          </div>

          <!-- Custom Date Pickers if selected -->
          <div v-if="dateRangePreset === 'custom'" class="custom-dates-row">
            <input v-model="dateFrom" type="date" aria-label="From date" />
            <span class="to-text">to</span>
            <input v-model="dateTo" type="date" aria-label="To date" />
          </div>

          <div class="search-divider"></div>

          <!-- Submission Source Filter -->
          <div class="filter-item-wrap">
            <label class="filter-label" for="source-select">Method:</label>
            <div class="filter-select-inner">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="2" y1="12" x2="22" y2="12"></line>
                <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
              </svg>
              <select id="source-select" v-model="selectedSourceFilter" aria-label="Filter by Submission Source">
                <option value="all">All Submission Types</option>
                <option value="direct">Direct Website Submissions</option>
                <option value="invitation">Invitation Link Audits</option>
              </select>
            </div>
          </div>

          <button
            v-if="hasActiveFilters"
            class="btn-reset-filters"
            @click="resetFilters"
            title="Reset all filters to default"
          >
            ✕ Reset Filters
          </button>
        </div>
      </div>
    </section>

    <!-- Main Content Area -->
    <div class="analytics-content-layout">
      <!-- Loading State: Progressive Skeleton Dashboard -->
      <div v-if="loading" class="analytics-skeleton-wrapper" aria-busy="true">
        <div class="analytics-loading-card">
          <div class="spinner"></div>
          <span>Calculating portfolio analytics and cross-pillar benchmarks…</span>
        </div>

        <div class="metrics-kpi-grid">
          <div class="kpi-card skeleton-card" v-for="i in 4" :key="i">
            <div class="skeleton-shimmer sk-kpi-icon"></div>
            <div class="sk-kpi-info">
              <div class="skeleton-shimmer sk-kpi-label"></div>
              <div class="skeleton-shimmer sk-kpi-val"></div>
            </div>
          </div>
        </div>

        <div class="analytics-charts-grid">
          <div class="chart-panel-card skeleton-chart" v-for="i in 2" :key="i">
            <div class="skeleton-shimmer sk-chart-title"></div>
            <div class="skeleton-shimmer sk-chart-canvas"></div>
          </div>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="alert alert-error">
        <span>{{ error }}</span>
        <button class="btn btn-outline btn-sm" @click="loadData">Try Again</button>
      </div>

      <!-- Empty State -->
      <div v-else-if="filteredSubmissions.length === 0" class="analytics-empty-card">
        <div class="empty-icon">📊</div>
        <h3>No Submissions Found Matching Filters</h3>
        <p>No audit submissions match your selected organisation, date range, or submission method.</p>
        <button class="btn btn-primary btn-sm" @click="resetFilters">Clear Active Filters</button>
      </div>

      <!-- Analytical Dashboard -->
      <template v-else>
        <!-- Row 1: KPI Summary Metric Cards -->
        <div class="metrics-kpi-grid">
          <div class="kpi-card">
            <div class="kpi-icon-box kpi-blue">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
            </div>
            <div class="kpi-content">
              <span class="kpi-label">Total Audits Analyzed</span>
              <div class="kpi-value-row">
                <span class="kpi-value">{{ filteredSubmissions.length }}</span>
                <span class="kpi-sub">across {{ activeOrgCount }} {{ activeOrgCount === 1 ? 'org' : 'orgs' }}</span>
              </div>
            </div>
          </div>

          <div class="kpi-card">
            <div class="kpi-icon-box kpi-green">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            </div>
            <div class="kpi-content">
              <span class="kpi-label">Average Weighted Index</span>
              <div class="kpi-value-row">
                <span class="kpi-value">{{ portfolioAvgScore }}</span>
                <span class="kpi-denom">/ 20</span>
                <span class="kpi-badge" :class="getMaturityClass(portfolioAvgScore)">{{ portfolioLevel }}</span>
              </div>
            </div>
          </div>

          <div class="kpi-card">
            <div class="kpi-icon-box kpi-amber">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
            </div>
            <div class="kpi-content">
              <span class="kpi-label">Highest Performing Pillar</span>
              <div class="kpi-text-value">
                <span class="kpi-bold-title">{{ strongestPillar.label }}</span>
                <span class="kpi-strong-score">{{ strongestPillar.avg }}/20 ({{ Math.round((strongestPillar.avg / 20) * 100) }}%)</span>
              </div>
            </div>
          </div>

          <div class="kpi-card">
            <div class="kpi-icon-box kpi-red">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
            </div>
            <div class="kpi-content">
              <span class="kpi-label">Priority Growth Focus</span>
              <div class="kpi-text-value">
                <span class="kpi-bold-title">{{ weakestPillar.label }}</span>
                <span class="kpi-weak-score">{{ weakestPillar.avg }}/20 ({{ Math.round((weakestPillar.avg / 20) * 100) }}%)</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Row 2: Radar Chart + Maturity Donut Distribution -->
        <div class="charts-row-2">
          <!-- 8 Core Pillars Radar Chart -->
          <div class="card chart-card">
            <div class="chart-head">
              <div>
                <h3 class="chart-title">8 Core Pillars Maturity Profile</h3>
                <span class="chart-sub">Average score out of 20 across {{ filteredSubmissions.length }} submissions</span>
              </div>
              <span class="chart-dim-badge">Radar View</span>
            </div>
            <div class="radar-container">
              <canvas ref="radarChartRef"></canvas>
            </div>
          </div>

          <!-- Maturity Level Breakdown Donut -->
          <div class="card chart-card">
            <div class="chart-head">
              <div>
                <h3 class="chart-title">Maturity Level Distribution</h3>
                <span class="chart-sub">Portfolio breakdown by NIWI maturity tier</span>
              </div>
              <span class="chart-dim-badge">3 Tiers</span>
            </div>
            <div class="donut-container">
              <div class="donut-canvas-wrap">
                <canvas ref="donutChartRef"></canvas>
              </div>
              <div class="donut-legend-list">
                <div v-for="item in maturityLegend" :key="item.label" class="legend-row">
                  <div class="legend-color-tag" :style="{ background: item.color }"></div>
                  <div class="legend-info">
                    <span class="legend-name">{{ item.label }}</span>
                    <span class="legend-range">{{ item.range }}</span>
                  </div>
                  <div class="legend-count-box">
                    <strong>{{ item.count }}</strong>
                    <span class="legend-pct">({{ item.pct }}%)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Row 3: Ranked Section Scores Bar Chart -->
        <div class="card chart-card-full">
          <div class="chart-head">
            <div>
              <h3 class="chart-title">Pillar Scores Ranked: Lowest to Highest</h3>
              <span class="chart-sub">Benchmark comparison identifying systemic organisational strengths vs intervention priorities</span>
            </div>
            <span class="chart-dim-badge">Out of 20</span>
          </div>
          <div class="bar-chart-container">
            <canvas ref="barChartRef" height="85"></canvas>
          </div>
        </div>

        <!-- Row 4: Monthly Trend Chart -->
        <div class="card chart-card-full">
          <div class="chart-head">
            <div>
              <h3 class="chart-title">Monthly Inclusion Score Trend</h3>
              <span class="chart-sub">Timeline of aggregate workplace inclusion maturity (grouped by Indian Standard Time calendar months)</span>
            </div>
            <span class="chart-dim-badge">IST Timeline</span>
          </div>
          <div class="trend-chart-container">
            <canvas ref="trendChartRef" height="85"></canvas>
          </div>
        </div>

        <!-- Row 5: Top Performing vs Needs Support Organisations -->
        <div class="charts-row-2">
          <!-- Top Performing Orgs -->
          <div class="card ranking-card">
            <div class="chart-head">
              <div>
                <h3 class="chart-title">Top Performing Organisations</h3>
                <span class="chart-sub">Highest aggregated inclusion maturity index</span>
              </div>
              <span class="rank-tag rank-top">Highest</span>
            </div>
            <div class="rank-list" v-if="topOrgs.length">
              <div
                v-for="(org, i) in topOrgs"
                :key="org.name"
                class="rank-row"
                @click="navigateToOrg(org)"
              >
                <span class="rank-badge top">{{ i + 1 }}</span>
                <div class="rank-details">
                  <span class="rank-org-name">{{ org.name }}</span>
                  <span class="rank-sub-meta">{{ org.count }} {{ org.count === 1 ? 'submission' : 'submissions' }}</span>
                </div>
                <div class="rank-bar-wrap">
                  <div class="rank-bar-bg">
                    <div class="rank-bar-fill green" :style="{ width: `${(org.avg / 20) * 100}%` }"></div>
                  </div>
                </div>
                <span class="rank-score-pill">{{ org.avg }} / 20</span>
              </div>
            </div>
            <div v-else class="empty-rank-note">No organisation submissions found.</div>
          </div>

          <!-- Needs Most Support -->
          <div class="card ranking-card">
            <div class="chart-head">
              <div>
                <h3 class="chart-title">Priority Support Focus</h3>
                <span class="chart-sub">Organisations with lowest average maturity requiring active intervention</span>
              </div>
              <span class="rank-tag rank-priority">Focus Areas</span>
            </div>
            <div class="rank-list" v-if="bottomOrgs.length">
              <div
                v-for="(org, i) in bottomOrgs"
                :key="org.name"
                class="rank-row"
                @click="navigateToOrg(org)"
              >
                <span class="rank-badge priority">{{ i + 1 }}</span>
                <div class="rank-details">
                  <span class="rank-org-name">{{ org.name }}</span>
                  <span class="rank-sub-meta">{{ org.count }} {{ org.count === 1 ? 'submission' : 'submissions' }}</span>
                </div>
                <div class="rank-bar-wrap">
                  <div class="rank-bar-bg">
                    <div class="rank-bar-fill coral" :style="{ width: `${(org.avg / 20) * 100}%` }"></div>
                  </div>
                </div>
                <span class="rank-score-pill priority">{{ org.avg }} / 20</span>
              </div>
            </div>
            <div v-else class="empty-rank-note">No organisation submissions found.</div>
          </div>
        </div>

        <!-- Row 6: Cross-Portfolio DEI Segment Perception Breakdown -->
        <div class="card segment-breakdown-card">
          <div class="chart-head">
            <div>
              <h3 class="chart-title">Demographic &amp; Neurodiversity Segment Comparison</h3>
              <span class="chart-sub">Cross-portfolio inclusion perception variances across respondent identities</span>
            </div>
            <span class="chart-dim-badge">DEI Variances</span>
          </div>

          <div class="segment-cards-grid">
            <!-- Neurodivergent vs Neurotypical Perception -->
            <div class="seg-mini-card">
              <div class="smc-header">
                <span class="smc-icon">🧠</span>
                <div>
                  <h4 class="smc-title">Neurodiversity Perception Gap</h4>
                  <p class="smc-desc">Comparison between neurodivergent and neurotypical staff</p>
                </div>
              </div>

              <div class="smc-groups-list">
                <div class="smc-group-row">
                  <span class="smc-group-name">Neurodivergent (ND)</span>
                  <div class="smc-bar-box">
                    <div class="smc-bar-fill" :style="{ width: `${(ndAvgScore / 20) * 100}%` }"></div>
                  </div>
                  <span class="smc-group-score">{{ ndAvgScore }} / 20</span>
                  <span class="smc-group-count">({{ ndCount }} audits)</span>
                </div>

                <div class="smc-group-row">
                  <span class="smc-group-name">Neurotypical (NT)</span>
                  <div class="smc-bar-box">
                    <div class="smc-bar-fill" :style="{ width: `${(ntAvgScore / 20) * 100}%` }"></div>
                  </div>
                  <span class="smc-group-score">{{ ntAvgScore }} / 20</span>
                  <span class="smc-group-count">({{ ntCount }} audits)</span>
                </div>
              </div>

              <div v-if="ndCount > 0 && ntCount > 0" class="smc-variance-tag" :class="ndDiffClass">
                <span>Perception Variance:</span>
                <strong>{{ Math.abs(ndDiff) }} pts {{ ndDiff > 0 ? '(NT rated higher)' : '(ND rated higher)' }}</strong>
              </div>
            </div>

            <!-- Role Seniority Comparison -->
            <div class="seg-mini-card">
              <div class="smc-header">
                <span class="smc-icon">👥</span>
                <div>
                  <h4 class="smc-title">Senior Leadership vs Individual Contributors</h4>
                  <p class="smc-desc">Perception alignment between leadership and frontline employees</p>
                </div>
              </div>

              <div class="smc-groups-list">
                <div class="smc-group-row">
                  <span class="smc-group-name">Leadership / Managers</span>
                  <div class="smc-bar-box">
                    <div class="smc-bar-fill" :style="{ width: `${(leaderAvgScore / 20) * 100}%` }"></div>
                  </div>
                  <span class="smc-group-score">{{ leaderAvgScore }} / 20</span>
                  <span class="smc-group-count">({{ leaderCount }} audits)</span>
                </div>

                <div class="smc-group-row">
                  <span class="smc-group-name">Individual Contributors</span>
                  <div class="smc-bar-box">
                    <div class="smc-bar-fill" :style="{ width: `${(icAvgScore / 20) * 100}%` }"></div>
                  </div>
                  <span class="smc-group-score">{{ icAvgScore }} / 20</span>
                  <span class="smc-group-count">({{ icCount }} audits)</span>
                </div>
              </div>

              <div v-if="leaderCount > 0 && icCount > 0" class="smc-variance-tag" :class="leaderDiffClass">
                <span>Alignment Variance:</span>
                <strong>{{ Math.abs(leaderDiff) }} pts {{ leaderDiff > 0 ? '(Leaders rated higher)' : '(Frontline rated higher)' }}</strong>
              </div>
            </div>
          </div>
        </div>

      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from "vue";
import { useRouter } from "vue-router";
import { Chart, registerables } from "chart.js";
import { getSubmissions } from "../api";
import { getISTMonthKey } from "../utils/datetime";

Chart.register(...registerables);

const router = useRouter();

// State
const loading = ref(true);
const error = ref("");
const allSubmissions = ref([]);

// Filter State
const selectedOrgFilter = ref("all");
const dateRangePreset = ref("all");
const dateFrom = ref("");
const dateTo = ref("");
const selectedSourceFilter = ref("all");

// Canvas refs
const radarChartRef = ref(null);
const donutChartRef = ref(null);
const barChartRef   = ref(null);
const trendChartRef = ref(null);

// Chart instances
let radarInstance = null;
let donutInstance = null;
let barInstance   = null;
let trendInstance = null;

// Core Pillars Configuration
const CORE_PILLARS = [
  { key: "lc_score", label: "Leadership & Culture", short: "Leadership", id: "lc" },
  { key: "ro_score", label: "Recruitment & Onboarding", short: "Recruitment", id: "ro" },
  { key: "we_score", label: "Work Environment", short: "Workplace", id: "we" },
  { key: "be_score", label: "Built Environment", short: "Sensory", id: "be" },
  { key: "tm_score", label: "Talent Management", short: "Talent", id: "tm" },
  { key: "ca_score", label: "Communication & Access", short: "Comms", id: "ca" },
  { key: "pc_score", label: "Products & Customers", short: "Products", id: "pc" },
  { key: "sp_score", label: "Suppliers & Procurement", short: "Suppliers", id: "sp" },
];

const hasActiveFilters = computed(() => {
  return selectedOrgFilter.value !== "all" ||
         dateRangePreset.value !== "all" ||
         selectedSourceFilter.value !== "all" ||
         Boolean(dateFrom.value || dateTo.value);
});

function resetFilters() {
  selectedOrgFilter.value = "all";
  dateRangePreset.value = "all";
  dateFrom.value = "";
  dateTo.value = "";
  selectedSourceFilter.value = "all";
}

// Unique Organisation Names for filter dropdown
const uniqueOrgNames = computed(() => {
  const names = new Set();
  allSubmissions.value.forEach(s => {
    if (s.company_name && s.company_name.trim()) {
      names.add(s.company_name.trim());
    }
  });
  return Array.from(names).sort((a, b) => a.localeCompare(b));
});

// Filtered Submissions
const filteredSubmissions = computed(() => {
  let list = [...allSubmissions.value];

  // Org filter
  if (selectedOrgFilter.value !== "all") {
    list = list.filter(s => (s.company_name || "").trim().toLowerCase() === selectedOrgFilter.value.toLowerCase());
  }

  // Source filter
  if (selectedSourceFilter.value !== "all") {
    const src = selectedSourceFilter.value.toUpperCase();
    list = list.filter(s => (s.submission_source || "DIRECT").toUpperCase() === src);
  }

  // Date filter
  if (dateRangePreset.value === "30d") {
    const cutoff = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    list = list.filter(s => new Date(s.submitted_at) >= cutoff);
  } else if (dateRangePreset.value === "90d") {
    const cutoff = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000);
    list = list.filter(s => new Date(s.submitted_at) >= cutoff);
  } else if (dateRangePreset.value === "year") {
    const cutoff = new Date(Date.now() - 365 * 24 * 60 * 60 * 1000);
    list = list.filter(s => new Date(s.submitted_at) >= cutoff);
  } else if (dateRangePreset.value === "custom") {
    if (dateFrom.value) {
      const from = new Date(dateFrom.value);
      list = list.filter(s => new Date(s.submitted_at) >= from);
    }
    if (dateTo.value) {
      const to = new Date(dateTo.value);
      to.setHours(23, 59, 59, 999);
      list = list.filter(s => new Date(s.submitted_at) <= to);
    }
  }

  return list;
});

// Active Organisation Count
const activeOrgCount = computed(() => {
  const set = new Set(filteredSubmissions.value.map(s => (s.company_name || '').trim().toLowerCase()));
  return set.size;
});

// Portfolio Average Score
const portfolioAvgScore = computed(() => {
  const subs = filteredSubmissions.value;
  if (!subs.length) return 0;
  const valid = subs.map(s => parseFloat(s.overall_avg || 0)).filter(v => !isNaN(v));
  if (!valid.length) return 0;
  return Math.round((valid.reduce((a, b) => a + b, 0) / valid.length) * 100) / 100;
});

const portfolioLevel = computed(() => {
  const s = portfolioAvgScore.value;
  if (s <= 6) return "Level 1 — Foundational";
  if (s <= 14) return "Level 2 — Early Progress";
  return "Level 3 — Developing";
});

// Pillar Averages
const pillarAverages = computed(() => {
  const subs = filteredSubmissions.value;
  return CORE_PILLARS.map(p => {
    const vals = subs.map(s => {
      const v = s[p.key];
      return (v != null && v !== 'NA') ? parseFloat(v) : null;
    }).filter(v => v !== null && !isNaN(v));
    const avg = vals.length ? Math.round((vals.reduce((a, b) => a + b, 0) / vals.length) * 10) / 10 : 0;
    return {
      key: p.key,
      label: p.label,
      short: p.short,
      avg,
    };
  });
});

const strongestPillar = computed(() => {
  const list = [...pillarAverages.value].sort((a, b) => b.avg - a.avg);
  return list[0] || { label: "N/A", avg: 0 };
});

const weakestPillar = computed(() => {
  const list = [...pillarAverages.value].sort((a, b) => a.avg - b.avg);
  return list[0] || { label: "N/A", avg: 0 };
});

// Maturity Distribution
const maturityLegend = computed(() => {
  const subs = filteredSubmissions.value;
  const counts = { l1: 0, l2: 0, l3: 0 };
  subs.forEach(s => {
    const avg = parseFloat(s.overall_avg || 0);
    if (avg <= 6) counts.l1++;
    else if (avg <= 14) counts.l2++;
    else counts.l3++;
  });
  const total = subs.length || 1;
  return [
    { label: "Level 1 — Foundational", range: "0 – 6 pts", count: counts.l1, pct: Math.round((counts.l1 / total) * 100), color: "#E05A47" },
    { label: "Level 2 — Early Progress", range: "7 – 14 pts", count: counts.l2, pct: Math.round((counts.l2 / total) * 100), color: "#D97706" },
    { label: "Level 3 — Developing", range: "15 – 20 pts", count: counts.l3, pct: Math.round((counts.l3 / total) * 100), color: "#04907C" },
  ];
});

// Organisation Rankings
const orgSummaryMap = computed(() => {
  const map = {};
  filteredSubmissions.value.forEach(s => {
    const name = (s.company_name || 'Unknown Organisation').trim();
    if (!map[name]) {
      map[name] = { name, scores: [], count: 0 };
    }
    map[name].count++;
    if (s.overall_avg != null) {
      map[name].scores.push(parseFloat(s.overall_avg));
    }
  });

  return Object.values(map).map(item => {
    const avg = item.scores.length
      ? Math.round((item.scores.reduce((a, b) => a + b, 0) / item.scores.length) * 100) / 100
      : 0;
    return {
      name: item.name,
      count: item.count,
      avg,
    };
  });
});

const topOrgs = computed(() => {
  return [...orgSummaryMap.value].sort((a, b) => b.avg - a.avg).slice(0, 5);
});

const bottomOrgs = computed(() => {
  return [...orgSummaryMap.value].sort((a, b) => a.avg - b.avg).slice(0, 5);
});

// Demographic Segment Breakdowns across portfolio
const ndStats = computed(() => {
  const subs = filteredSubmissions.value;
  const ndScores = [];
  const ntScores = [];

  subs.forEach(s => {
    const ans = s.answers || {};
    const ndStatus = String(ans.is_neurodivergent || s.is_neurodivergent || '').toLowerCase().trim();
    const score = parseFloat(s.overall_avg || 0);

    if (ndStatus === 'yes') ndScores.push(score);
    else if (ndStatus === 'no') ntScores.push(score);
  });

  const ndAvg = ndScores.length ? Math.round((ndScores.reduce((a, b) => a + b, 0) / ndScores.length) * 100) / 100 : 0;
  const ntAvg = ntScores.length ? Math.round((ntScores.reduce((a, b) => a + b, 0) / ntScores.length) * 100) / 100 : 0;
  const diff = Math.round((ntAvg - ndAvg) * 100) / 100;

  return {
    ndCount: ndScores.length,
    ntCount: ntScores.length,
    ndAvg,
    ntAvg,
    diff,
  };
});

const ndCount = computed(() => ndStats.value.ndCount);
const ntCount = computed(() => ndStats.value.ntCount);
const ndAvgScore = computed(() => ndStats.value.ndAvg);
const ntAvgScore = computed(() => ndStats.value.ntAvg);
const ndDiff = computed(() => ndStats.value.diff);
const ndDiffClass = computed(() => ndDiff.value > 0.5 ? 'gap-alert' : 'gap-aligned');

const roleStats = computed(() => {
  const subs = filteredSubmissions.value;
  const leaderScores = [];
  const icScores = [];

  subs.forEach(s => {
    const ans = s.answers || {};
    const roleStr = String(ans.role || s.role || s.designation || '').toLowerCase().trim();
    const score = parseFloat(s.overall_avg || 0);

    if (roleStr.includes('leader') || roleStr.includes('manager') || roleStr.includes('exec') || roleStr.includes('c-suite')) {
      leaderScores.push(score);
    } else if (roleStr.includes('contributor') || roleStr.includes('individual') || roleStr.includes('engineer') || roleStr.includes('specialist')) {
      icScores.push(score);
    }
  });

  const leaderAvg = leaderScores.length ? Math.round((leaderScores.reduce((a, b) => a + b, 0) / leaderScores.length) * 100) / 100 : 0;
  const icAvg = icScores.length ? Math.round((icScores.reduce((a, b) => a + b, 0) / icScores.length) * 100) / 100 : 0;
  const diff = Math.round((leaderAvg - icAvg) * 100) / 100;

  return {
    leaderCount: leaderScores.length,
    icCount: icScores.length,
    leaderAvg,
    icAvg,
    diff,
  };
});

const leaderCount = computed(() => roleStats.value.leaderCount);
const icCount = computed(() => roleStats.value.icCount);
const leaderAvgScore = computed(() => roleStats.value.leaderAvg);
const icAvgScore = computed(() => roleStats.value.icAvg);
const leaderDiff = computed(() => roleStats.value.diff);
const leaderDiffClass = computed(() => Math.abs(leaderDiff.value) > 0.5 ? 'gap-alert' : 'gap-aligned');

function getMaturityClass(score) {
  if (score == null) return "badge-neutral";
  const s = parseFloat(score);
  if (s <= 6) return "badge-level-1";
  if (s <= 14) return "badge-level-2";
  return "badge-level-3";
}

function navigateToOrg(org) {
  router.push({ path: "/admin/organisations", query: { search: org.name } });
}

// Chart Renderers
function destroyCharts() {
  if (radarInstance) { radarInstance.destroy(); radarInstance = null; }
  if (donutInstance) { donutInstance.destroy(); donutInstance = null; }
  if (barInstance)   { barInstance.destroy();   barInstance = null; }
  if (trendInstance) { trendInstance.destroy(); trendInstance = null; }
}

async function renderCharts() {
  await nextTick();
  destroyCharts();

  if (!filteredSubmissions.value.length) return;

  // 1. Radar Chart: 8 Core Pillars
  if (radarChartRef.value) {
    const labels = pillarAverages.value.map(p => p.short);
    const dataVals = pillarAverages.value.map(p => p.avg);

    radarInstance = new Chart(radarChartRef.value, {
      type: "radar",
      data: {
        labels,
        datasets: [{
          label: "Portfolio Pillar Average",
          data: dataVals,
          backgroundColor: "rgba(4, 144, 124, 0.20)",
          borderColor: "#04907C",
          borderWidth: 2.2,
          pointBackgroundColor: "#161057",
          pointBorderColor: "#FFFFFF",
          pointBorderWidth: 1.5,
          pointRadius: 4.5,
          pointHoverRadius: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Score: ${ctx.raw} / 20 (${Math.round((ctx.raw / 20) * 100)}%)`
            }
          }
        },
        scales: {
          r: {
            min: 0,
            max: 20,
            ticks: {
              stepSize: 5,
              color: "#94A3B8",
              font: { size: 10, family: 'Geist' }
            },
            grid: { color: "rgba(22, 16, 87, 0.08)" },
            angleLines: { color: "rgba(22, 16, 87, 0.08)" },
            pointLabels: {
              color: "#161057",
              font: { size: 11, weight: "600", family: 'Geist' }
            }
          }
        }
      }
    });
  }

  // 2. Donut Chart: Maturity Tiers
  if (donutChartRef.value) {
    const legend = maturityLegend.value;
    donutInstance = new Chart(donutChartRef.value, {
      type: "doughnut",
      data: {
        labels: legend.map(l => l.label),
        datasets: [{
          data: legend.map(l => l.count),
          backgroundColor: legend.map(l => l.color),
          borderWidth: 2,
          borderColor: "#FFFFFF",
          hoverOffset: 4,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "68%",
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.label}: ${ctx.raw} audits`
            }
          }
        }
      }
    });
  }

  // 3. Ranked Bar Chart: Weakest to Strongest
  if (barChartRef.value) {
    const sorted = [...pillarAverages.value].sort((a, b) => a.avg - b.avg);
    const labels = sorted.map(s => s.label);
    const dataVals = sorted.map(s => s.avg);
    const barColors = sorted.map(s => {
      if (s.avg <= 6) return "#E05A47";
      if (s.avg <= 14) return "#D97706";
      return "#04907C";
    });

    barInstance = new Chart(barChartRef.value, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "Average Score / 20",
          data: dataVals,
          backgroundColor: barColors,
          borderRadius: 6,
          borderSkipped: false,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Score: ${ctx.raw} / 20 (${Math.round((ctx.raw / 20) * 100)}%)`
            }
          }
        },
        scales: {
          x: {
            min: 0,
            max: 20,
            grid: { color: "rgba(22, 16, 87, 0.06)" },
            ticks: { stepSize: 5, color: "#64748B", font: { family: 'Geist' } }
          },
          y: {
            grid: { display: false },
            ticks: { color: "#161057", font: { weight: "600", family: 'Geist' } }
          }
        }
      }
    });
  }

  // 4. Monthly Trend Line Chart
  if (trendChartRef.value) {
    const monthMap = {};
    filteredSubmissions.value.forEach(s => {
      const { key, label } = getISTMonthKey(s.submitted_at);
      if (!monthMap[key]) {
        monthMap[key] = { label, scores: [] };
      }
      if (s.overall_avg != null) {
        monthMap[key].scores.push(parseFloat(s.overall_avg));
      }
    });

    const entries = Object.keys(monthMap).sort().slice(-12).map(k => monthMap[k]);
    const labels = entries.length ? entries.map(e => e.label) : ["Current Month"];
    const trendData = entries.length ? entries.map(e => {
      return e.scores.length ? Math.round((e.scores.reduce((a, b) => a + b, 0) / e.scores.length) * 100) / 100 : 0;
    }) : [portfolioAvgScore.value];

    trendInstance = new Chart(trendChartRef.value, {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "Monthly Average Score",
          data: trendData,
          borderColor: "#161057",
          backgroundColor: "rgba(22, 16, 87, 0.05)",
          borderWidth: 2.5,
          tension: 0.3,
          fill: true,
          pointBackgroundColor: "#04907C",
          pointBorderColor: "#FFFFFF",
          pointBorderWidth: 2,
          pointRadius: 4.5,
          pointHoverRadius: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `Monthly Avg: ${ctx.raw} / 20`
            }
          }
        },
        scales: {
          y: {
            min: 0,
            max: 20,
            grid: { color: "rgba(22, 16, 87, 0.06)" },
            ticks: { stepSize: 5, color: "#64748B", font: { family: 'Geist' } }
          },
          x: {
            grid: { display: false },
            ticks: { color: "#161057", font: { family: 'Geist' } }
          }
        }
      }
    });
  }
}

// Watch filters to re-render charts
watch([selectedOrgFilter, dateRangePreset, dateFrom, dateTo, selectedSourceFilter], () => {
  renderCharts();
});

async function loadData() {
  loading.value = true;
  error.value = "";
  try {
    const subs = await getSubmissions();
    allSubmissions.value = subs || [];
  } catch (e) {
    console.error("Failed to load analytics submissions:", e);
    error.value = e.message || "Failed to load analytics data.";
  } finally {
    loading.value = false;
    await renderCharts();
  }
}

onMounted(() => {
  loadData();
});

onBeforeUnmount(() => {
  destroyCharts();
});
</script>

<style scoped>
.analytics-page {
  padding: 0 0 40px 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Hero Section */
.hero-section {
  background: #FAF9F5;
  border-bottom: 1.5px solid rgba(22, 16, 87, 0.10);
  padding: 24px 32px;
}

.hero-content {
  max-width: 1360px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-header-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
}

.hero-title {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.85rem;
  font-weight: 700;
  color: var(--primary, #161057);
  letter-spacing: -0.02em;
}

.hero-subtitle {
  font-size: 0.92rem;
  color: #64748B;
  margin-top: 4px;
  max-width: 820px;
  line-height: 1.5;
}

.spin-icon {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Filter Controls Card */
.search-banner-card {
  display: flex;
  align-items: center;
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 12px;
  padding: 8px 16px;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.08);
  gap: 12px;
  flex-wrap: wrap;
}

.filter-item-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.filter-label {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--primary, #161057);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  white-space: nowrap;
}

.filter-select-inner {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #F8FAFC;
  border: 1px solid #CBD5E1;
  border-radius: 8px;
  padding: 5px 10px;
}
.filter-select-inner svg {
  color: var(--primary, #161057);
  flex-shrink: 0;
}
.filter-select-inner select {
  border: none;
  background: transparent;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--primary, #161057);
  outline: none;
  cursor: pointer;
  padding: 0;
}

.search-divider {
  width: 1px;
  height: 28px;
  background: #E2E8F0;
}

.custom-dates-row {
  display: flex;
  align-items: center;
  gap: 6px;
}
.custom-dates-row input {
  padding: 4px 8px;
  font-size: 0.8rem;
  border: 1px solid #CBD5E1;
  border-radius: 6px;
}
.to-text {
  font-size: 0.75rem;
  color: #64748B;
}

.btn-reset-filters {
  background: #FEE2E2;
  color: #991B1B;
  border: 1px solid #FECACA;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  margin-left: auto;
  transition: all 0.15s ease;
}
.btn-reset-filters:hover {
  background: #FCA5A5;
}

/* Layout */
.analytics-content-layout {
  max-width: 1360px;
  margin: 0 auto;
  padding: 0 32px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* Loading & Empty Cards */
.analytics-loading-card, .analytics-empty-card {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 14px;
  padding: 48px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: #64748B;
}
.empty-icon {
  font-size: 2.5rem;
}
.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #E2E8F0;
  border-top-color: var(--accent, #04907C);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* KPI Grid */
.metrics-kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}

.kpi-card {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.06);
}

.kpi-icon-box {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.kpi-blue { background: #EFF6FF; color: #1D4ED8; border: 1px solid #BFDBFE; }
.kpi-green { background: #ECFDF5; color: #047857; border: 1px solid #A7F3D0; }
.kpi-amber { background: #FFFBEB; color: #B45309; border: 1px solid #FDE68A; }
.kpi-red { background: #FEF2F2; color: #B91C1C; border: 1px solid #FECACA; }

.kpi-content {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.kpi-label {
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  color: #64748B;
  letter-spacing: 0.04em;
}

.kpi-value-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 2px;
}
.kpi-value {
  font-size: 1.6rem;
  font-weight: 800;
  color: var(--primary, #161057);
  font-family: var(--font-heading, 'Fraunces', serif);
}
.kpi-denom {
  font-size: 0.85rem;
  font-weight: 600;
  color: #64748B;
}
.kpi-sub {
  font-size: 0.75rem;
  color: #64748B;
}
.kpi-badge {
  font-size: 0.68rem;
  padding: 2px 7px;
  border-radius: 99px;
  font-weight: 700;
}

.kpi-text-value {
  display: flex;
  flex-direction: column;
  margin-top: 2px;
}
.kpi-bold-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--primary, #161057);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.kpi-strong-score {
  font-size: 0.78rem;
  font-weight: 700;
  color: #047857;
}
.kpi-weak-score {
  font-size: 0.78rem;
  font-weight: 700;
  color: #B91C1C;
}

/* Chart Cards */
.charts-row-2 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
  gap: 20px;
}

.chart-card, .chart-card-full, .ranking-card, .segment-breakdown-card {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 14px;
  padding: 20px;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.06);
}

.chart-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  gap: 12px;
}

.chart-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--primary, #161057);
}
.chart-sub {
  font-size: 0.8rem;
  color: #64748B;
  display: block;
  margin-top: 2px;
}

.chart-dim-badge, .rank-tag {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--primary, #161057);
  background: #F1F5F9;
  border: 1px solid #CBD5E1;
  padding: 3px 8px;
  border-radius: 6px;
  white-space: nowrap;
}
.rank-top { background: #ECFDF5; color: #047857; border-color: #A7F3D0; }
.rank-priority { background: #FEF2F2; color: #B91C1C; border-color: #FECACA; }

.radar-container {
  height: 320px;
  position: relative;
}

.donut-container {
  display: flex;
  align-items: center;
  gap: 20px;
  height: 320px;
}

.donut-canvas-wrap {
  flex: 1;
  height: 100%;
  position: relative;
}

.donut-legend-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.legend-row {
  display: flex;
  align-items: center;
  gap: 10px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  padding: 8px 12px;
}
.legend-color-tag {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
}
.legend-info {
  display: flex;
  flex-direction: column;
  flex: 1;
}
.legend-name {
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--primary, #161057);
}
.legend-range {
  font-size: 0.7rem;
  color: #64748B;
}
.legend-count-box {
  display: flex;
  align-items: baseline;
  gap: 4px;
}
.legend-count-box strong {
  font-size: 1rem;
  color: var(--primary, #161057);
}
.legend-pct {
  font-size: 0.75rem;
  color: #64748B;
}

.bar-chart-container, .trend-chart-container {
  height: 260px;
  position: relative;
}

/* Ranking Lists */
.rank-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rank-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.rank-row:hover {
  background: #EFF6FF;
  border-color: var(--primary, #161057);
  transform: translateX(2px);
}

.rank-badge {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 800;
  flex-shrink: 0;
}
.rank-badge.top { background: #ECFDF5; color: #047857; }
.rank-badge.priority { background: #FEF2F2; color: #B91C1C; }

.rank-details {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}
.rank-org-name {
  font-size: 0.88rem;
  font-weight: 700;
  color: var(--primary, #161057);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.rank-sub-meta {
  font-size: 0.72rem;
  color: #64748B;
}

.rank-bar-wrap {
  width: 100px;
  flex-shrink: 0;
}
.rank-bar-bg {
  height: 6px;
  background: #E2E8F0;
  border-radius: 99px;
  overflow: hidden;
}
.rank-bar-fill {
  height: 100%;
  border-radius: 99px;
}
.rank-bar-fill.green { background: #04907C; }
.rank-bar-fill.coral { background: #E05A47; }

.rank-score-pill {
  font-family: 'Geist', monospace;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--primary, #161057);
  background: #FFFFFF;
  border: 1px solid #CBD5E1;
  padding: 3px 8px;
  border-radius: 6px;
  white-space: nowrap;
}
.rank-score-pill.priority {
  color: #B91C1C;
  border-color: #FECACA;
  background: #FFF5F5;
}

/* Segment Breakdown Cards */
.segment-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(420px, 1fr));
  gap: 16px;
}

.seg-mini-card {
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.smc-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
.smc-icon {
  font-size: 1.5rem;
}
.smc-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--primary, #161057);
}
.smc-desc {
  font-size: 0.75rem;
  color: #64748B;
}

.smc-groups-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.smc-group-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.82rem;
}
.smc-group-name {
  width: 140px;
  font-weight: 600;
  color: var(--primary, #161057);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.smc-bar-box {
  flex: 1;
  height: 8px;
  background: #E2E8F0;
  border-radius: 99px;
  overflow: hidden;
}
.smc-bar-fill {
  height: 100%;
  background: var(--accent, #04907C);
  border-radius: 99px;
}
.smc-group-score {
  font-family: 'Geist', monospace;
  font-weight: 700;
  color: var(--primary, #161057);
  width: 60px;
  text-align: right;
}
.smc-group-count {
  font-size: 0.72rem;
  color: #64748B;
  width: 65px;
}

.smc-variance-tag {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 0.78rem;
}
.gap-alert {
  background: #FEF2F2;
  color: #991B1B;
  border: 1px solid #FECACA;
}
.gap-aligned {
  background: #ECFDF5;
  color: #065F46;
  border: 1px solid #A7F3D0;
}

@media (max-width: 900px) {
  .hero-section {
    padding: 16px 20px;
  }
  .analytics-content-layout {
    padding: 0 20px;
  }
  .charts-row-2 {
    grid-template-columns: 1fr;
  }
  .donut-container {
    flex-direction: column;
    height: auto;
  }
  .donut-canvas-wrap {
    height: 220px;
    width: 100%;
  }
  .donut-legend-list {
    width: 100%;
  }
  .search-banner-card {
    flex-direction: column;
    align-items: stretch;
  }
  .search-divider {
    display: none;
  }
}

/* Skeleton Loading for Analytics Dashboard */
.analytics-skeleton-wrapper {
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.skeleton-shimmer {
  background: linear-gradient(90deg, #ece9e6 25%, #f7f6f4 50%, #ece9e6 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: 4px;
}
@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
.skeleton-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
}
.sk-kpi-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  flex-shrink: 0;
}
.sk-kpi-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  flex: 1;
}
.sk-kpi-label {
  width: 55%;
  height: 14px;
  border-radius: 4px;
}
.sk-kpi-val {
  width: 40%;
  height: 24px;
  border-radius: 4px;
}
.skeleton-chart {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.sk-chart-title {
  width: 40%;
  height: 20px;
  border-radius: 4px;
}
.sk-chart-canvas {
  width: 100%;
  height: 240px;
  border-radius: 8px;
}

</style>
