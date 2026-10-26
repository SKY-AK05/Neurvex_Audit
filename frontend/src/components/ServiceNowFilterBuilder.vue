<template>
  <div class="sn-filter-wrapper">
    <!-- Top Action Bar -->
    <div class="sn-topbar">
      <div class="sn-topbar-left">
        <button
          type="button"
          class="sn-icon-btn sn-funnel-toggle"
          :class="{ active: isOpen }"
          @click="toggleOpen"
          title="Toggle Filter Builder"
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
          </svg>
          <span class="sn-toggle-label">Filters</span>
        </button>

        <button type="button" class="sn-btn sn-btn-primary" @click="applyFilter" title="Execute query">
          Run
        </button>

        <button type="button" class="sn-btn sn-btn-outline" @click="openSaveModal" title="Save current filter">
          Save Filters
        </button>

        <div class="sn-saved-dropdown-wrap">
          <button type="button" class="sn-btn sn-btn-outline" @click="showSavedDropdown = !showSavedDropdown">
            <span>{{ activeSavedFilterName || 'Presets' }}</span>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"></polyline></svg>
          </button>
          <div v-if="showSavedDropdown" class="sn-dropdown-menu">
            <div class="sn-dropdown-header">Saved &amp; Preset Filters</div>
            <div
              v-for="sf in savedFilters"
              :key="sf.id"
              class="sn-dropdown-item"
              :class="{ selected: sf.name === activeSavedFilterName }"
              @click="loadSavedFilter(sf)"
            >
              <div class="sn-dropdown-item-text">
                <strong>{{ sf.name }}</strong>
                <span v-if="sf.description" class="sn-dropdown-item-desc">{{ sf.description }}</span>
              </div>
              <button
                v-if="sf.created_by !== 'system'"
                type="button"
                class="sn-dropdown-delete-btn"
                @click.stop="removeSavedFilter(sf.id)"
                title="Delete saved filter"
              >
                &times;
              </button>
            </div>
          </div>
        </div>

        <button type="button" class="sn-btn sn-btn-secondary" @click="addTopCondition('AND')">
          AND
        </button>

        <button type="button" class="sn-btn sn-btn-secondary" @click="addTopCondition('OR')">
          OR
        </button>

        <button type="button" class="sn-btn sn-btn-secondary" @click="addSortRule">
          *Add Sort
        </button>

        <button
          type="button"
          class="sn-icon-btn sn-pin-btn"
          :class="{ pinned: isPinned }"
          @click="isPinned = !isPinned"
          title="Pin filter open"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="17" x2="12" y2="22"></line>
            <path d="M5 17h14v-2l-2-3V5a2 2 0 0 0-2-2H9a2 2 0 0 0-2 2v7l-2 3v2z"></path>
          </svg>
        </button>

        <button
          v-if="hasActiveConditions"
          type="button"
          class="sn-btn sn-btn-text"
          @click="clearAllFilters"
          title="Reset to default"
        >
          Clear
        </button>
      </div>
    </div>

    <!-- Collapsible Filter Builder Body -->
    <div v-if="isOpen || isPinned" class="sn-filter-body">
      <div class="sn-condition-section-label">
        All of these conditions must be met
      </div>

      <!-- Condition Groups -->
      <div v-if="!filterGroups.length" class="sn-no-conditions">
        <em>No conditions applied. Showing all records. Click <strong>AND</strong> or <strong>OR</strong> to add filter conditions.</em>
      </div>

      <div
        v-for="(group, gIdx) in filterGroups"
        :key="gIdx"
        class="sn-group-block"
      >
        <div
          v-for="(cond, cIdx) in group.conditions"
          :key="cIdx"
          class="sn-condition-row"
        >
          <!-- Prefix label (empty for first, 'or' for subsequent in OR group) -->
          <div class="sn-cond-prefix">
            <span v-if="cIdx > 0" class="sn-prefix-tag">{{ group.logical_operator.toLowerCase() }}</span>
          </div>

          <!-- Field selector -->
          <select
            v-model="cond.field"
            class="sn-select sn-field-select"
            @change="onFieldChange(cond)"
          >
            <option v-for="(meta, fKey) in fieldsMeta" :key="fKey" :value="fKey">
              {{ meta.label }}
            </option>
          </select>

          <!-- Operator selector -->
          <select
            v-model="cond.operator"
            class="sn-select sn-operator-select"
            @change="onOperatorChange(cond)"
          >
            <option
              v-for="op in getOperatorsForField(cond.field)"
              :key="op.value"
              :value="op.value"
            >
              {{ op.label }}
            </option>
          </select>

          <!-- Value Input (Dynamic based on data type and operator) -->
          <div class="sn-value-input-container">
            <!-- No value needed for is_empty / is_not_empty -->
            <span v-if="cond.operator === 'is_empty' || cond.operator === 'is_not_empty'" class="sn-empty-placeholder">
              (no value required)
            </span>

            <!-- Multiselect listbox for 'is_one_of' and 'is_not_one_of' -->
            <div v-else-if="cond.operator === 'is_one_of' || cond.operator === 'is_not_one_of'" class="sn-multiselect-box">
              <select
                multiple
                v-model="cond.values"
                class="sn-multi-select"
                size="4"
              >
                <option
                  v-for="opt in getEnumOptions(cond.field)"
                  :key="opt"
                  :value="opt"
                >
                  {{ opt }}
                </option>
              </select>
            </div>

            <!-- Between Range for Numeric / Date -->
            <div v-else-if="cond.operator === 'between'" class="sn-between-inputs">
              <template v-if="getFieldType(cond.field) === 'date'">
                <input v-model="cond.value" type="date" class="sn-input sn-date-input" />
                <span class="sn-range-sep">and</span>
                <input v-model="cond.value_to" type="date" class="sn-input sn-date-input" />
              </template>
              <template v-else>
                <input v-model="cond.value" type="number" step="any" placeholder="Min" class="sn-input sn-num-input" />
                <span class="sn-range-sep">and</span>
                <input v-model="cond.value_to" type="number" step="any" placeholder="Max" class="sn-input sn-num-input" />
              </template>
            </div>

            <!-- Single Date input -->
            <input
              v-else-if="getFieldType(cond.field) === 'date'"
              v-model="cond.value"
              type="date"
              class="sn-input sn-date-input"
            />

            <!-- Single Enum dropdown for 'is' / 'is_not' -->
            <select
              v-else-if="getFieldType(cond.field) === 'enum'"
              v-model="cond.value"
              class="sn-select sn-val-select"
            >
              <option value="">-- Select --</option>
              <option
                v-for="opt in getEnumOptions(cond.field)"
                :key="opt"
                :value="opt"
              >
                {{ opt }}
              </option>
            </select>

            <!-- Single Numeric input -->
            <input
              v-else-if="getFieldType(cond.field) === 'numeric'"
              v-model="cond.value"
              type="number"
              step="any"
              placeholder="Score (0-20)"
              class="sn-input sn-num-input"
            />

            <!-- Standard text input with magnifying glass search icon -->
            <div v-else class="sn-text-search-wrap">
              <input
                v-model="cond.value"
                type="text"
                placeholder="Search value..."
                class="sn-input sn-text-input"
                @keyup.enter="applyFilter"
              />
              <span class="sn-search-icon">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#888" stroke-width="2">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
              </span>
            </div>
          </div>

          <!-- Trailing Row Actions (AND, OR, Remove) -->
          <div class="sn-row-actions">
            <button
              type="button"
              class="sn-btn-action sn-btn-and"
              @click="addConditionToGroup(gIdx, 'AND')"
              title="Add condition with AND"
            >
              AND
            </button>
            <button
              type="button"
              class="sn-btn-action sn-btn-or"
              @click="addConditionToGroup(gIdx, 'OR')"
              title="Add condition with OR"
            >
              OR
            </button>
            <button
              type="button"
              class="sn-btn-remove"
              @click="removeCondition(gIdx, cIdx)"
              title="Delete condition"
            >
              &times;
            </button>
          </div>
        </div>
      </div>

      <!-- Sorting Controls Section -->
      <div v-if="sortRules.length" class="sn-sort-section">
        <div class="sn-sort-title">Order by:</div>
        <div v-for="(rule, sIdx) in sortRules" :key="sIdx" class="sn-sort-row">
          <select v-model="rule.field" class="sn-select sn-sort-select">
            <option v-for="(meta, fKey) in fieldsMeta" :key="fKey" :value="fKey">
              {{ meta.label }}
            </option>
          </select>
          <select v-model="rule.direction" class="sn-select sn-sort-dir">
            <option value="desc">Descending (Z-A / High-Low)</option>
            <option value="asc">Ascending (A-Z / Low-High)</option>
          </select>
          <button
            type="button"
            class="sn-btn-remove"
            @click="removeSortRule(sIdx)"
            title="Remove sort rule"
          >
            &times;
          </button>
        </div>
      </div>
    </div>

    <!-- Active Breadcrumb Summary String (ServiceNow-Style) -->
    <div class="sn-breadcrumb-bar">
      <span class="sn-breadcrumb-text">
        <span class="sn-crumb-all">All</span>
        <template v-if="readableSummary && readableSummary !== 'All'">
          <span class="sn-crumb-sep">&gt;</span>
          <span class="sn-crumb-query">{{ readableSummary.replace(/^All\s*>\s*/, '') }}</span>
        </template>
      </span>
      <span v-if="totalCount !== null" class="sn-total-badge">
        {{ totalCount }} {{ totalCount === 1 ? 'record' : 'records' }}
      </span>
    </div>

    <!-- Save Filter Modal -->
    <div v-if="showSaveModal" class="sn-modal-overlay" @click.self="showSaveModal = false">
      <div class="sn-modal-card">
        <h3>Save Current Filter</h3>
        <p class="sn-modal-desc">Save this filter configuration to easily access it later.</p>

        <div class="sn-form-group">
          <label>Filter Name <span class="req">*</span></label>
          <input
            v-model="newFilterName"
            type="text"
            placeholder="e.g. Critical High-Priority Audits"
            class="sn-input"
            autofocus
          />
        </div>

        <div class="sn-form-group">
          <label>Description (Optional)</label>
          <input
            v-model="newFilterDesc"
            type="text"
            placeholder="Brief explanation of this filter"
            class="sn-input"
          />
        </div>

        <div class="sn-modal-actions">
          <button type="button" class="sn-btn sn-btn-outline" @click="showSaveModal = false">
            Cancel
          </button>
          <button
            type="button"
            class="sn-btn sn-btn-primary"
            :disabled="!newFilterName.trim()"
            @click="submitSaveFilter"
          >
            Save Filter
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { getSavedFilters, createSavedFilter, deleteSavedFilter } from "../api";

const props = defineProps({
  totalCount: {
    type: Number,
    default: null,
  },
  readableSummary: {
    type: String,
    default: "All",
  },
});

const emit = defineEmits(["filter-changed", "run-filter"]);

// State
const isOpen = ref(true);
const isPinned = ref(true);
const showSavedDropdown = ref(false);
const showSaveModal = ref(false);
const newFilterName = ref("");
const newFilterDesc = ref("");
const savedFilters = ref([]);
const activeSavedFilterName = ref("");

// Filter Groups: list of { logical_operator: 'AND'|'OR', conditions: [...] }
const filterGroups = ref([
  {
    logical_operator: "AND",
    conditions: [
      { field: "company_name", operator: "contains", value: "", value_to: null, values: [] }
    ]
  }
]);

// Sort rules
const sortRules = ref([
  { field: "submitted_at", direction: "desc" }
]);

// Fields metadata & verified schema definitions
const fieldsMeta = {
  // ── Respondent identity ─────────────────────────────────────────────────
  company_name: {
    label: "Organization Name",
    type: "text",
  },
  name: {
    label: "Respondent Name",
    type: "text",
  },
  email: {
    label: "Recipient Email",
    type: "text",
  },
  designation: {
    label: "Job Role / Designation",
    type: "text",
  },
  // ── Demographics (sourced from answers JSONB, surfaced to top-level) ────
  function: {
    label: "Function / Department",
    type: "enum",
    options: [
      "Administration", "Engineering", "ESG / Sustainability", "Finance",
      "HR / People", "Legal & Compliance", "Manufacturing / Production",
      "Marketing & Communications", "Operations", "Project Management",
      "Quality Assurance / Quality Control", "Research & Development (R&D)",
      "Sales & Business Development", "Supply Chain / Procurement / Logistics",
      "Technology / IT / Product Management", "Other",
    ],
  },
  role: {
    label: "Role Level",
    type: "enum",
    options: [
      "Individual Contributor / Team Member",
      "People Manager/Supervisor",
      "Head of Function/Director",
      "VP / Senior Leader",
      "C-Suite / Executive",
      "Board Member / Trustee",
      "Consultant / Advisor",
      "Other",
    ],
  },
  country: {
    label: "Country",
    type: "text",
  },
  state_ut: {
    label: "State / UT (India)",
    type: "text",
  },
  gender: {
    label: "Gender Identity",
    type: "enum",
    options: [
      "Man", "Woman", "Non-binary / Gender non-conforming",
      "Prefer not to say", "Other gender identity",
    ],
  },
  is_pwd: {
    label: "Person with Disability (PwD)",
    type: "enum",
    options: ["Yes", "No", "Prefer not to say"],
  },
  is_neurodivergent: {
    label: "Neurodivergent",
    type: "enum",
    options: ["Yes", "No", "Prefer not to say"],
  },
  is_marginalized: {
    label: "Underrepresented / Marginalized",
    type: "enum",
    options: ["Yes", "No", "Prefer not to say"],
  },
  // ── Audit outcome ───────────────────────────────────────────────────────
  status: {
    label: "Status",
    type: "enum",
    options: ["pending", "sending", "sent", "failed"],
  },
  overall_level: {
    label: "Maturity Level",
    type: "enum",
    options: ["Level 1 — Foundational", "Level 2 — Early Progress", "Level 3 — Developing"],
  },
  overall_avg: {
    label: "Overall Score",
    type: "numeric",
  },
  submitted_at: {
    label: "Sent Date & Time",
    type: "date",
  },
  id: {
    label: "Submission ID",
    type: "text",
  },
};

const operatorsByType = {
  text: [
    { value: "contains", label: "contains" },
    { value: "does_not_contain", label: "does not contain" },
    { value: "is", label: "is" },
    { value: "is_not", label: "is not" },
    { value: "starts_with", label: "starts with" },
    { value: "ends_with", label: "ends with" },
    { value: "is_empty", label: "is empty" },
    { value: "is_not_empty", label: "is not empty" },
  ],
  enum: [
    { value: "is", label: "is" },
    { value: "is_not", label: "is not" },
    { value: "is_one_of", label: "is one of" },
    { value: "is_not_one_of", label: "is not one of" },
    { value: "is_empty", label: "is empty" },
    { value: "is_not_empty", label: "is not empty" },
  ],
  numeric: [
    { value: "equals", label: "equals" },
    { value: "does_not_equal", label: "does not equal" },
    { value: "greater_than", label: "greater than" },
    { value: "less_than", label: "less than" },
    { value: "greater_than_or_equal", label: "greater than or equal to" },
    { value: "less_than_or_equal", label: "less than or equal to" },
    { value: "between", label: "between" },
    { value: "is_empty", label: "is empty" },
    { value: "is_not_empty", label: "is not empty" },
  ],
  date: [
    { value: "is", label: "is" },
    { value: "is_before", label: "is before" },
    { value: "is_after", label: "is after" },
    { value: "is_on_or_before", label: "is on or before" },
    { value: "is_on_or_after", label: "is on or after" },
    { value: "between", label: "between" },
    { value: "is_empty", label: "is empty" },
    { value: "is_not_empty", label: "is not empty" },
  ],
};

function getFieldType(fieldKey) {
  return fieldsMeta[fieldKey]?.type || "text";
}

function getOperatorsForField(fieldKey) {
  const type = getFieldType(fieldKey);
  return operatorsByType[type] || operatorsByType.text;
}

function getEnumOptions(fieldKey) {
  return fieldsMeta[fieldKey]?.options || [];
}

const hasActiveConditions = computed(() => {
  return filterGroups.value.some(g => g.conditions && g.conditions.length > 0);
});

function toggleOpen() {
  if (isPinned.value) {
    isPinned.value = false;
    isOpen.value = false;
  } else {
    isOpen.value = !isOpen.value;
  }
}

function onFieldChange(cond) {
  const type = getFieldType(cond.field);
  const ops = operatorsByType[type];
  cond.operator = ops[0].value;
  cond.value = "";
  cond.value_to = null;
  cond.values = [];
}

function onOperatorChange(cond) {
  if (cond.operator !== "is_one_of" && cond.operator !== "is_not_one_of") {
    cond.values = [];
  }
}

function addTopCondition(logOp) {
  if (!filterGroups.value.length) {
    filterGroups.value.push({
      logical_operator: logOp,
      conditions: [{ field: "company_name", operator: "contains", value: "", value_to: null, values: [] }],
    });
    return;
  }

  // If adding same logical operator, add to existing group
  const lastGroup = filterGroups.value[filterGroups.value.length - 1];
  if (lastGroup.logical_operator === logOp) {
    lastGroup.conditions.push({ field: "company_name", operator: "contains", value: "", value_to: null, values: [] });
  } else {
    // Start new group
    filterGroups.value.push({
      logical_operator: logOp,
      conditions: [{ field: "company_name", operator: "contains", value: "", value_to: null, values: [] }],
    });
  }
}

function addConditionToGroup(gIdx, logOp) {
  const group = filterGroups.value[gIdx];
  if (group.logical_operator === logOp) {
    group.conditions.push({ field: "company_name", operator: "contains", value: "", value_to: null, values: [] });
  } else {
    // Insert new group
    filterGroups.value.splice(gIdx + 1, 0, {
      logical_operator: logOp,
      conditions: [{ field: "company_name", operator: "contains", value: "", value_to: null, values: [] }],
    });
  }
}

function removeCondition(gIdx, cIdx) {
  filterGroups.value[gIdx].conditions.splice(cIdx, 1);
  if (!filterGroups.value[gIdx].conditions.length) {
    filterGroups.value.splice(gIdx, 1);
  }
}

function addSortRule() {
  sortRules.value.push({ field: "submitted_at", direction: "desc" });
}

function removeSortRule(sIdx) {
  sortRules.value.splice(sIdx, 1);
}

function clearAllFilters() {
  filterGroups.value = [];
  sortRules.value = [{ field: "submitted_at", direction: "desc" }];
  activeSavedFilterName.value = "";
  applyFilter();
}

function getCleanFilterPayload() {
  // Only include valid non-empty conditions
  const cleanGroups = [];
  for (const group of filterGroups.value) {
    const validConds = group.conditions.filter(c => {
      if (c.operator === "is_empty" || c.operator === "is_not_empty") return true;
      if (c.operator === "is_one_of" || c.operator === "is_not_one_of") return c.values && c.values.length > 0;
      if (c.operator === "between") return c.value !== "" && c.value_to !== null && c.value_to !== "";
      return c.value !== undefined && c.value !== null && String(c.value).trim() !== "";
    });

    if (validConds.length > 0) {
      cleanGroups.push({
        logical_operator: group.logical_operator,
        conditions: validConds,
      });
    }
  }

  return {
    filter_groups: cleanGroups,
    sort_by: sortRules.value,
  };
}

function applyFilter() {
  const payload = getCleanFilterPayload();
  emit("run-filter", payload);
}

function openSaveModal() {
  newFilterName.value = activeSavedFilterName.value || "";
  newFilterDesc.value = "";
  showSaveModal.value = true;
}

async function submitSaveFilter() {
  if (!newFilterName.value.trim()) return;
  const payload = getCleanFilterPayload();
  try {
    const saved = await createSavedFilter({
      name: newFilterName.value.trim(),
      description: newFilterDesc.value.trim(),
      filter_config: payload,
    });
    activeSavedFilterName.value = saved.name;
    showSaveModal.value = false;
    await refreshSavedFilters();
  } catch (err) {
    alert("Failed to save filter: " + err.message);
  }
}

async function loadSavedFilter(sf) {
  showSavedDropdown.value = false;
  activeSavedFilterName.value = sf.name;

  const config = sf.filter_config || {};
  filterGroups.value = (config.filter_groups && config.filter_groups.length)
    ? JSON.parse(JSON.stringify(config.filter_groups))
    : [];

  sortRules.value = (config.sort_by && config.sort_by.length)
    ? JSON.parse(JSON.stringify(config.sort_by))
    : [{ field: "submitted_at", direction: "desc" }];

  applyFilter();
}

async function removeSavedFilter(id) {
  if (!confirm("Are you sure you want to delete this saved filter?")) return;
  try {
    await deleteSavedFilter(id);
    if (savedFilters.value.find(s => s.id === id)?.name === activeSavedFilterName.value) {
      activeSavedFilterName.value = "";
    }
    await refreshSavedFilters();
  } catch (err) {
    alert("Could not delete filter: " + err.message);
  }
}

async function refreshSavedFilters() {
  try {
    savedFilters.value = await getSavedFilters();
  } catch (err) {
    console.error("Failed to load saved filters:", err);
  }
}

onMounted(() => {
  refreshSavedFilters();
});

defineExpose({
  getCleanFilterPayload,
  applyFilter,
});
</script>

<style scoped>
.sn-filter-wrapper {
  background: var(--c-white, #FFFFFF);
  border: 1px solid var(--c-border, rgba(22, 16, 87, 0.15));
  border-radius: 8px;
  margin-bottom: 1.25rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: visible;
  font-family: var(--font-body, 'Inter', sans-serif);
}

/* Top Action Bar */
.sn-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.6rem 0.85rem;
  background: #F8F9FA;
  border-bottom: 1px solid var(--c-border, rgba(22, 16, 87, 0.12));
  border-radius: 7px 7px 0 0;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.sn-topbar-left {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.sn-btn {
  padding: 0.38rem 0.75rem;
  font-size: 0.82rem;
  font-weight: 600;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s ease;
  border: 1px solid transparent;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-family: inherit;
}

.sn-btn-primary {
  background: #1B58C9;
  color: #FFFFFF;
  border-color: #174BB0;
}
.sn-btn-primary:hover {
  background: #1444A0;
}

.sn-btn-outline {
  background: #FFFFFF;
  color: #2D3748;
  border-color: #CBD5E0;
}
.sn-btn-outline:hover {
  background: #F1F5F9;
  border-color: #94A3B8;
}

.sn-btn-secondary {
  background: #EDF2F7;
  color: #334155;
  border-color: #CBD5E0;
  font-weight: 700;
  font-size: 0.78rem;
}
.sn-btn-secondary:hover {
  background: #E2E8F0;
}

.sn-btn-text {
  background: transparent;
  color: #64748B;
  border: none;
  font-size: 0.8rem;
  cursor: pointer;
}
.sn-btn-text:hover {
  color: #DC2626;
  text-decoration: underline;
}

.sn-icon-btn {
  padding: 0.38rem 0.5rem;
  background: #FFFFFF;
  border: 1px solid #CBD5E0;
  border-radius: 4px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  color: #475569;
  font-size: 0.8rem;
  font-weight: 600;
}
.sn-icon-btn:hover {
  background: #F1F5F9;
}
.sn-icon-btn.active, .sn-icon-btn.pinned {
  background: #E0E7FF;
  border-color: #818CF8;
  color: #4338CA;
}

/* Saved Filters Dropdown */
.sn-saved-dropdown-wrap {
  position: relative;
}
.sn-dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  margin-top: 4px;
  background: #FFFFFF;
  border: 1px solid #CBD5E0;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  width: 260px;
  z-index: 50;
  padding: 0.4rem 0;
}
.sn-dropdown-header {
  padding: 0.4rem 0.75rem;
  font-size: 0.72rem;
  font-weight: 700;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #F1F5F9;
}
.sn-dropdown-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  font-size: 0.82rem;
  cursor: pointer;
  color: #334155;
  transition: background 0.1s;
}
.sn-dropdown-item:hover {
  background: #F8FAFC;
}
.sn-dropdown-item.selected {
  background: #EEF2FF;
  color: #4338CA;
}
.sn-dropdown-item-text {
  display: flex;
  flex-direction: column;
}
.sn-dropdown-item-desc {
  font-size: 0.72rem;
  color: #94A3B8;
  margin-top: 0.15rem;
}
.sn-dropdown-delete-btn {
  background: transparent;
  border: none;
  font-size: 1.1rem;
  color: #94A3B8;
  cursor: pointer;
  padding: 0 0.3rem;
}
.sn-dropdown-delete-btn:hover {
  color: #EF4444;
}

/* Filter Builder Body */
.sn-filter-body {
  padding: 0.85rem 1rem;
  background: #FAFAFA;
  border-bottom: 1px solid var(--c-border, rgba(22, 16, 87, 0.1));
}

.sn-condition-section-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
  margin-bottom: 0.65rem;
}

.sn-no-conditions {
  color: #94A3B8;
  font-size: 0.82rem;
  padding: 0.5rem 0;
}

/* Condition rows */
.sn-group-block {
  margin-bottom: 0.35rem;
}

.sn-condition-row {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  margin-bottom: 0.4rem;
  flex-wrap: wrap;
}

.sn-cond-prefix {
  width: 32px;
  text-align: right;
}
.sn-prefix-tag {
  font-size: 0.72rem;
  font-weight: 700;
  color: #64748B;
  text-transform: uppercase;
}

.sn-select, .sn-input {
  border: 1px solid #CBD5E0;
  border-radius: 4px;
  padding: 0.36rem 0.6rem;
  font-size: 0.82rem;
  color: #1E293B;
  background: #FFFFFF;
  outline: none;
  font-family: inherit;
  transition: border-color 0.15s;
}
.sn-select:focus, .sn-input:focus {
  border-color: #3B82F6;
  box-shadow: 0 0 0 1px #3B82F6;
}

.sn-field-select {
  width: 210px;
}
.sn-operator-select {
  width: 170px;
}

/* Value Input Container */
.sn-value-input-container {
  min-width: 230px;
  flex: 1;
  max-width: 360px;
}

.sn-empty-placeholder {
  font-size: 0.78rem;
  color: #94A3B8;
  font-style: italic;
  line-height: 28px;
}

.sn-text-search-wrap {
  position: relative;
  width: 100%;
}
.sn-text-input {
  width: 100%;
  padding-right: 1.8rem;
}
.sn-search-icon {
  position: absolute;
  right: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
}

.sn-val-select, .sn-date-input, .sn-num-input {
  width: 100%;
}

.sn-between-inputs {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.sn-range-sep {
  font-size: 0.78rem;
  color: #94A3B8;
}

.sn-multiselect-box {
  width: 100%;
}
.sn-multi-select {
  width: 100%;
  border: 1px solid #CBD5E0;
  border-radius: 4px;
  font-size: 0.8rem;
  padding: 0.25rem 0.4rem;
  background: #FFFFFF;
  outline: none;
}
.sn-multi-select option {
  padding: 0.2rem 0.3rem;
}

/* Row Actions */
.sn-row-actions {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.sn-btn-action {
  padding: 0.28rem 0.5rem;
  font-size: 0.72rem;
  font-weight: 700;
  border: 1px solid #CBD5E0;
  background: #FFFFFF;
  border-radius: 3px;
  cursor: pointer;
  color: #475569;
}
.sn-btn-action:hover {
  background: #F1F5F9;
  border-color: #94A3B8;
}

.sn-btn-remove {
  width: 24px;
  height: 24px;
  border: 1px solid #CBD5E0;
  background: #FFFFFF;
  border-radius: 3px;
  color: #94A3B8;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  line-height: 1;
}
.sn-btn-remove:hover {
  background: #FEE2E2;
  border-color: #F87171;
  color: #DC2626;
}

/* Sorting section */
.sn-sort-section {
  margin-top: 0.85rem;
  padding-top: 0.75rem;
  border-top: 1px dashed #CBD5E0;
}
.sn-sort-title {
  font-size: 0.76rem;
  font-weight: 700;
  color: #64748B;
  text-transform: uppercase;
  margin-bottom: 0.35rem;
}
.sn-sort-row {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  margin-bottom: 0.35rem;
}
.sn-sort-select {
  width: 210px;
}
.sn-sort-dir {
  width: 220px;
}

/* Breadcrumb bar */
.sn-breadcrumb-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.85rem;
  background: #FFFFFF;
  border-radius: 0 0 7px 7px;
  font-size: 0.82rem;
  color: #334155;
}
.sn-breadcrumb-text {
  font-family: inherit;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sn-crumb-all {
  font-weight: 700;
  color: #1E293B;
}
.sn-crumb-sep {
  margin: 0 0.35rem;
  color: #94A3B8;
}
.sn-crumb-query {
  color: #2563EB;
}
.sn-total-badge {
  font-size: 0.78rem;
  font-weight: 700;
  color: #475569;
  background: #F1F5F9;
  padding: 0.2rem 0.55rem;
  border-radius: 12px;
  white-space: nowrap;
}

/* Modal */
.sn-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.sn-modal-card {
  background: #FFFFFF;
  border-radius: 8px;
  width: 90%;
  max-width: 440px;
  padding: 1.5rem;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
}
.sn-modal-card h3 {
  font-size: 1.15rem;
  font-weight: 700;
  color: #1E293B;
  margin-bottom: 0.3rem;
}
.sn-modal-desc {
  font-size: 0.82rem;
  color: #64748B;
  margin-bottom: 1rem;
}
.sn-form-group {
  margin-bottom: 1rem;
}
.sn-form-group label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #334155;
  margin-bottom: 0.35rem;
}
.sn-form-group .req {
  color: #DC2626;
}
.sn-form-group .sn-input {
  width: 100%;
}
.sn-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  margin-top: 1.25rem;
}
</style>
