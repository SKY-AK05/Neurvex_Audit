<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1>User Management</h1>
        <p class="subtitle">Manage who has access to the admin portal.</p>
      </div>
    </div>

    <!-- Add User Section -->
    <div class="card add-user-card">
      <h3>Grant Access</h3>
      <div class="add-user-form">
        <div class="form-group">
          <label>Email Address</label>
          <input type="email" v-model="newEmail" placeholder="employee@orchvate.com" />
        </div>
        <div class="form-group">
          <label>Role</label>
          <select v-model="newRole">
            <option value="admin">Standard Admin (View Only)</option>
            <option value="super">Super Admin (Manage Users)</option>
          </select>
        </div>
        <button class="btn btn-primary" @click="addUser" :disabled="loading || !newEmail">
          {{ loading ? 'Adding...' : 'Add User' }}
        </button>
      </div>
      <div v-if="error" class="error-msg">{{ error }}</div>
      <div v-if="success" class="success-msg">{{ success }}</div>
    </div>

    <!-- Users List Section -->
    <div class="card list-card">
      <h3>Authorized Users</h3>
      <div class="table-container">
        <table class="users-table">
          <thead>
            <tr>
              <th>Email</th>
              <th>Role</th>
              <th>Date Added</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loadingList">
              <td colspan="4" class="text-center">Loading users...</td>
            </tr>
            <tr v-else-if="users.length === 0">
              <td colspan="4" class="text-center text-muted">No users found.</td>
            </tr>
            <tr v-for="user in users" :key="user.email" v-else>
              <td class="font-medium">{{ user.email }}</td>
              <td>
                <select 
                  v-if="user.email !== currentUserEmail" 
                  v-model="user.role" 
                  @change="updateRole(user.email, user.role)"
                  :class="['role-badge', 'role-select', user.role]"
                >
                  <option value="admin">Admin</option>
                  <option value="super">Super</option>
                </select>
                <span v-else :class="['role-badge', user.role]">{{ user.role === 'super' ? 'Super' : 'Admin' }}</span>
              </td>
              <td class="text-muted">{{ formatDate(user.created_at) }}</td>
              <td>
                <button 
                  v-if="user.email !== currentUserEmail" 
                  class="btn-icon text-danger" 
                  title="Revoke Access"
                  @click="removeUser(user.email)"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                </button>
                <span v-else class="text-muted text-sm">(You)</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { formatDate } from '../utils/datetime';

const users = ref([]);
const newEmail = ref('');
const newRole = ref('admin');
const loading = ref(false);
const loadingList = ref(false);
const error = ref('');
const success = ref('');

const currentUserEmail = sessionStorage.getItem('nd_user_name') || '';

const API_BASE = import.meta.env.VITE_API_BASE || "/api";

function getAuthHeaders() {
  const token = sessionStorage.getItem("nd_auth_token");
  return token ? { "Authorization": `Bearer ${token}` } : {};
}

async function fetchUsers() {
  loadingList.value = true;
  error.value = '';
  try {
    const res = await fetch(`${API_BASE}/manage/users`, {
      headers: getAuthHeaders(),
    });
    if (!res.ok) throw new Error('Failed to load users');
    users.value = await res.json();
  } catch (err) {
    error.value = err.message;
    console.error(err);
  } finally {
    loadingList.value = false;
  }
}

async function addUser() {
  error.value = '';
  success.value = '';
  loading.value = true;
  
  try {
    const res = await fetch(`${API_BASE}/manage/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({ email: newEmail.value, role: newRole.value })
    });
    
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || data.error || 'Failed to add user');
    }
    
    success.value = `${newEmail.value} has been granted access.`;
    newEmail.value = '';
    newRole.value = 'admin';
    await fetchUsers();
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

async function updateRole(email, role) {
  error.value = '';
  success.value = '';
  try {
    const res = await fetch(`${API_BASE}/manage/users`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
      body: JSON.stringify({ email, role })
    });
    
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || data.error || 'Failed to update role');
    }
    
    success.value = `Updated role for ${email}.`;
    setTimeout(() => { success.value = ''; }, 3000);
  } catch (err) {
    error.value = err.message;
    await fetchUsers();
  }
}

async function removeUser(email) {
  if (!confirm(`Are you sure you want to revoke access for ${email}?`)) return;
  
  try {
    const res = await fetch(`${API_BASE}/manage/users/${encodeURIComponent(email)}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    
    if (!res.ok) throw new Error('Failed to remove user');
    await fetchUsers();
  } catch (err) {
    alert(err.message);
  }
}


onMounted(() => {
  fetchUsers();
});
</script>

<style scoped>
.add-user-card {
  margin-bottom: 2rem;
}

.add-user-form {
  display: flex;
  align-items: flex-end;
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.form-group {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--c-primary-dark);
}

.form-group input, .form-group select {
  padding: 0.75rem 1rem;
  border: 2px solid #E2E8F0;
  border-radius: 8px;
  font-family: inherit;
  font-size: 1rem;
  transition: all 0.2s;
}

.form-group input:focus, .form-group select:focus {
  outline: none;
  border-color: var(--c-primary-dark);
  box-shadow: 4px 4px 0 var(--c-accent);
}

.table-container {
  overflow-x: auto;
  margin-top: 1rem;
}

.users-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}

.users-table th {
  text-align: left;
  padding: 1rem;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748B;
  border-bottom: 2px solid #E2E8F0;
}

.users-table td {
  padding: 1.25rem 1rem;
  border-bottom: 1px solid #E2E8F0;
  vertical-align: middle;
}

.role-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 700;
  text-transform: uppercase;
}

.role-badge.super {
  background: var(--c-retro-lime);
  color: var(--c-primary-dark);
}

.role-badge.admin {
  background: #E2E8F0;
  color: #475569;
}

.role-select {
  border: 1px solid transparent;
  cursor: pointer;
  appearance: none;
  padding-right: 1.5rem;
  background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23000%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.5-12.8z%22%2F%3E%3C%2Fsvg%3E");
  background-repeat: no-repeat;
  background-position: right 0.5rem center;
  background-size: 0.65em auto;
}
.role-select:hover {
  border-color: rgba(0,0,0,0.1);
}
.role-select:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(0,0,0,0.1);
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 8px;
  transition: all 0.2s;
}

.btn-icon:hover {
  background: #FEE2E2;
}

.text-danger { color: #EF4444; }

.error-msg {
  margin-top: 1rem;
  color: #EF4444;
  font-size: 0.9rem;
  font-weight: 600;
}

.success-msg {
  margin-top: 1rem;
  color: #10B981;
  font-size: 0.9rem;
  font-weight: 600;
}
</style>
