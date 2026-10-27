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

      <!-- Table Section -->
      <div v-if="loading" class="loading-state">
        <div class="spinner"></div>
        <p>Loading submissions...</p>
      </div>
      <p v-else-if="error" class="alert alert-error">{{ error }}</p>
      <template v-else>
        <div class="table-container">
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
                <td class="org-name">{{ s.company_name }}</td>
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
</style>
