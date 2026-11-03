<template>
  <div class="dashboard-page animate-in">
    <!-- Hero / Main Search Banner matching Reference Image -->
    <section class="hero-section" aria-label="Dashboard Search Banner">
      <div class="hero-content">
        <h1 class="hero-title">Neurodiversity &amp; Inclusion Audits</h1>
        <p class="hero-subtitle">
          Explore latest organization audit submissions, evaluate workplace inclusion maturity levels, and manage actionable reports.
        </p>

        <!-- Search Bar with Location/Sector Dropdown and CTA -->
        <div class="search-banner-card">
          <div class="search-input-group">
            <svg class="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" aria-hidden="true">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
            </svg>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search organisation, leader, designation, or email…"
              aria-label="Search submissions"
              @keyup.enter="applySearch"
            />
          </div>

          <div class="search-divider"></div>

          <div class="search-sector-group">
            <svg class="location-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
              <circle cx="12" cy="10" r="3"></circle>
            </svg>
            <select v-model="selectedSector" aria-label="Filter by Sector or Location">
              <option value="">All Sectors &amp; Locations</option>
              <option value="tech">Technology &amp; Software</option>
              <option value="finance">Finance &amp; Banking</option>
              <option value="health">Healthcare &amp; Pharma</option>
              <option value="consulting">Enterprise Consulting</option>
              <option value="retail">Retail &amp; Media</option>
            </select>
          </div>

          <button class="hero-search-btn" @click="applySearch" type="button">
            Search
          </button>
        </div>
      </div>
    </section>

    <!-- Subheader / Results Count & Action Controls -->
    <div class="results-header-bar">
      <div class="results-header-left">
        <h2 class="results-title">Total Audits</h2>
        <span class="results-count-pill">{{ filteredSubmissions.length }} audit results</span>

        <!-- Active Filter Tags -->
        <div class="active-tags-list" v-if="hasActiveFilters">
          <span v-if="searchQuery" class="filter-tag" @click="searchQuery = ''">
            Search: "{{ searchQuery }}" <span class="tag-close">✕</span>
          </span>
          <span v-if="selectedSector" class="filter-tag" @click="selectedSector = ''">
            Sector: {{ selectedSectorLabel }} <span class="tag-close">✕</span>
          </span>
          <span v-if="filterStatusPending" class="filter-tag" @click="filterStatusPending = false">
            Status: Pending Review <span class="tag-close">✕</span>
          </span>
          <span v-if="filterStatusSent" class="filter-tag" @click="filterStatusSent = false">
            Status: Delivered <span class="tag-close">✕</span>
          </span>
          <span v-if="selectedMaturityLevels.length" class="filter-tag" @click="selectedMaturityLevels = []">
            Maturity: {{ selectedMaturityLevels.join(', ') }} <span class="tag-close">✕</span>
          </span>
          <button class="btn-clear-all-tags" @click="resetFilters" type="button">Clear All</button>
        </div>
      </div>

      <div class="results-header-right">
        <!-- View Toggle (Cards vs Table) -->
        <div class="view-toggle-group" role="group" aria-label="View switch">
          <button
            class="view-btn"
            :class="{ active: viewMode === 'cards' }"
            @click="viewMode = 'cards'"
            title="Card View"
            aria-label="Cards view"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>
            Cards
          </button>
          <button
            class="view-btn"
            :class="{ active: viewMode === 'table' }"
            @click="viewMode = 'table'"
            title="Table View"
            aria-label="Table view"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"></line><line x1="8" y1="12" x2="21" y2="12"></line><line x1="8" y1="18" x2="21" y2="18"></line><line x1="3" y1="6" x2="3.01" y2="6"></line><line x1="3" y1="12" x2="3.01" y2="12"></line><line x1="3" y1="18" x2="3.01" y2="18"></line></svg>
            Table
          </button>
        </div>

        <!-- Sort Select -->
        <div class="sort-wrapper">
          <label class="sort-label" for="sort-select">Sort by:</label>
          <select id="sort-select" v-model="sortBy" class="sort-select">
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="score_desc">Highest Score (20 → 0)</option>
            <option value="score_asc">Lowest Score (0 → 20)</option>
            <option value="urgent">Pending Review First</option>
          </select>
        </div>

        <!-- Action CTAs -->
        <button class="btn btn-outline-retro" @click="copyAuditLink" type="button" :title="linkCopied ? 'Link Copied!' : 'Copy Audit Link'">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
          {{ linkCopied ? 'Copied!' : 'Copy Link' }}
        </button>

        <button class="btn btn-primary-retro" @click="downloadReport" :disabled="downloading" type="button">
          {{ downloading ? 'Exporting…' : '⬇ Export CSV' }}
        </button>
      </div>
    </div>

    <!-- Main Two-Column Layout -->
    <div class="main-dashboard-grid">
      <!-- Left Sidebar: Filters Card -->
      <aside class="filters-sidebar-card" :class="{ collapsed: isFiltersCollapsed }" aria-label="Audit Filters">
        <div class="filters-card-header" @click="isFiltersCollapsed = !isFiltersCollapsed">
          <span class="filters-title">Filters</span>
          <button class="filter-toggle-icon" type="button" :aria-label="isFiltersCollapsed ? 'Expand filters' : 'Collapse filters'">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
              :class="{ 'rotate-180': isFiltersCollapsed }"
            >
              <polyline points="6 9 12 15 18 9"></polyline>
            </svg>
          </button>
        </div>

        <div v-show="!isFiltersCollapsed" class="filters-body">
          <!-- Date Posted / Submitted Filter -->
          <div class="filter-section">
            <label class="filter-section-title" for="date-range-select">Date posted</label>
            <select id="date-range-select" v-model="dateRangePreset" class="filter-dropdown">
              <option value="all">All Time</option>
              <option value="today">Today</option>
              <option value="week">Last Week</option>
              <option value="month">Last Month</option>
              <option value="quarter">Last Quarter</option>
              <option value="custom">Custom Date Range</option>
            </select>

            <div v-if="dateRangePreset === 'custom'" class="custom-date-inputs">
              <div class="date-field">
                <span class="date-label">From:</span>
                <input v-model="dateFrom" type="date" class="date-picker-input" />
              </div>
              <div class="date-field">
                <span class="date-label">To:</span>
                <input v-model="dateTo" type="date" class="date-picker-input" />
              </div>
            </div>
          </div>

          <!-- Audit Status Filter (Job Type in Reference) -->
          <div class="filter-section">
            <span class="filter-section-title">Audit Status</span>
            <div class="filter-checkbox-grid">
              <label class="custom-checkbox-row">
                <input type="checkbox" v-model="filterStatusPending" />
                <span class="checkmark"></span>
                <span class="checkbox-label">Pending Review</span>
                <span class="count-pill red">{{ countPending }}</span>
              </label>

              <label class="custom-checkbox-row">
                <input type="checkbox" v-model="filterStatusSent" />
                <span class="checkmark"></span>
                <span class="checkbox-label">Delivered / Sent</span>
                <span class="count-pill green">{{ countSent }}</span>
              </label>

              <label class="custom-checkbox-row">
                <input type="checkbox" v-model="filterStatusDraft" />
                <span class="checkmark"></span>
                <span class="checkbox-label">Draft / In Progress</span>
                <span class="count-pill slate">{{ countDraft }}</span>
              </label>
            </div>
          </div>

          <!-- Maturity Level Filter (Salary Range in Reference) -->
          <div class="filter-section">
            <span class="filter-section-title">Maturity Level</span>
            <div class="filter-checkbox-grid">
              <label class="custom-checkbox-row">
                <input type="checkbox" value="Leading" v-model="selectedMaturityLevels" />
                <span class="checkmark"></span>
                <span class="checkbox-label">Leading (16–20 pts)</span>
              </label>

              <label class="custom-checkbox-row">
                <input type="checkbox" value="Maturing" v-model="selectedMaturityLevels" />
                <span class="checkmark"></span>
                <span class="checkbox-label">Maturing (12–15.9 pts)</span>
              </label>

              <label class="custom-checkbox-row">
                <input type="checkbox" value="Developing" v-model="selectedMaturityLevels" />
                <span class="checkmark"></span>
                <span class="checkbox-label">Developing (8–11.9 pts)</span>
              </label>

              <label class="custom-checkbox-row">
                <input type="checkbox" value="Emerging" v-model="selectedMaturityLevels" />
                <span class="checkmark"></span>
                <span class="checkbox-label">Emerging (&lt; 8 pts)</span>
              </label>
            </div>
          </div>

          <!-- Workplace / Urgency Filter (On site/Remote in Reference) -->
          <div class="filter-section">
            <span class="filter-section-title">Urgency &amp; Focus</span>
            <div class="filter-checkbox-grid">
              <label class="custom-checkbox-row">
                <input type="checkbox" v-model="filterUrgentOnly" />
                <span class="checkmark"></span>
                <span class="checkbox-label">Action Needed Only</span>
              </label>

              <label class="custom-checkbox-row">
                <input type="checkbox" v-model="filterHighScorers" />
                <span class="checkmark"></span>
                <span class="checkbox-label">Top Quartile (&gt;15 pts)</span>
              </label>
            </div>
          </div>

          <!-- Reset All Filters Link -->
          <button class="btn-reset-filters" @click="resetFilters" type="button">
            Reset All Filters
          </button>
        </div>
      </aside>

      <!-- Right Main Content Area: Cards or Table -->
      <main class="submissions-main-content">
        <!-- Top KPI Quick Stats Bar -->
        <div class="kpi-metric-strip">
          <div class="kpi-chip">
            <div class="kpi-icon-wrap blue">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            </div>
            <div class="kpi-text">
              <span class="kpi-label">Total Audits</span>
              <strong class="kpi-value">{{ stats.total }}</strong>
            </div>
            <span v-if="stats.weekNew > 0" class="kpi-badge green">+{{ stats.weekNew }} this wk</span>
          </div>

          <div class="kpi-chip" :class="{ 'urgent-border': stats.pending > 0 }">
            <div class="kpi-icon-wrap red">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            </div>
            <div class="kpi-text">
              <span class="kpi-label">Pending Review</span>
              <strong class="kpi-value">{{ stats.pending }}</strong>
            </div>
            <span v-if="stats.pending > 0" class="kpi-badge red">Action Needed</span>
          </div>

          <div class="kpi-chip">
            <div class="kpi-icon-wrap green">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            </div>
            <div class="kpi-text">
              <span class="kpi-label">Reports Delivered</span>
              <strong class="kpi-value">{{ stats.sent }}</strong>
            </div>
            <span class="kpi-subtext">of {{ stats.total }}</span>
          </div>

          <div class="kpi-chip">
            <div class="kpi-icon-wrap teal">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
            </div>
            <div class="kpi-text">
              <span class="kpi-label">Avg. Maturity Score</span>
              <strong class="kpi-value">{{ stats.avgScore }}<small class="kpi-scale">/20</small></strong>
            </div>
          </div>
        </div>

        <!-- Loading State: Progressive Skeleton Cards -->
        <div v-if="loading" class="overview-skeleton-list" aria-busy="true">
          <div v-for="i in 4" :key="i" class="overview-skeleton-card">
            <div class="skeleton-header">
              <div class="skeleton-shimmer skeleton-badge"></div>
              <div class="skeleton-shimmer skeleton-score"></div>
            </div>
            <div class="skeleton-shimmer skeleton-title-lg"></div>
            <div class="skeleton-shimmer skeleton-text-sub"></div>
            <div class="skeleton-bars-grid">
              <div v-for="j in 8" :key="j" class="skeleton-shimmer skeleton-mini-bar"></div>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else-if="!filteredSubmissions.length" class="empty-results-card">
          <div class="empty-icon-wrap">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <circle cx="11" cy="11" r="8"></circle>
              <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
              <line x1="8" y1="11" x2="14" y2="11"></line>
            </svg>
          </div>
          <h3>No audit submissions found</h3>
          <p>We couldn't find any submissions matching your active search and filter criteria.</p>
          <button class="btn btn-primary-retro" @click="resetFilters" type="button">Reset Filters</button>
        </div>

        <!-- CARDS VIEW (Matching Reference Image) -->
        <div v-else-if="viewMode === 'cards'" class="audit-cards-list">
          <article
            v-for="sub in paginatedSubmissions"
            :key="sub.id"
            class="audit-card"
            @click="goToSubmission(sub.id)"
          >
            <!-- Card Top Header -->
            <div class="card-header-row">
              <div class="card-identity">
                <!-- Org Avatar Monogram -->
                <div class="org-avatar-badge" :style="{ backgroundColor: getAvatarColor(sub.company_name) }">
                  {{ getInitials(sub.company_name) }}
                </div>

                <div class="org-title-group">
                  <div class="title-and-badges">
                    <h3 class="card-org-name">{{ sub.company_name }}</h3>

                    <!-- Status Pill (Delivered / Pending) -->
                    <span :class="['card-badge', 'status-badge', sub.status === 'sent' ? 'badge-delivered' : 'badge-pending']">
                      {{ sub.status === 'sent' ? 'Delivered' : 'Pending Review' }}
                    </span>

                    <!-- Maturity Level Badge -->
                    <span :class="['card-badge', 'level-badge', getMaturityBadgeClass(sub.overall_level)]">
                      {{ sub.overall_level || 'Evaluating' }}
                    </span>
                  </div>

                  <p class="card-contact-name">
                    {{ sub.name }} <span v-if="sub.designation" class="contact-role">· {{ sub.designation }}</span>
                  </p>
                </div>
              </div>

              <!-- Location / Region Indicator (Top-Right) -->
              <div class="card-location">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path>
                  <circle cx="12" cy="10" r="3"></circle>
                </svg>
                <span>{{ getLocation(sub) }}</span>
              </div>
            </div>

            <!-- Bullet Points Section (Matching Reference Image) -->
            <ul class="card-bullets-list">
              <li>
                • Overall Maturity Score: <strong>{{ sub.overall_avg }}/20</strong>
                <span class="bullet-subscores">
                  · Maturity Tier: {{ sub.overall_level || 'Evaluating' }}
                  · Domain: {{ getSector(sub) }}
                </span>
              </li>
              <li>
                • Submitted on {{ fmtDate(sub.submitted_at) }}
                <span class="bullet-email">· Recipient: {{ sub.email }}</span>
                <span v-if="sub.contact_number" class="bullet-phone">· Contact: {{ sub.contact_number }}</span>
              </li>
            </ul>

            <!-- Bottom Action Row -->
            <div class="card-action-row" @click.stop>
              <div class="card-footer-meta">
                <span class="sector-tag">{{ getSector(sub) }}</span>
              </div>

              <div class="card-buttons">
                <button
                  class="card-csv-btn"
                  @click="downloadOne(sub)"
                  title="Download CSV report"
                  aria-label="Download CSV"
                  type="button"
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                </button>

                <!-- Coral / Accent Action CTA Button ("Apply Now" in Reference) -->
                <button
                  class="card-action-btn"
                  @click="goToSubmission(sub.id)"
                  type="button"
                >
                  Review Audit
                </button>
              </div>
            </div>
          </article>
        </div>

        <!-- TABLE VIEW -->
        <div v-else class="audit-table-card">
          <div class="table-responsive">
            <table class="data-table" role="table">
              <thead>
                <tr>
                  <th scope="col">Organisation</th>
                  <th scope="col">Respondent</th>
                  <th scope="col">Job Role</th>
                  <th scope="col">Location</th>
                  <th scope="col">Submitted</th>
                  <th scope="col">Score</th>
                  <th scope="col">Maturity</th>
                  <th scope="col">Status</th>
                  <th scope="col" class="text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="sub in paginatedSubmissions"
                  :key="sub.id"
                  @click="goToSubmission(sub.id)"
                  class="table-row-clickable"
                >
                  <td class="font-bold org-col">
                    <div class="table-org-wrap">
                      <span class="table-mini-avatar" :style="{ backgroundColor: getAvatarColor(sub.company_name) }">
                        {{ getInitials(sub.company_name) }}
                      </span>
                      {{ sub.company_name }}
                    </div>
                  </td>
                  <td>{{ sub.name }}</td>
                  <td class="text-muted">{{ sub.designation || '—' }}</td>
                  <td class="text-muted">{{ getLocation(sub) }}</td>
                  <td class="text-muted">{{ fmtDate(sub.submitted_at) }}</td>
                  <td class="score-col"><strong>{{ sub.overall_avg }}</strong><small>/20</small></td>
                  <td>
                    <span :class="['table-pill', getMaturityBadgeClass(sub.overall_level)]">
                      {{ sub.overall_level || 'Evaluating' }}
                    </span>
                  </td>
                  <td>
                    <span :class="['badge-dot-pill', sub.status === 'sent' ? 'delivered' : 'pending']">
                      <span class="status-dot"></span>
                      {{ sub.status === 'sent' ? 'Delivered' : 'Pending' }}
                    </span>
                  </td>
                  <td class="text-right" @click.stop>
                    <div class="table-action-btns">
                      <button class="table-icon-btn" @click="downloadOne(sub)" title="Download CSV">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                      </button>
                      <button class="table-view-btn" @click="goToSubmission(sub.id)">
                        Review →
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Pagination Controls -->
        <div v-if="filteredSubmissions.length > pageSize" class="pagination-bar">
          <div class="pagination-info">
            Showing {{ paginationStart + 1 }} to {{ Math.min(paginationEnd, filteredSubmissions.length) }} of {{ filteredSubmissions.length }} audits
          </div>

          <div class="pagination-controls">
            <button
              class="page-nav-btn"
              :disabled="currentPage === 1"
              @click="currentPage--"
              type="button"
            >
              Previous
            </button>

            <button
              v-for="page in totalPages"
              :key="page"
              class="page-number-btn"
              :class="{ active: currentPage === page }"
              @click="currentPage = page"
              type="button"
            >
              {{ page }}
            </button>

            <button
              class="page-nav-btn"
              :disabled="currentPage === totalPages"
              @click="currentPage++"
              type="button"
            >
              Next
            </button>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { getSubmissions } from "../api";
import {
  formatDateShort as fmtDate,
  formatDate,
  startOfISTWeek,
  todayISTDateString,
} from "../utils/datetime";
import { downloadSingleSubmission, downloadFilteredSubmissions } from "../utils/csvExport";

const router = useRouter();

// State
const loading = ref(true);
const allSubmissions = ref([]);
const downloading = ref(false);
const linkCopied = ref(false);

// View and filter states
const viewMode = ref("cards"); // 'cards' | 'table'
const isFiltersCollapsed = ref(false);
const searchQuery = ref("");
const selectedSector = ref("");
const dateRangePreset = ref("all");
const dateFrom = ref("");
const dateTo = ref("");
const filterStatusPending = ref(false);
const filterStatusSent = ref(false);
const filterStatusDraft = ref(false);
const selectedMaturityLevels = ref([]);
const filterUrgentOnly = ref(false);
const filterHighScorers = ref(false);
const sortBy = ref("newest");

// Pagination
const currentPage = ref(1);
const pageSize = ref(8);

// KPI Stats
const stats = ref({
  total: 0,
  pending: 0,
  sent: 0,
  avgScore: 0,
  weekNew: 0,
  weekPrev: 0,
  weekSent: 0,
});

// Rich mock submissions dataset matching the reference image format
const MOCK_SUBMISSIONS = [
  {
    id: "sub-goog-01",
    company_name: "Google",
    name: "Alex Vance",
    designation: "Product Designer",
    email: "alex.vance@google.com",
    contact_number: "+1 206 555-0142",
    location: "Seattle, WA, USA",
    sector: "Technology & Software",
    status: "sent",
    overall_avg: "17.4",
    overall_level: "Leading",
    lc_score: "19",
    ro_score: "18",
    we_score: "17",
    be_score: "18",
    tm_score: "16",
    ca_score: "17",
    pc_score: "16",
    sp_score: "18",
    submitted_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "sub-meta-02",
    company_name: "Meta, Facebook",
    name: "Jordan Hayes",
    designation: "UX Designer",
    email: "jhayes@meta.com",
    contact_number: "+1 212 555-0188",
    location: "New York, NY, USA",
    sector: "Technology & Software",
    status: "pending",
    overall_avg: "14.2",
    overall_level: "Maturing",
    lc_score: "15",
    ro_score: "14",
    we_score: "14",
    be_score: "15",
    tm_score: "13",
    ca_score: "14",
    pc_score: "14",
    sp_score: "14",
    submitted_at: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "sub-msft-03",
    company_name: "Microsoft",
    name: "Morgan Chen",
    designation: "Interaction Designer",
    email: "m.chen@microsoft.com",
    contact_number: "+1 425 555-0199",
    location: "Seattle, WA, USA",
    sector: "Technology & Software",
    status: "sent",
    overall_avg: "16.8",
    overall_level: "Leading",
    lc_score: "18",
    ro_score: "17",
    we_score: "16",
    be_score: "17",
    tm_score: "16",
    ca_score: "17",
    pc_score: "17",
    sp_score: "16",
    submitted_at: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "sub-tcs-04",
    company_name: "Tata Consultancy Services",
    name: "Priya Sharma",
    designation: "Head of Talent & Culture",
    email: "priya.sharma@tcs.com",
    contact_number: "+91 80 4123 5678",
    location: "Bengaluru, KA, India",
    sector: "Enterprise Consulting",
    status: "pending",
    overall_avg: "15.1",
    overall_level: "Maturing",
    lc_score: "16",
    ro_score: "15",
    we_score: "15",
    be_score: "14",
    tm_score: "15",
    ca_score: "16",
    pc_score: "15",
    sp_score: "15",
    submitted_at: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "sub-apple-05",
    company_name: "Apple Inc.",
    name: "Marcus Miller",
    designation: "Accessibility Experience Lead",
    email: "mmiller@apple.com",
    contact_number: "+1 408 555-0112",
    location: "Cupertino, CA, USA",
    sector: "Technology & Software",
    status: "sent",
    overall_avg: "18.2",
    overall_level: "Leading",
    lc_score: "19",
    ro_score: "18",
    we_score: "18",
    be_score: "19",
    tm_score: "17",
    ca_score: "18",
    pc_score: "18",
    sp_score: "19",
    submitted_at: new Date(Date.now() - 6 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "sub-jpm-06",
    company_name: "JPMorgan Chase",
    name: "Elena Rostova",
    designation: "VP, Global Inclusion",
    email: "elena.rostova@jpmchase.com",
    contact_number: "+1 212 555-0177",
    location: "New York, NY, USA",
    sector: "Finance & Banking",
    status: "pending",
    overall_avg: "11.6",
    overall_level: "Developing",
    lc_score: "12",
    ro_score: "11",
    we_score: "12",
    be_score: "11",
    tm_score: "10",
    ca_score: "12",
    pc_score: "11",
    sp_score: "13",
    submitted_at: new Date(Date.now() - 8 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "sub-spotify-07",
    company_name: "Spotify",
    name: "Lukas Lindqvist",
    designation: "Diversity & Belonging Specialist",
    email: "lukas.l@spotify.com",
    contact_number: "+46 8 555 019",
    location: "Stockholm, Sweden",
    sector: "Retail & Media",
    status: "sent",
    overall_avg: "16.1",
    overall_level: "Leading",
    lc_score: "17",
    ro_score: "16",
    we_score: "16",
    be_score: "16",
    tm_score: "15",
    ca_score: "17",
    pc_score: "16",
    sp_score: "16",
    submitted_at: new Date(Date.now() - 10 * 24 * 60 * 60 * 1000).toISOString(),
  },
  {
    id: "sub-nov-08",
    company_name: "Novartis Healthcare",
    name: "Claire Dubois",
    designation: "Director of Workplace Wellness",
    email: "c.dubois@novartis.com",
    contact_number: "+41 61 555 010",
    location: "Basel, Switzerland",
    sector: "Healthcare & Pharma",
    status: "sent",
    overall_avg: "13.9",
    overall_level: "Maturing",
    lc_score: "14",
    ro_score: "14",
    we_score: "14",
    be_score: "13",
    tm_score: "14",
    ca_score: "14",
    pc_score: "13",
    sp_score: "15",
    submitted_at: new Date(Date.now() - 12 * 24 * 60 * 60 * 1000).toISOString(),
  },
];

// Submissions counts
const countPending = computed(() => allSubmissions.value.filter(s => s.status === "pending").length);
const countSent = computed(() => allSubmissions.value.filter(s => s.status === "sent").length);
const countDraft = computed(() => allSubmissions.value.filter(s => s.status === "draft" || s.status === "in_progress").length);

const hasActiveFilters = computed(() => {
  return (
    !!searchQuery.value ||
    !!selectedSector.value ||
    filterStatusPending.value ||
    filterStatusSent.value ||
    selectedMaturityLevels.value.length > 0 ||
    filterUrgentOnly.value ||
    filterHighScorers.value ||
    dateRangePreset.value !== "all"
  );
});

const selectedSectorLabel = computed(() => {
  const map = {
    tech: "Technology & Software",
    finance: "Finance & Banking",
    health: "Healthcare & Pharma",
    consulting: "Enterprise Consulting",
    retail: "Retail & Media",
  };
  return map[selectedSector.value] || selectedSector.value;
});

// Filtering and Sorting
const filteredSubmissions = computed(() => {
  let list = [...allSubmissions.value];

  // Text search
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase();
    list = list.filter(
      s =>
        (s.company_name && s.company_name.toLowerCase().includes(q)) ||
        (s.name && s.name.toLowerCase().includes(q)) ||
        (s.email && s.email.toLowerCase().includes(q)) ||
        (s.designation && s.designation.toLowerCase().includes(q)) ||
        (s.location && s.location.toLowerCase().includes(q))
    );
  }

  // Sector filter
  if (selectedSector.value) {
    const map = {
      tech: ["technology", "software", "google", "meta", "microsoft", "apple"],
      finance: ["finance", "banking", "chase", "jpmorgan"],
      health: ["health", "pharma", "wellness", "novartis"],
      consulting: ["consulting", "tcs", "tata", "services"],
      retail: ["retail", "media", "spotify"],
    };
    const keywords = map[selectedSector.value] || [];
    list = list.filter(s => {
      const matchSector = s.sector && keywords.some(k => s.sector.toLowerCase().includes(k));
      const matchName = s.company_name && keywords.some(k => s.company_name.toLowerCase().includes(k));
      return matchSector || matchName;
    });
  }

  // Audit Status
  const activeStatusFilters = [];
  if (filterStatusPending.value) activeStatusFilters.push("pending");
  if (filterStatusSent.value) activeStatusFilters.push("sent");
  if (filterStatusDraft.value) activeStatusFilters.push("draft", "in_progress");

  if (activeStatusFilters.length > 0) {
    list = list.filter(s => activeStatusFilters.includes(s.status));
  }

  // Maturity Level (handles Level 1-4 and labels)
  if (selectedMaturityLevels.value.length > 0) {
    list = list.filter(s => {
      const lvl = String(s.overall_level || "").toLowerCase();
      const avg = parseFloat(s.overall_avg || 0);
      return selectedMaturityLevels.value.some(sel => {
        const lowerSel = sel.toLowerCase();
        if (lowerSel === "leading") return lvl.includes("lead") || lvl.includes("4") || avg >= 16;
        if (lowerSel === "advancing") return lvl.includes("advanc") || lvl.includes("matur") || lvl.includes("3") || (avg >= 12 && avg < 16);
        if (lowerSel === "early") return lvl.includes("early") || lvl.includes("develop") || lvl.includes("2") || (avg >= 8 && avg < 12);
        if (lowerSel === "foundational") return lvl.includes("foundat") || lvl.includes("emerg") || lvl.includes("1") || avg < 8;
        return lvl.includes(lowerSel);
      });
    });
  }

  // Urgent Only
  if (filterUrgentOnly.value) {
    list = list.filter(s => s.status === "pending");
  }

  // High Scorers
  if (filterHighScorers.value) {
    list = list.filter(s => parseFloat(s.overall_avg || 0) >= 15.0);
  }

  // Date Range filter
  if (dateRangePreset.value === "today") {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    list = list.filter(s => new Date(s.submitted_at) >= today);
  } else if (dateRangePreset.value === "week") {
    const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
    list = list.filter(s => new Date(s.submitted_at) >= weekAgo);
  } else if (dateRangePreset.value === "month") {
    const monthAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
    list = list.filter(s => new Date(s.submitted_at) >= monthAgo);
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

  // Sorting
  if (sortBy.value === "newest") {
    list.sort((a, b) => new Date(b.submitted_at || 0) - new Date(a.submitted_at || 0));
  } else if (sortBy.value === "oldest") {
    list.sort((a, b) => new Date(a.submitted_at || 0) - new Date(b.submitted_at || 0));
  } else if (sortBy.value === "score_desc") {
    list.sort((a, b) => parseFloat(b.overall_avg || 0) - parseFloat(a.overall_avg || 0));
  } else if (sortBy.value === "score_asc") {
    list.sort((a, b) => parseFloat(a.overall_avg || 0) - parseFloat(b.overall_avg || 0));
  } else if (sortBy.value === "urgent") {
    list.sort((a, b) => (b.status === "pending" ? 1 : 0) - (a.status === "pending" ? 1 : 0));
  }

  return list;
});

// Pagination computed
const totalPages = computed(() => Math.ceil(filteredSubmissions.value.length / pageSize.value) || 1);
const paginationStart = computed(() => (currentPage.value - 1) * pageSize.value);
const paginationEnd = computed(() => paginationStart.value + pageSize.value);
const paginatedSubmissions = computed(() =>
  filteredSubmissions.value.slice(paginationStart.value, paginationEnd.value)
);

// Helpers
function getInitials(name) {
  if (!name) return "ND";
  const p = name.trim().split(" ");
  if (p.length >= 2) return (p[0][0] + p[1][0]).toUpperCase();
  return name.substring(0, 2).toUpperCase();
}

function getAvatarColor(name) {
  const colors = [
    "#FEE2E2", // soft red
    "#DBEAFE", // soft blue
    "#D1FAE5", // soft green
    "#FEF3C7", // soft amber
    "#EDE9FE", // soft purple
    "#FCE7F3", // soft pink
    "#E0E7FF", // soft indigo
  ];
  if (!name) return colors[0];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

function getLocation(sub) {
  if (!sub) return "—";
  if (sub.state_ut && sub.country) {
    return `${sub.state_ut}, ${sub.country}`;
  }
  return sub.state_ut || sub.country || sub.location || "India";
}

function getSector(sub) {
  if (!sub) return "Enterprise";
  return sub.function || sub.role || sub.sector || sub.designation || "Corporate";
}

function getMaturityBadgeClass(level) {
  if (!level) return "badge-maturing";
  const l = String(level).toLowerCase();
  if (l.includes("4") || l.includes("lead")) return "badge-leading";
  if (l.includes("3") || l.includes("advanc") || l.includes("matur")) return "badge-maturing";
  if (l.includes("2") || l.includes("early") || l.includes("develop")) return "badge-developing";
  return "badge-emerging";
}

function applySearch() {
  currentPage.value = 1;
}

function resetFilters() {
  searchQuery.value = "";
  selectedSector.value = "";
  dateRangePreset.value = "all";
  dateFrom.value = "";
  dateTo.value = "";
  filterStatusPending.value = false;
  filterStatusSent.value = false;
  filterStatusDraft.value = false;
  selectedMaturityLevels.value = [];
  filterUrgentOnly.value = false;
  filterHighScorers.value = false;
  sortBy.value = "newest";
  currentPage.value = 1;
}

function goToSubmission(id) {
  router.push(`/admin/submissions/${id}`);
}

function copyAuditLink() {
  const url = import.meta.env.VITE_APP_URL || "https://NIWI.orchvate.in/";
  navigator.clipboard.writeText(url).then(() => {
    linkCopied.value = true;
    setTimeout(() => {
      linkCopied.value = false;
    }, 2000);
  });
}

function downloadOne(sub) {
  try {
    downloadSingleSubmission(sub);
  } catch (err) {
    console.error("Export error:", err);
  }
}

function downloadReport() {
  downloading.value = true;
  try {
    const list = filteredSubmissions.value.length ? filteredSubmissions.value : allSubmissions.value;
    if (!list.length) return;
    const headers = [
      "ID",
      "Organisation",
      "Recipient Name",
      "Designation",
      "Email",
      "Contact",
      "Submitted At",
      "Overall Score",
      "Maturity Level",
      "Status",
      "Leadership",
      "Recruitment",
      "Workplace",
      "Sensory",
      "Talent",
      "Comms",
      "Products",
      "Suppliers",
    ];
    const rows = list.map(s => [
      s.id,
      s.company_name,
      s.name,
      s.designation,
      s.email,
      s.contact_number,
      s.submitted_at ? formatDate(s.submitted_at) : "",
      s.overall_avg,
      s.overall_level,
      s.status,
      s.lc_score,
      s.ro_score,
      s.we_score,
      s.be_score,
      s.tm_score,
      s.ca_score,
      s.pc_score,
      s.sp_score,
    ]);
    const csv = [headers, ...rows]
      .map(r => r.map(v => `"${String(v ?? "").replace(/"/g, '""')}"`).join(","))
      .join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `NIWI-dashboard-report-${todayISTDateString()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  } finally {
    downloading.value = false;
  }
}

onMounted(async () => {
  try {
    const subs = await getSubmissions();
    allSubmissions.value = subs || [];

    const startOfWeek = startOfISTWeek();
    const startOfLastWeek = new Date(startOfWeek.getTime() - 7 * 24 * 60 * 60 * 1000);

    const subsList = allSubmissions.value;
    const thisWeek = subsList.filter(s => new Date(s.submitted_at) >= startOfWeek);
    const lastWeek = subsList.filter(
      s => new Date(s.submitted_at) >= startOfLastWeek && new Date(s.submitted_at) < startOfWeek
    );

    const avg = subsList.length
      ? (subsList.reduce((a, s) => a + parseFloat(s.overall_avg || 0), 0) / subsList.length).toFixed(1)
      : "0";

    stats.value = {
      total: subsList.length,
      pending: subsList.filter(s => s.status === "pending").length,
      sent: subsList.filter(s => s.status === "sent").length,
      avgScore: avg,
      weekNew: thisWeek.length,
      weekPrev: lastWeek.length,
      weekSent: thisWeek.filter(s => s.status === "sent").length,
    };
  } catch (e) {
    allSubmissions.value = [];
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
/* Skeleton Loading for Progressive Rendering */
.overview-skeleton-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.overview-skeleton-card {
  padding: 20px;
  background: #ffffff;
  border: 1px solid #e2ddd4;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.skeleton-shimmer {
  background: linear-gradient(90deg, #ece9e6 25%, #f7f6f4 50%, #ece9e6 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: 4px;
}
.skeleton-header {
  display: flex;
  justify-content: space-between;
}
.skeleton-badge { width: 90px; height: 20px; border-radius: 12px; }
.skeleton-score { width: 60px; height: 24px; border-radius: 6px; }
.skeleton-title-lg { width: 50%; height: 22px; }
.skeleton-text-sub { width: 30%; height: 14px; }
.skeleton-bars-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-top: 8px;
}
.skeleton-mini-bar { height: 16px; border-radius: 4px; }
@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* Page Root */
.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
  color: var(--primary, #161057);
}

/* ==========================================================================
   HERO / SEARCH BANNER (Neo-Modern style matching Reference Image)
   ========================================================================== */
.hero-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 24px 0 12px;
}

.hero-content {
  max-width: 860px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.hero-title {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 2.5rem;
  font-weight: 800;
  color: var(--primary, #161057);
  letter-spacing: -0.03em;
  margin-bottom: 8px;
  line-height: 1.15;
}

.hero-subtitle {
  font-family: var(--font-body);
  font-size: 0.95rem;
  color: #64748B;
  max-width: 580px;
  margin-bottom: 24px;
  line-height: 1.5;
}

/* Unified Search Banner Card */
.search-banner-card {
  display: flex;
  align-items: center;
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 12px;
  box-shadow: 3px 3px 0px rgba(22, 16, 87, 0.12);
  padding: 6px 8px 6px 16px;
  width: 100%;
  max-width: 820px;
  transition: all 0.2s ease;
}

.search-banner-card:focus-within {
  box-shadow: 4px 4px 0px rgba(22, 16, 87, 0.2);
}

.search-input-group {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1.4;
}

.search-icon {
  color: #64748B;
  flex-shrink: 0;
}

.search-input-group input {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  font-family: var(--font-body);
  font-size: 0.95rem;
  color: var(--primary, #161057);
}

.search-input-group input::placeholder {
  color: #94A3B8;
}

.search-divider {
  width: 1.5px;
  height: 28px;
  background: rgba(22, 16, 87, 0.15);
  margin: 0 12px;
}

.search-sector-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.location-icon {
  color: #64748B;
  flex-shrink: 0;
}

.search-sector-group select {
  width: 100%;
  border: none;
  outline: none;
  background: transparent;
  font-family: var(--font-body);
  font-size: 0.9rem;
  color: var(--primary, #161057);
  cursor: pointer;
  padding: 4px 0;
}

/* Search CTA Button in Warm Coral matching Reference */
.hero-search-btn {
  background: #E05A47;
  color: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 8px;
  padding: 10px 28px;
  font-family: var(--font-body);
  font-size: 0.925rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 2px 2px 0px var(--primary, #161057);
  transition: all 0.15s ease;
  white-space: nowrap;
}

.hero-search-btn:hover {
  background: #D04835;
  transform: translateY(-1px);
  box-shadow: 3px 3px 0px var(--primary, #161057);
}

.hero-search-btn:active {
  transform: translateY(1px);
  box-shadow: 1px 1px 0px var(--primary, #161057);
}

/* ==========================================================================
   RESULTS SUBHEADER & CONTROLS BAR (Matching Reference Image)
   ========================================================================== */
.results-header-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(22, 16, 87, 0.08);
}

.results-header-left {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.results-title {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--primary, #161057);
  margin: 0;
}

.results-count-pill {
  display: inline-flex;
  align-items: center;
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 8px;
  padding: 3px 12px;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--primary, #161057);
  box-shadow: 1.5px 1.5px 0px rgba(22, 16, 87, 0.12);
}

.active-tags-list {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(22, 16, 87, 0.06);
  border: 1px solid rgba(22, 16, 87, 0.15);
  border-radius: 99px;
  padding: 2px 10px;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--primary, #161057);
  cursor: pointer;
  transition: all 0.15s;
}

.filter-tag:hover {
  background: #FEE2E2;
  color: #991B1B;
  border-color: #F87171;
}

.tag-close {
  font-size: 0.7rem;
  font-weight: bold;
}

.btn-clear-all-tags {
  background: transparent;
  border: none;
  color: #64748B;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  text-decoration: underline;
}

.results-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

/* View Switcher */
.view-toggle-group {
  display: flex;
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 1.5px 1.5px 0px rgba(22, 16, 87, 0.12);
}

.view-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  font-size: 0.8rem;
  font-weight: 600;
  color: #64748B;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}

.view-btn.active {
  background: var(--primary, #161057);
  color: #FFFFFF;
}

/* Sort Selector */
.sort-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 8px;
  padding: 5px 10px;
  box-shadow: 1.5px 1.5px 0px rgba(22, 16, 87, 0.12);
}

.sort-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: #64748B;
  text-transform: uppercase;
}

.sort-select {
  border: none;
  outline: none;
  background: transparent;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--primary, #161057);
  cursor: pointer;
}

/* Retro Outline & Primary Action Buttons */
.btn-outline-retro {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #FFFFFF;
  color: var(--primary, #161057);
  border: 1.5px solid var(--primary, #161057);
  border-radius: 8px;
  padding: 7px 14px;
  font-size: 0.825rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.12);
  transition: all 0.15s ease;
}

.btn-outline-retro:hover {
  background: #FAF9F5;
  transform: translateY(-1px);
  box-shadow: 3px 3px 0px rgba(22, 16, 87, 0.2);
}

.btn-primary-retro {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: var(--primary, #161057);
  color: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 8px;
  padding: 7px 16px;
  font-size: 0.825rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.15);
  transition: all 0.15s ease;
}

.btn-primary-retro:hover {
  background: #0F0A42;
  transform: translateY(-1px);
  box-shadow: 3px 3px 0px rgba(22, 16, 87, 0.25);
}

/* ==========================================================================
   TWO-COLUMN MAIN GRID (Filters Left, Content Right)
   ========================================================================== */
.main-dashboard-grid {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: 24px;
  align-items: start;
}

/* ==========================================================================
   LEFT SIDEBAR: FILTERS CARD (Neo-Modern style from Reference Image)
   ========================================================================== */
.filters-sidebar-card {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 12px;
  box-shadow: 3px 3px 0px rgba(22, 16, 87, 0.12);
  padding: 20px;
  position: sticky;
  top: 96px;
  transition: all 0.2s ease;
}

.filters-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  padding-bottom: 12px;
  border-bottom: 1.5px solid rgba(22, 16, 87, 0.12);
}

.filters-title {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--primary, #161057);
}

.filter-toggle-icon {
  background: transparent;
  border: none;
  color: var(--primary, #161057);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease;
}

.rotate-180 {
  transform: rotate(180deg);
}

.filters-body {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 16px;
}

.filter-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-section-title {
  font-size: 0.775rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #64748B;
}

.filter-dropdown {
  width: 100%;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 8px;
  padding: 8px 12px;
  font-family: var(--font-body);
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--primary, #161057);
  background: #FFFFFF;
  outline: none;
  cursor: pointer;
  box-shadow: 1.5px 1.5px 0px rgba(22, 16, 87, 0.08);
}

.custom-date-inputs {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 6px;
}

.date-field {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.date-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748B;
}

.date-picker-input {
  border: 1px solid rgba(22, 16, 87, 0.2);
  border-radius: 6px;
  padding: 4px 8px;
  font-size: 0.8rem;
  outline: none;
  font-family: var(--font-body);
}

/* Custom Styled Checkboxes */
.filter-checkbox-grid {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.custom-checkbox-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--primary, #161057);
  cursor: pointer;
  user-select: none;
  position: relative;
}

.custom-checkbox-row input {
  position: absolute;
  opacity: 0;
  cursor: pointer;
}

.checkmark {
  width: 18px;
  height: 18px;
  background-color: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 4px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  transition: all 0.15s ease;
}

.custom-checkbox-row input:checked ~ .checkmark {
  background-color: var(--primary, #161057);
}

.custom-checkbox-row input:checked ~ .checkmark::after {
  content: "";
  width: 5px;
  height: 9px;
  border: solid #FFFFFF;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
  margin-bottom: 2px;
}

.checkbox-label {
  flex: 1;
}

.count-pill {
  font-size: 0.7rem;
  font-weight: 800;
  padding: 1px 7px;
  border-radius: 99px;
}

.count-pill.red {
  background: #FEE2E2;
  color: #991B1B;
}

.count-pill.green {
  background: #DCFCE7;
  color: #166534;
}

.count-pill.slate {
  background: #F1F5F9;
  color: #475569;
}

.btn-reset-filters {
  background: transparent;
  border: 1px dashed rgba(22, 16, 87, 0.25);
  border-radius: 8px;
  padding: 8px;
  font-family: var(--font-body);
  font-size: 0.8rem;
  font-weight: 700;
  color: #64748B;
  cursor: pointer;
  transition: all 0.15s;
  text-align: center;
  margin-top: 8px;
}

.btn-reset-filters:hover {
  background: #FEE2E2;
  color: #991B1B;
  border-color: #FCA5A5;
}

/* ==========================================================================
   RIGHT COLUMN: MAIN CONTENT (KPI Metrics, Cards List, Table)
   ========================================================================== */
.submissions-main-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Quick KPI Metric Strip */
.kpi-metric-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.kpi-chip {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.1);
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
  transition: transform 0.15s;
}

.kpi-chip:hover {
  transform: translateY(-2px);
}

.kpi-chip.urgent-border {
  border-color: #E05A47;
  background: #FFFBFB;
}

.kpi-icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.kpi-icon-wrap.blue { background: #DBEAFE; color: #1E40AF; }
.kpi-icon-wrap.red { background: #FEE2E2; color: #991B1B; }
.kpi-icon-wrap.green { background: #DCFCE7; color: #166534; }
.kpi-icon-wrap.teal { background: #CCFBF1; color: #0F766E; }

.kpi-text {
  display: flex;
  flex-direction: column;
}

.kpi-label {
  font-size: 0.675rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #64748B;
}

.kpi-value {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--primary, #161057);
  line-height: 1.1;
}

.kpi-scale {
  font-size: 0.75rem;
  font-weight: 500;
  color: #94A3B8;
}

.kpi-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  font-size: 0.65rem;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 99px;
}

.kpi-badge.green { background: #DCFCE7; color: #166534; }
.kpi-badge.red { background: #FEE2E2; color: #991B1B; }

.kpi-subtext {
  position: absolute;
  top: 12px;
  right: 12px;
  font-size: 0.7rem;
  font-weight: 600;
  color: #94A3B8;
}

/* ==========================================================================
   CARDS LIST (Pixel-perfect matching Reference Image)
   ========================================================================== */
.audit-cards-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.audit-card {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 12px;
  box-shadow: 3px 3px 0px rgba(22, 16, 87, 0.12);
  padding: 22px 24px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.audit-card:hover {
  transform: translateY(-2px);
  box-shadow: 4px 4px 0px rgba(22, 16, 87, 0.2);
}

/* Card Header Row */
.card-header-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.card-identity {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

/* Monogram Logo Circle */
.org-avatar-badge {
  width: 44px;
  height: 44px;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-family: var(--font-heading);
  font-size: 1rem;
  font-weight: 800;
  color: var(--primary, #161057);
  flex-shrink: 0;
  box-shadow: 1.5px 1.5px 0px rgba(22, 16, 87, 0.1);
}

.org-title-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.title-and-badges {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.card-org-name {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--primary, #161057);
  letter-spacing: -0.015em;
  margin: 0;
}

/* Card Badges (like Full-time, Mid Level pills in reference) */
.card-badge {
  font-family: var(--font-body);
  font-size: 0.725rem;
  font-weight: 700;
  padding: 2px 9px;
  border-radius: 6px;
  border: 1.2px solid currentColor;
}

.badge-delivered {
  background: #04907C;
  color: #FFFFFF;
  border-color: #037A69;
}

.badge-pending {
  background: #E05A47;
  color: #FFFFFF;
  border-color: #B93826;
}

.badge-leading {
  background: #DCFCE7;
  color: #166534;
  border-color: #86EFAC;
}

.badge-maturing {
  background: #DBEAFE;
  color: #1E40AF;
  border-color: #93C5FD;
}

.badge-developing {
  background: #FEF3C7;
  color: #92400E;
  border-color: #FCD34D;
}

.badge-emerging {
  background: #F1F5F9;
  color: #475569;
  border-color: #CBD5E1;
}

.card-contact-name {
  font-size: 0.85rem;
  font-weight: 600;
  color: #64748B;
  margin: 0;
}

.contact-role {
  color: #475569;
}

/* Location Tag on Top Right */
.card-location {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.825rem;
  font-weight: 600;
  color: #64748B;
  white-space: nowrap;
}

/* Bullet Points (Matching Reference Image) */
.card-bullets-list {
  list-style: none;
  padding-left: 6px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 0;
}

.card-bullets-list li {
  font-size: 0.875rem;
  line-height: 1.45;
  color: #334155;
}

.card-bullets-list strong {
  color: var(--primary, #161057);
}

.bullet-subscores {
  color: #64748B;
  font-size: 0.825rem;
}

.bullet-email {
  color: #475569;
  font-weight: 500;
}

.bullet-phone {
  color: #64748B;
  font-size: 0.825rem;
}

/* Card Action Row (Bottom) */
.card-action-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 4px;
}

.card-footer-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sector-tag {
  background: rgba(22, 16, 87, 0.05);
  border: 1px solid rgba(22, 16, 87, 0.1);
  border-radius: 99px;
  padding: 3px 10px;
  font-size: 0.725rem;
  font-weight: 700;
  color: #64748B;
}

.card-buttons {
  display: flex;
  align-items: center;
  gap: 10px;
}

.card-csv-btn {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 8px;
  width: 38px;
  height: 38px;
  display: grid;
  place-items: center;
  color: var(--primary, #161057);
  cursor: pointer;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.1);
  transition: all 0.15s;
}

.card-csv-btn:hover {
  background: #FAF9F5;
  transform: translateY(-1px);
  box-shadow: 3px 3px 0px rgba(22, 16, 87, 0.18);
}

/* Coral CTA Button ("Apply Now" in reference) */
.card-action-btn {
  background: #E05A47;
  color: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 8px;
  padding: 8px 24px;
  font-family: var(--font-body);
  font-size: 0.875rem;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 2px 2px 0px var(--primary, #161057);
  transition: all 0.15s ease;
}

.card-action-btn:hover {
  background: #D04835;
  transform: translateY(-1px);
  box-shadow: 3px 3px 0px var(--primary, #161057);
}

.card-action-btn:active {
  transform: translateY(1px);
  box-shadow: 1px 1px 0px var(--primary, #161057);
}

/* ==========================================================================
   TABLE VIEW
   ========================================================================== */
.audit-table-card {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 12px;
  box-shadow: 3px 3px 0px rgba(22, 16, 87, 0.12);
  overflow: hidden;
}

.table-responsive {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.875rem;
}

.data-table th {
  background: #FAF9F5;
  color: #64748B;
  font-weight: 700;
  font-size: 0.725rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 14px 16px;
  border-bottom: 1.5px solid rgba(22, 16, 87, 0.12);
}

.data-table td {
  padding: 14px 16px;
  border-bottom: 1px solid rgba(22, 16, 87, 0.06);
  color: var(--primary, #161057);
}

.table-row-clickable {
  cursor: pointer;
  transition: background 0.15s;
}

.table-row-clickable:hover {
  background: #F8FAFC;
}

.table-org-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}

.table-mini-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid var(--primary, #161057);
  display: grid;
  place-items: center;
  font-size: 0.7rem;
  font-weight: 800;
  color: var(--primary, #161057);
  flex-shrink: 0;
}

.score-col strong {
  font-size: 1rem;
}

.table-pill {
  font-size: 0.725rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 6px;
  display: inline-block;
}

.badge-dot-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 99px;
}

.badge-dot-pill.delivered { background: #DCFCE7; color: #166534; }
.badge-dot-pill.pending { background: #FEE2E2; color: #991B1B; }

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}

.table-action-btns {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.table-icon-btn {
  background: transparent;
  border: 1px solid rgba(22, 16, 87, 0.2);
  border-radius: 6px;
  padding: 6px;
  color: var(--primary, #161057);
  cursor: pointer;
  transition: all 0.15s;
}

.table-icon-btn:hover {
  background: #FAF9F5;
  border-color: var(--primary, #161057);
}

.table-view-btn {
  background: var(--primary, #161057);
  color: #FFFFFF;
  border: none;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s;
}

.table-view-btn:hover {
  background: #0F0A42;
}

.text-right { text-align: right; }
.text-muted { color: #64748B; }
.font-bold { font-weight: 700; }

/* ==========================================================================
   PAGINATION
   ========================================================================== */
.pagination-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  padding: 16px 4px;
}

.pagination-info {
  font-size: 0.85rem;
  font-weight: 600;
  color: #64748B;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 6px;
}

.page-nav-btn {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--primary, #161057);
  cursor: pointer;
  box-shadow: 1.5px 1.5px 0px rgba(22, 16, 87, 0.1);
  transition: all 0.15s;
}

.page-nav-btn:hover:not(:disabled) {
  background: #FAF9F5;
  transform: translateY(-1px);
}

.page-nav-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-number-btn {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 6px;
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--primary, #161057);
  cursor: pointer;
  box-shadow: 1.5px 1.5px 0px rgba(22, 16, 87, 0.1);
  transition: all 0.15s;
}

.page-number-btn:hover:not(.active) {
  background: #FAF9F5;
}

.page-number-btn.active {
  background: var(--primary, #161057);
  color: #FFFFFF;
}

/* ==========================================================================
   EMPTY STATE & LOADING
   ========================================================================== */
.empty-results-card {
  background: #FFFFFF;
  border: 1.5px solid var(--primary, #161057);
  border-radius: 12px;
  box-shadow: 3px 3px 0px rgba(22, 16, 87, 0.12);
  padding: 48px 24px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.empty-icon-wrap {
  color: #94A3B8;
  margin-bottom: 4px;
}

.empty-results-card h3 {
  font-family: var(--font-heading);
  font-size: 1.25rem;
  color: var(--primary, #161057);
}

.empty-results-card p {
  color: #64748B;
  font-size: 0.9rem;
  max-width: 440px;
  margin-bottom: 12px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  gap: 16px;
  color: #64748B;
  font-weight: 600;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid rgba(22, 16, 87, 0.15);
  border-top-color: var(--primary, #161057);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ==========================================================================
   RESPONSIVENESS (Desktops, Tablets, Mobile)
   ========================================================================== */
@media (max-width: 1024px) {
  .main-dashboard-grid {
    grid-template-columns: 240px minmax(0, 1fr);
    gap: 16px;
  }
  .kpi-metric-strip {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 860px) {
  .hero-title {
    font-size: clamp(1.5rem, 5vw, 2rem);
  }
  .search-banner-card {
    flex-direction: column;
    align-items: stretch;
    padding: 12px;
    gap: 10px;
  }
  .search-divider {
    display: none;
  }
  .hero-search-btn {
    width: 100%;
    text-align: center;
    min-height: 44px;
  }
  .main-dashboard-grid {
    grid-template-columns: 1fr;
  }
  .filters-sidebar-card {
    position: static;
  }
}

@media (max-width: 600px) {
  .results-header-bar {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  .results-header-right {
    width: 100%;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: flex-start;
  }
  .card-header-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  .card-action-row {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }
  .card-buttons {
    display: flex;
    gap: 8px;
    width: 100%;
  }
  .card-action-btn {
    flex: 1;
    text-align: center;
    min-height: 44px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
  .card-csv-btn {
    width: 44px;
    height: 44px;
    min-width: 44px;
    min-height: 44px;
  }
  .kpi-metric-strip {
    grid-template-columns: 1fr;
  }
  .sort-wrapper {
    width: 100%;
  }
  .sort-select {
    flex: 1;
    min-height: 40px;
  }
}

@media (max-width: 420px) {
  .card-buttons {
    flex-direction: column;
  }
  .card-csv-btn {
    width: 100%;
  }
  .view-toggle-group {
    width: 100%;
  }
  .view-btn {
    flex: 1;
    justify-content: center;
    min-height: 40px;
  }
  .btn-outline-retro, .btn-primary-retro {
    width: 100%;
    justify-content: center;
    min-height: 44px;
  }
}
</style>
