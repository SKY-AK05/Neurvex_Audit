<template>
  <div>
    <div class="toolbar">
      <h1>Submissions</h1>
      <button class="btn btn-primary" @click="load" :disabled="loading">
        {{ loading ? "Loading…" : "Refresh" }}
      </button>
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
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="s in submissions"
            :key="s.id"
            @click="$router.push(`/admin/submissions/${s.id}`)"
          >
            <td>{{ s.id }}</td>
            <td>{{ s.name }}</td>
            <td>{{ s.company_name }}</td>
            <td>{{ s.email }}</td>
            <td>{{ fmtDate(s.submitted_at) }}</td>
            <td>{{ s.overall_avg }}/20</td>
            <td>{{ s.overall_level }}</td>
            <td><span :class="`badge badge-${s.status}`">{{ cap(s.status) }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { getSubmissions } from "../api";
import { formatDateTime as fmtDate } from "../utils/datetime";

const submissions = ref([]);
const loading     = ref(false);
const error       = ref("");

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
</style>
