<template>
  <div>
    <div class="toolbar">
      <h1>Submissions</h1>
      <button class="btn btn-primary" @click="load" :disabled="loading">
        {{ loading ? "Loading…" : "Refresh" }}
      </button>
    </div>

    <!-- Filters + Download -->
    <div class="card filter-bar">
      <div class="filter-row">
        <div class="search-box">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input v-model="search" type="text" placeholder="Search name, org or email…" />
        </div>
        <div class="date-group">
          <label class="date-label">From</label>
          <input v-model="dateFrom" type="date" class="date-input" />
          <label class="date-label">To</label>
          <input v-model="dateTo" type="date" class="date-input" />
          <button class="btn-clear" @click="dateFrom=''; dateTo=''; search=''" title="Clear filters">✕ Clear</button>
        </div>
        <button
          class="btn-download"
          :disabled="!filtered.length"
          @click="downloadAll"
          title="Download filtered results as CSV"
        >
          ⬇ Download CSV <span class="dl-count">({{ filtered.length }})</span>
        </button>
      </div>
      <p class="filter-hint" v-if="dateFrom || dateTo || search">
        Showing {{ filtered.length }} of {{ submissions.length }} submissions
      </p>
    </div>

    <div class="card">
      <p v-if="loading" class="loading">Loading submissions…</p>
      <p v-else-if="error" class="alert alert-error">{{ error }}</p>
      <p v-else-if="!submissions.length" class="loading">No submissions yet.</p>

      <table v-else class="data-table">
        <thead>
          <tr>
            <th>#</th>
            <th>Name</th>
            <th>Organisation</th>
            <th>Email</th>
            <th>Submitted</th>
            <th>Avg Score</th>
            <th>Maturity</th>
            <th>Status</th>
            <th>Export</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="s in filtered"
            :key="s.id"
            @click="$router.push(`/admin/submissions/${s.id}`)"
          >
            <td class="id-cell">{{ s.id }}</td>
            <td>{{ s.name }}</td>
            <td>{{ s.company_name }}</td>
            <td class="email-cell">{{ s.email }}</td>
            <td>{{ fmtDate(s.submitted_at) }}</td>
            <td><strong>{{ s.overall_avg }}</strong>/20</td>
            <td>{{ s.overall_level }}</td>
            <td><span :class="`badge badge-${s.status}`">{{ cap(s.status) }}</span></td>
            <td @click.stop>
              <button class="row-dl-btn" @click="downloadOne(s)" title="Download this submission">
                ⬇
              </button>
            </td>
          </tr>
          <tr v-if="!filtered.length">
            <td colspan="9" class="empty-row">No submissions match the current filters.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { getSubmissions, getSubmission } from "../api";
import { formatDateTime as fmtDate } from "../utils/datetime";
import { downloadSingleSubmission, downloadFilteredSubmissions } from "../utils/csvExport";

const submissions = ref([]);
const loading     = ref(false);
const error       = ref("");
const search      = ref("");
const dateFrom    = ref("");
const dateTo      = ref("");

async function load() {
  loading.value = true;
  error.value   = "";
  try {
    submissions.value = await getSubmissions();
  } catch (e) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

function cap(s) { return s ? s.charAt(0).toUpperCase() + s.slice(1) : ""; }

function toDateStr(iso) {
  if (!iso) return "";
  return new Date(iso).toISOString().slice(0, 10);
}

const filtered = computed(() => {
  return submissions.value.filter(s => {
    const q = search.value.toLowerCase();
    const matchSearch = !q ||
      s.name?.toLowerCase().includes(q) ||
      s.company_name?.toLowerCase().includes(q) ||
      s.email?.toLowerCase().includes(q);
    const day = toDateStr(s.submitted_at);
    const matchFrom = !dateFrom.value || day >= dateFrom.value;
    const matchTo   = !dateTo.value   || day <= dateTo.value;
    return matchSearch && matchFrom && matchTo;
  });
});

// Download all filtered (summary data only — no per-question answers in list view)
async function downloadAll() {
  // Fetch full detail for each filtered submission
  const ids = filtered.value.map(s => s.id);
  loading.value = true;
  try {
    const full = await Promise.all(ids.map(id => getSubmission(id)));
    downloadFilteredSubmissions(full, dateFrom.value, dateTo.value);
  } catch (e) {
    alert("Export failed: " + e.message);
  } finally {
    loading.value = false;
  }
}

// Download single row — fetch full detail first
async function downloadOne(s) {
  try {
    const full = await getSubmission(s.id);
    downloadSingleSubmission(full);
  } catch (e) {
    alert("Export failed: " + e.message);
  }
}

onMounted(load);
</script>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}
h1 { font-size: 1.3rem; font-weight: 600; }

.filter-bar {
  margin-bottom: 1rem;
  padding: 1rem 1.25rem;
}
.filter-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}
.search-box {
  display: flex; align-items: center; gap: 0.5rem;
  border: 2px solid var(--c-primary-dark); border-radius: 8px;
  padding: 0.5rem 0.85rem; background: #fff; flex: 1; min-width: 200px;
}
.search-box input {
  border: none; outline: none; font-size: 0.875rem; width: 100%;
  background: transparent; color: var(--c-primary-dark);
}
.date-group {
  display: flex; align-items: center; gap: 0.5rem;
}
.date-label {
  font-size: 0.72rem; font-weight: 700; color: #aaa; text-transform: uppercase;
}
.date-input {
  border: 2px solid var(--c-primary-dark); border-radius: 8px;
  padding: 0.5rem 0.75rem; font-size: 0.875rem; color: var(--c-primary-dark);
  background: #fff;
}
.date-input:focus { outline: none; border-color: var(--c-accent); }
.btn-clear {
  border: 2px solid #ccc; border-radius: 8px; padding: 0.5rem 0.75rem;
  font-size: 0.8rem; cursor: pointer; background: #fff; color: #888;
  transition: all 0.15s;
}
.btn-clear:hover { border-color: #ff4444; color: #ff4444; }
.btn-download {
  display: flex; align-items: center; gap: 0.4rem;
  background: var(--c-accent); color: #fff;
  border: 2px solid var(--c-accent); border-radius: 8px;
  padding: 0.55rem 1rem; font-size: 0.875rem; font-weight: 700;
  cursor: pointer; transition: all 0.15s; white-space: nowrap;
  box-shadow: 3px 3px 0 rgba(4,144,124,0.3);
}
.btn-download:hover:not(:disabled) { transform: translate(-2px,-2px); box-shadow: 5px 5px 0 rgba(4,144,124,0.3); }
.btn-download:disabled { opacity: 0.4; cursor: not-allowed; box-shadow: none; }
.dl-count { font-weight: 400; opacity: 0.85; font-size: 0.82rem; }
.filter-hint { font-size: 0.78rem; color: #aaa; margin-top: 0.5rem; }

.data-table { width: 100%; border-collapse: collapse; }
.data-table th {
  text-align: left; padding: 0.75rem 1rem;
  font-size: 0.72rem; font-weight: 800; color: #aaa;
  border-bottom: 2px solid var(--c-primary-dark);
  text-transform: uppercase; letter-spacing: 0.07em;
}
.data-table td {
  padding: 0.85rem 1rem; font-size: 0.875rem;
  border-bottom: 1px solid #f0ede8; vertical-align: middle; color: #333;
}
.data-table tbody tr { cursor: pointer; transition: background 0.1s; }
.data-table tbody tr:hover { background: #FDFAF0; }
.id-cell { color: #bbb; font-size: 0.78rem; }
.email-cell { color: #888; }
.empty-row { text-align: center; color: #ccc; padding: 2.5rem; }

.row-dl-btn {
  width: 30px; height: 30px; border-radius: 50%;
  border: 2px solid var(--c-primary-dark); background: #fff;
  font-size: 0.85rem; cursor: pointer; color: var(--c-primary-dark);
  display: grid; place-items: center; transition: all 0.15s;
}
.row-dl-btn:hover { background: var(--c-accent); color: #fff; border-color: var(--c-accent); }
</style>
