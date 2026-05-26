<template>
  <div>
    <div class="page-header">
      <div>
        <h1>Submission History</h1>
        <p>Review and manage all finalized inclusion audit reports sent to organizations.</p>
      </div>
    </div>

    <div class="card">
      <!-- Filters -->
      <div class="filters">
        <div class="search-box">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#999" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input v-model="search" type="text" placeholder="Search organization..." />
        </div>
        <input v-model="dateFrom" type="date" class="date-input" />
        <span class="date-sep">to</span>
        <input v-model="dateTo" type="date" class="date-input" />
        <button class="btn btn-outline">⇅ More Filters</button>
      </div>

      <!-- Table -->
      <p v-if="loading" class="loading">Loading…</p>
      <p v-else-if="error" class="alert alert-error">{{ error }}</p>
      <template v-else>
        <table class="sub-table">
          <thead>
            <tr>
              <th>Organization Name</th>
              <th>Recipient Email</th>
              <th>Job Role</th>
              <th>Sent Date &amp; Time</th>
              <th>Status</th>
              <th>Maturity Level</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!paginated.length">
              <td colspan="7" class="empty">No submissions found.</td>
            </tr>
            <tr v-for="s in paginated" :key="s.id" @click="$router.push(`/admin/submissions/${s.id}`)">
              <td class="org-name">{{ s.company_name }}</td>
              <td class="email-cell">{{ s.email }}</td>
              <td class="designation-cell">{{ s.designation || '—' }}</td>
              <td>{{ fmtDate(s.submitted_at) }}</td>
              <td>
                <span :class="`badge badge-${s.status === 'sent' ? 'delivered' : 'pending'}`">
                  <span class="badge-dot"></span>
                  {{ s.status === 'sent' ? 'Delivered' : 'Pending' }}
                </span>
              </td>
              <td>{{ s.overall_level }}</td>
              <td @click.stop>
                <button class="action-btn" @click="$router.push(`/admin/submissions/${s.id}`)">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Pagination -->
        <div class="pagination">
          <span class="page-info">Showing {{ pageStart }} to {{ pageEnd }} of {{ filtered.length }} entries</span>
          <div class="page-btns">
            <button class="page-btn" :disabled="page === 1" @click="page--">‹</button>
            <button
              v-for="p in totalPages" :key="p"
              :class="['page-btn', { active: p === page }]"
              @click="page = p"
            >{{ p }}</button>
            <button class="page-btn" :disabled="page === totalPages" @click="page++">›</button>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { getSubmissions } from "../api";

const submissions = ref([]);
const loading     = ref(true);
const error       = ref("");
const search      = ref("");
const dateFrom    = ref("");
const dateTo      = ref("");
const page        = ref(1);
const perPage     = 10;

onMounted(async () => {
  try { submissions.value = await getSubmissions(); }
  catch (e) { error.value = e.message; }
  finally { loading.value = false; }
});

const filtered = computed(() => {
  return submissions.value.filter(s => {
    const matchSearch = !search.value ||
      s.company_name?.toLowerCase().includes(search.value.toLowerCase()) ||
      s.email?.toLowerCase().includes(search.value.toLowerCase()) ||
      s.designation?.toLowerCase().includes(search.value.toLowerCase());
    const matchFrom = !dateFrom.value || new Date(s.submitted_at) >= new Date(dateFrom.value);
    const matchTo   = !dateTo.value   || new Date(s.submitted_at) <= new Date(dateTo.value + "T23:59:59");
    return matchSearch && matchFrom && matchTo;
  });
});

const totalPages = computed(() => Math.max(1, Math.ceil(filtered.value.length / perPage)));
const pageStart  = computed(() => filtered.value.length ? (page.value - 1) * perPage + 1 : 0);
const pageEnd    = computed(() => Math.min(page.value * perPage, filtered.value.length));
const paginated  = computed(() => filtered.value.slice((page.value - 1) * perPage, page.value * perPage));

function fmtDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata",
    dateStyle: "medium",
    timeStyle: "short",
  });
}
</script>

<style scoped>
.page-header { margin-bottom: 1.5rem; }
.page-header h1 { font-size: 2rem; font-weight: 800; color: var(--c-primary-dark); letter-spacing: -0.03em; font-family: 'Playfair Display', serif; }
.page-header p  { color: #888; font-size: 0.875rem; margin-top: 0.3rem; }

.filters { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.25rem; flex-wrap: wrap; }
.search-box {
  display: flex; align-items: center; gap: 0.5rem;
  border: 2px solid var(--c-primary-dark); border-radius: 8px;
  padding: 0.6rem 1rem; background: var(--c-white); flex: 1; min-width: 200px;
  box-shadow: 2px 2px 0 rgba(0,0,0,0.1); transition: all 0.15s;
}
.search-box:focus-within { box-shadow: 4px 4px 0 var(--c-accent); transform: translate(-2px, -2px); }
.search-box input { border: none; outline: none; font-size: 0.95rem; width: 100%; background: transparent; color: var(--c-primary-dark); font-family: 'Inter', sans-serif; }
.date-input { border: 2px solid var(--c-primary-dark); border-radius: 8px; padding: 0.6rem 1rem; font-size: 0.95rem; color: var(--c-primary-dark); background: var(--c-white); font-family: 'Inter', sans-serif; box-shadow: 2px 2px 0 rgba(0,0,0,0.1); transition: all 0.15s; }
.date-input:focus { outline: none; box-shadow: 4px 4px 0 var(--c-accent); transform: translate(-2px, -2px); }
.date-sep { color: #bbb; font-size: 0.85rem; font-weight: 600; }

.sub-table { width: 100%; border-collapse: collapse; }
.sub-table th {
  text-align: left; padding: 0.75rem 1rem;
  font-size: 0.72rem; font-weight: 800; color: #aaa;
  border-bottom: 2px solid var(--c-primary-dark); text-transform: uppercase; letter-spacing: 0.07em;
}
.sub-table td { padding: 1rem; font-size: 0.875rem; border-bottom: 1px solid var(--c-bg); vertical-align: middle; color: #333; }
.sub-table tbody tr { cursor: pointer; transition: background 0.1s; }
.sub-table tbody tr:hover { background: #FDFAF0; }
.org-name { font-weight: 700; color: var(--c-primary-dark); }
.email-cell { color: #888; }
.designation-cell { color: #555; font-style: italic; }
.empty { text-align: center; color: #ccc; padding: 3rem; font-family: 'Playfair Display', serif; font-weight: 700; }

.action-btn {
  width: 34px; height: 34px; border-radius: 50%;
  border: 2px solid var(--c-primary-dark); background: var(--c-bg);
  display: grid; place-items: center; cursor: pointer; color: var(--c-primary-dark);
  transition: all 0.15s;
}
.action-btn:hover { background: var(--c-accent); }

.pagination { display: flex; align-items: center; justify-content: space-between; padding-top: 1rem; margin-top: 0.5rem; border-top: 2px solid var(--c-primary-dark); }
.page-info { font-size: 0.82rem; color: #bbb; font-weight: 600; }
.page-btns { display: flex; gap: 0.4rem; }
.page-btn {
  width: 34px; height: 34px; border-radius: 50%;
  border: 2px solid var(--c-primary-dark); background: var(--c-white);
  font-size: 0.85rem; cursor: pointer; color: var(--c-primary-dark); font-weight: 700;
  display: grid; place-items: center; transition: all 0.15s;
  font-family: 'Playfair Display', serif;
}
.page-btn:hover:not(:disabled) { background: var(--c-bg); }
.page-btn:disabled { opacity: 0.3; cursor: not-allowed; }
.page-btn.active { background: var(--c-primary-dark); color: var(--c-accent); }
</style>
