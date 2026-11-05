<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Submission History</h1>
        <p>Review, filter, and manage all inclusion audit reports across organizations.</p>
      </div>
    </div>

    <!-- ServiceNow-Style Dynamic Filter Builder Section -->
    <ServiceNowFilterBuilder
      ref="filterBuilderRef"
      :total-count="totalRecords"
      :readable-summary="filterSummary"
      @run-filter="handleRunFilter"
    />

    <div class="card">
      <!-- Quick Action Toolbar -->
      <div class="table-toolbar">
        <div class="toolbar-left">
          <span class="active-summary-label">Showing results for:</span>
          <span class="active-summary-text">{{ filterSummary }}</span>
        </div>
        <div class="toolbar-right">
          <button
            class="btn-download"
            :disabled="!submissions.length"
            @click="downloadCurrentPage"
            title="Download CSV"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            Download CSV <span class="dl-count">({{ totalRecords }})</span>
          </button>
        </div>
      </div>

      <!-- Table Section: Progressive Skeleton Loading -->
      <div v-if="loading" class="submissions-skeleton-container" aria-busy="true">
        <div class="loading-state-banner">
          <div class="spinner"></div>
          <p>Loading submissions...</p>
        </div>
        <div class="table-container desktop-table-view skeleton-table-wrap">
          <table class="sub-table">
            <thead>
              <tr>
                <th>Organization Name</th>
                <th>Role & Function</th>
                <th>Score</th>
                <th>Demographics</th>
                <th>Submitted</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="i in 8" :key="i" class="skeleton-row">
                <td><div class="skeleton-shimmer sk-cell-org"></div></td>
                <td><div class="skeleton-shimmer sk-cell-role"></div></td>
                <td><div class="skeleton-shimmer sk-cell-score"></div></td>
                <td><div class="skeleton-shimmer sk-cell-badge"></div></td>
                <td><div class="skeleton-shimmer sk-cell-date"></div></td>
                <td><div class="skeleton-shimmer sk-cell-btn"></div></td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <p v-else-if="error" class="alert alert-error">{{ error }}</p>
      <template v-else>
        <!-- Desktop / Tablet Table View (769px+) -->
        <div class="table-container desktop-table-view">
          <table class="sub-table">
            <thead>
              <tr>
                <th>Organization Name</th>
                <th>Recipient Email</th>
                <th>Job Role</th>
                <th>Overall Score</th>
                <th>Sent Date &amp; Time</th>
                <th>Status</th>
                <th>Maturity Level</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!submissions.length">
                <td colspan="8" class="empty">
                  No submissions found matching the active filter criteria.
                </td>
              </tr>
              <tr
                v-for="s in submissions"
                :key="s.id"
                @click="$router.push(`/admin/submissions/${s.id}`)"
              >
                <td class="org-name">
                  <div class="org-name-cell">
                    <span>{{ s.company_name }}</span>
                    <span :class="`source-badge source-${(s.submission_source || 'DIRECT').toLowerCase()}`">
                      {{ s.submission_source === 'INVITATION' ? 'Invite' : 'Direct' }}
                    </span>
                  </div>
                </td>
                <td class="email-cell">{{ s.email }}</td>
                <td class="designation-cell">{{ s.designation || '—' }}</td>
                <td class="score-cell">
                  <strong>{{ s.overall_avg !== undefined && s.overall_avg !== null ? s.overall_avg : '—' }}</strong><span class="score-max">/20</span>
                </td>
                <td>{{ fmtDate(s.submitted_at) }}</td>
                <td>
                  <span :class="`badge badge-${s.status === 'sent' ? 'delivered' : 'pending'}`">
                    <span class="badge-dot"></span>
                    {{ s.status === 'sent' ? 'Delivered' : (s.status === 'sending' ? 'Sending' : 'Pending') }}
                  </span>
                </td>
                <td>{{ s.overall_level || '—' }}</td>
                <td @click.stop>
                  <div class="action-group">
                    <button class="action-btn" @click="$router.push(`/admin/submissions/${s.id}`)" title="View Details">
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                    </button>
                    <button class="action-btn dl-btn" @click="downloadOne(s)" title="Download CSV">
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Mobile Adaptive Card View (<= 768px) -->
        <div class="mobile-submissions-feed">
          <div v-if="!submissions.length" class="empty-mobile-card">
            No submissions found matching the active filter criteria.
          </div>
          <div
            v-for="s in submissions"
            :key="'mob-' + s.id"
            class="sub-card-mobile"
            @click="$router.push(`/admin/submissions/${s.id}`)"
          >
            <div class="scm-header">
              <div class="scm-org-group">
                <span class="scm-org">{{ s.company_name }}</span>
                <span :class="`source-badge source-${(s.submission_source || 'DIRECT').toLowerCase()}`">
                  {{ s.submission_source === 'INVITATION' ? 'Invite' : 'Direct' }}
                </span>
              </div>
              <span :class="`badge badge-${s.status === 'sent' ? 'delivered' : 'pending'}`">
                <span class="badge-dot"></span>
                {{ s.status === 'sent' ? 'Delivered' : (s.status === 'sending' ? 'Sending' : 'Pending') }}
              </span>
            </div>
            
            <div class="scm-body">
              <div class="scm-row">
                <span class="scm-label">Recipient:</span>
                <span class="scm-value email">{{ s.email }}</span>
              </div>
              <div class="scm-row" v-if="s.designation">
                <span class="scm-label">Role:</span>
                <span class="scm-value">{{ s.designation }}</span>
              </div>
              <div class="scm-row">
                <span class="scm-label">Score &amp; Level:</span>
                <div class="scm-score-badge">
                  <strong>{{ s.overall_avg != null ? s.overall_avg : '—' }}</strong>/20
                  <span class="scm-level" v-if="s.overall_level">({{ s.overall_level }})</span>
                </div>
              </div>
              <div class="scm-row">
                <span class="scm-label">Date:</span>
                <span class="scm-value">{{ fmtDate(s.submitted_at) }}</span>
              </div>
            </div>

            <div class="scm-footer" @click.stop>
              <button class="scm-btn scm-btn-view" @click="$router.push(`/admin/submissions/${s.id}`)">
                View Full Audit →
              </button>
              <button class="scm-btn-icon" @click="downloadOne(s)" title="Download CSV" aria-label="Download CSV">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Server-Side Pagination -->
        <div class="pagination">
          <span class="page-info">
            Showing {{ pageStart }} to {{ pageEnd }} of {{ totalRecords }} entries
          </span>
          <div class="page-btns">
            <button class="page-btn" :disabled="currentPage <= 1" @click="changePage(currentPage - 1)">‹</button>
            <button
              v-for="p in visiblePages"
              :key="p"
              :class="['page-btn', { active: p === currentPage }]"
              @click="changePage(p)"
            >
              {{ p }}
            </button>
            <button class="page-btn" :disabled="currentPage >= totalPages" @click="changePage(currentPage + 1)">›</button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { filterSubmissions, getSubmission } from "../api";
import { formatDateTime as fmtDate } from "../utils/datetime";
import { downloadSingleSubmission, downloadFilteredSubmissions } from "../utils/csvExport";
import ServiceNowFilterBuilder from "../components/ServiceNowFilterBuilder.vue";

const filterBuilderRef = ref(null);
const submissions    = ref([]);
const totalRecords   = ref(0);
const totalPages     = ref(1);
const currentPage    = ref(1);
const perPage        = ref(10);
const loading        = ref(true);
const error          = ref("");
const filterSummary  = ref("All");

// Stored filter payload for pagination
const currentFilterPayload = ref({
  filter_groups: [],
  sort_by: [{ field: "submitted_at", direction: "desc" }],
});

onMounted(async () => {
  await fetchFilteredSubmissions(1);
});

async function handleRunFilter(payload) {
  currentFilterPayload.value = payload;
  await fetchFilteredSubmissions(1);
}

async function fetchFilteredSubmissions(page = 1) {
  loading.value = true;
  error.value = "";
  try {
    const payload = {
      ...currentFilterPayload.value,
      page: page,
      per_page: perPage.value,
    };
    const response = await filterSubmissions(payload);
    submissions.value = response.items || [];
    totalRecords.value = response.total || 0;
    totalPages.value = response.total_pages || 1;
    currentPage.value = response.page || 1;
    filterSummary.value = response.summary || "All";
  } catch (err) {
    error.value = err.message || "Failed to load submissions";
  } finally {
    loading.value = false;
  }
}

async function changePage(p) {
  if (p < 1 || p > totalPages.value || p === currentPage.value) return;
  await fetchFilteredSubmissions(p);
}

const pageStart = computed(() => {
  if (!totalRecords.value) return 0;
  return (currentPage.value - 1) * perPage.value + 1;
});

const pageEnd = computed(() => {
  return Math.min(currentPage.value * perPage.value, totalRecords.value);
});

const visiblePages = computed(() => {
  const pages = [];
  const maxButtons = 5;
  let start = Math.max(1, currentPage.value - Math.floor(maxButtons / 2));
  let end = Math.min(totalPages.value, start + maxButtons - 1);
  if (end - start + 1 < maxButtons) {
    start = Math.max(1, end - maxButtons + 1);
  }
  for (let i = start; i <= end; i++) {
    pages.push(i);
  }
  return pages;
});

async function downloadOne(s) {
  try {
    const full = await getSubmission(s.id);
    downloadSingleSubmission(full);
  } catch (e) {
    alert("Export failed: " + e.message);
  }
}

async function downloadCurrentPage() {
  if (!submissions.value.length) return;
  loading.value = true;
  try {
    const fullRecords = await Promise.all(
      submissions.value.map(s => getSubmission(s.id))
    );
    downloadFilteredSubmissions(fullRecords);
  } catch (e) {
    alert("Export failed: " + e.message);
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.page-header { margin-bottom: 1.25rem; }
.page-header h1 { font-size: 2rem; font-weight: 800; color: var(--c-primary-dark, #161057); letter-spacing: -0.03em; font-family: 'Fraunces', serif; }
.page-header p  { color: #64748B; font-size: 0.875rem; margin-top: 0.3rem; }

.card {
  background: var(--c-white, #FFFFFF);
  border: 1px solid rgba(22, 16, 87, 0.08);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 2px 12px rgba(22, 16, 87, 0.03);
}

.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(22, 16, 87, 0.06);
  flex-wrap: wrap;
  gap: 0.75rem;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
}

.active-summary-label {
  color: #64748B;
  font-weight: 500;
}

.active-summary-text {
  color: #1E293B;
  font-weight: 600;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-download {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--c-accent, #04907C);
  color: #fff;
  border: none;
  border-radius: 99px;
  padding: 0.55rem 1.2rem;
  font-size: 0.825rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(4, 144, 124, 0.2);
}
.btn-download:hover:not(:disabled) {
  background: #037A69;
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(4, 144, 124, 0.28);
}
.btn-download:disabled {
  opacity: 0.45;
  cursor: not-allowed;
  transform: none;
}
.dl-count { font-weight: 500; opacity: 0.85; }

.table-container { width: 100%; overflow-x: auto; }
.sub-table { width: 100%; border-collapse: collapse; min-width: 950px; }
.sub-table th {
  text-align: left; padding: 0.85rem 1rem;
  font-size: 0.72rem; font-weight: 800; color: #64748B;
  border-bottom: 1.5px solid rgba(22, 16, 87, 0.12);
  text-transform: uppercase; letter-spacing: 0.07em;
}
.sub-table td { padding: 0.95rem 1rem; font-size: 0.875rem; border-bottom: 1px solid #F1F5F9; vertical-align: middle; color: #1E293B; }
.sub-table tbody tr { cursor: pointer; transition: background 0.12s; }
.sub-table tbody tr:hover { background: #F8FAFC; }

.org-name { font-weight: 700; color: var(--c-primary-dark, #161057); }
.email-cell { color: #64748B; }
.designation-cell { color: #475569; font-style: italic; }
.score-cell { font-family: monospace; font-size: 0.95rem; }
.score-max { color: #94A3B8; font-size: 0.78rem; }
.empty { text-align: center; color: #94A3B8; padding: 3rem; font-family: inherit; font-size: 0.92rem; }

.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.65rem;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: capitalize;
}
.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.badge-delivered {
  background: #DCFCE7;
  color: #166534;
}
.badge-delivered .badge-dot {
  background: #16A34A;
}
.badge-pending {
  background: #FEF3C7;
  color: #92400E;
}
.badge-pending .badge-dot {
  background: #D97706;
}

.org-name-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.scm-org-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.source-badge {
  display: inline-block;
  padding: 0.15rem 0.45rem;
  font-size: 0.68rem;
  font-weight: 700;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  line-height: 1.2;
}
.source-direct {
  background: #E0F2FE;
  color: #0369A1;
}
.source-invitation {
  background: #FEF3C7;
  color: #B45309;
}

.action-group { display: flex; gap: 0.4rem; align-items: center; }
.action-btn {
  width: 34px; height: 34px; border-radius: 8px;
  border: 1px solid rgba(22, 16, 87, 0.12); background: #FFFFFF;
  display: grid; place-items: center; cursor: pointer; color: #475569;
  transition: all 0.15s;
}
.action-btn:hover { background: #F8FAFC; color: var(--c-primary-dark, #161057); border-color: rgba(22, 16, 87, 0.24); }
.dl-btn { color: var(--c-accent, #04907C); }
.dl-btn:hover { background: #E6F4F1; border-color: var(--c-accent, #04907C); }

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem 1rem;
  color: #64748B;
  font-size: 0.9rem;
}
.spinner {
  width: 28px;
  height: 28px;
  border: 3px solid #E2E8F0;
  border-top-color: var(--c-accent, #04907C);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-bottom: 0.75rem;
}
@keyframes spin {
  to { transform: rotate(360deg); }
}

.alert-error {
  background: #FEE2E2;
  color: #991B1B;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  margin-bottom: 1rem;
  font-size: 0.85rem;
}

.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 1.25rem;
  margin-top: 0.75rem;
  border-top: 1px solid rgba(22, 16, 87, 0.06);
  flex-wrap: wrap;
  gap: 0.5rem;
}
.page-info { font-size: 0.82rem; color: #64748B; font-weight: 500; }
.page-btns { display: flex; gap: 0.35rem; }
.page-btn {
  min-width: 34px; height: 34px; padding: 0 0.5rem;
  border-radius: 8px;
  border: 1px solid rgba(22, 16, 87, 0.12); background: #FFFFFF;
  font-size: 0.825rem; cursor: pointer; color: #334155; font-weight: 600;
  display: grid; place-items: center; transition: all 0.15s;
  font-family: inherit;
}
.page-btn:hover:not(:disabled) { background: #F8FAFC; border-color: rgba(22, 16, 87, 0.2); }
.page-btn:disabled { opacity: 0.35; cursor: not-allowed; }
.page-btn.active {
  background: var(--c-primary-dark, #161057);
  color: #FFFFFF;
  border-color: var(--c-primary-dark, #161057);
}

/* Mobile Submissions Cards (<= 768px) */
.mobile-submissions-feed {
  display: none;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.sub-card-mobile {
  background: #FFFFFF;
  border: 1.5px solid rgba(22, 16, 87, 0.12);
  border-radius: 12px;
  padding: 14px 16px;
  box-shadow: 2px 2px 0px rgba(22, 16, 87, 0.05);
  display: flex;
  flex-direction: column;
  gap: 10px;
  cursor: pointer;
  transition: transform 0.15s ease, border-color 0.15s ease;
}

.sub-card-mobile:hover {
  border-color: var(--c-primary-dark, #161057);
  transform: translateY(-1px);
}

.scm-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding-bottom: 8px;
  border-bottom: 1px solid #F1F5F9;
}

.scm-org {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--c-primary-dark, #161057);
}

.scm-body {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 0.85rem;
}

.scm-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.scm-label {
  color: #64748B;
  font-weight: 600;
  font-size: 0.78rem;
}

.scm-value {
  color: #1E293B;
  font-weight: 600;
  text-align: right;
  word-break: break-word;
}

.scm-value.email {
  color: #475569;
  font-size: 0.82rem;
}

.scm-score-badge {
  font-family: monospace;
  font-size: 0.95rem;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.scm-score-badge strong {
  color: var(--c-primary-dark, #161057);
  font-size: 1.05rem;
}

.scm-level {
  font-size: 0.75rem;
  color: var(--c-accent, #04907C);
  font-family: var(--font-body, sans-serif);
  font-weight: 700;
}

.scm-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid #F1F5F9;
  margin-top: 2px;
}

.scm-btn-view {
  flex: 1;
  min-height: 44px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: #FAF9F5;
  border: 1.5px solid var(--c-primary-dark, #161057);
  color: var(--c-primary-dark, #161057);
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease;
}

.scm-btn-view:hover {
  background: var(--c-primary-dark, #161057);
  color: #FFFFFF;
}

.scm-btn-icon {
  width: 44px;
  height: 44px;
  min-width: 44px;
  min-height: 44px;
  border-radius: 8px;
  border: 1.5px solid var(--c-accent, #04907C);
  background: #E6F4F1;
  color: var(--c-accent, #04907C);
  display: grid;
  place-items: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.scm-btn-icon:hover {
  background: var(--c-accent, #04907C);
  color: #FFFFFF;
}

.empty-mobile-card {
  text-align: center;
  padding: 32px 16px;
  color: #94A3B8;
  font-size: 0.9rem;
  background: #F8FAFC;
  border: 1px dashed #CBD5E1;
  border-radius: 10px;
}

/* Responsive Breakpoints */
@media (max-width: 768px) {
  .desktop-table-view {
    display: none;
  }
  .mobile-submissions-feed {
    display: flex;
  }
  .table-toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  .toolbar-right {
    width: 100%;
  }
  .btn-download {
    width: 100%;
    justify-content: center;
    min-height: 44px;
  }
  .card {
    padding: clamp(14px, 3vw, 20px);
  }
  .pagination {
    flex-direction: column;
    align-items: center;
    gap: 12px;
  }
  .page-btn {
    min-width: 38px;
    height: 38px;
  }
}

@media (max-width: 480px) {
  .scm-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 6px;
  }
  .scm-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 2px;
  }
  .scm-value {
    text-align: left;
  }
  .page-btns {
    flex-wrap: wrap;
    justify-content: center;
  }
}

/* Skeleton Loading for Submissions Table */
.submissions-skeleton-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.loading-state-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px;
  background: #EEF2FF;
  border: 1px solid #C7D2FE;
  border-radius: 10px;
  color: #4338CA;
  font-weight: 500;
  font-size: 0.9rem;
}
.loading-state-banner p {
  margin: 0;
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
.skeleton-row td {
  padding: 16px 12px;
}
.sk-cell-org { width: 130px; height: 16px; }
.sk-cell-role { width: 160px; height: 14px; }
.sk-cell-score { width: 60px; height: 22px; border-radius: 6px; }
.sk-cell-badge { width: 90px; height: 20px; border-radius: 12px; }
.sk-cell-date { width: 80px; height: 14px; }
.sk-cell-btn { width: 75px; height: 30px; border-radius: 6px; }

</style>
