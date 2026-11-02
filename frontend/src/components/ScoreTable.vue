<template>
  <div class="score-breakdown-wrapper">
    <!-- Optional Respondent Meta Header -->
    <div v-if="data?.name || data?.email || data?.designation" class="respondent-meta-header">
      <div class="rmh-left">
        <div class="rmh-avatar">{{ getInitials(data.name || data.email) }}</div>
        <div>
          <div class="rmh-name-row">
            <span class="rmh-name">{{ data.name || 'Anonymous Respondent' }}</span>
            <span v-if="data.submission_source" class="rmh-method-tag" :class="data.submission_source.toLowerCase()">
              {{ data.submission_source === 'INVITATION' ? '🔗 Invitation Link' : '🌐 Direct Website' }}
            </span>
            <span v-if="data.weight != null" class="rmh-weight-tag">
              Weight: {{ data.weight }}×
            </span>
          </div>
          <div class="rmh-details">
            <span v-if="data.designation" class="rmh-detail-item"><strong>Role:</strong> {{ data.designation }}</span>
            <span v-if="data.function || data.answers?.function" class="rmh-detail-item"><strong>Function:</strong> {{ data.function || data.answers?.function }}</span>
            <span v-if="data.email" class="rmh-detail-item"><strong>Email:</strong> {{ data.email }}</span>
          </div>
        </div>
      </div>
      <div class="rmh-right">
        <div class="rmh-score-box">
          <span class="rmh-score-num">{{ data.overall_avg != null ? data.overall_avg : '—' }}</span>
          <span class="rmh-score-denom">/ 20</span>
        </div>
        <span class="maturity-badge" :class="getMaturityClass(data.overall_avg)">
          {{ data.overall_level || 'Pending' }}
        </span>
      </div>
    </div>

    <!-- Explanatory Header -->
    <div class="scoring-explanation-note">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="16" x2="12" y2="12"></line>
        <line x1="12" y1="8" x2="12.01" y2="8"></line>
      </svg>
      <span>
        <strong>Transparent Score Breakdown:</strong> Each pillar consists of 5 questions.
        Response marks: <strong>Yes = 4 marks</strong>, <strong>Partially = 2 marks</strong>, <strong>No / Not Sure = 0 marks</strong> (max 20 per pillar).
        The overall index is the average across all 8 core pillars.
      </span>
    </div>

    <table class="scores-table">
      <thead>
        <tr>
          <th style="width: 32%">Pillar &amp; Dimension</th>
          <th style="width: 33%">Score &amp; Progress</th>
          <th style="width: 25%">Maturity Level</th>
          <th style="width: 10%; text-align: center">Breakdown</th>
        </tr>
      </thead>
      <template v-for="s in sections" :key="s.key">
        <tbody>
          <tr
            class="section-row"
            :class="{ 'is-expanded': expandedSection === s.key }"
            @click="toggleSection(s.key)"
          >
            <td class="section-name">
              <span class="bullet-dot"></span>
              <div>
                <strong class="sec-title">{{ s.label }}</strong>
                <span class="sec-dim-code">Dimension {{ s.key.toUpperCase() }}</span>
              </div>
            </td>
            <td>
              <div class="score-progress-wrap">
                <span class="score-num">
                  {{ data[`${s.key}_score`] != null ? data[`${s.key}_score`] : 0 }} / 20
                </span>
                <div class="progress-bar-bg">
                  <div
                    class="progress-bar-fill"
                    :style="{ width: `${Math.min(100, ((data[`${s.key}_score`] || 0) / 20) * 100)}%` }"
                  ></div>
                </div>
              </div>
            </td>
            <td>
              <span class="maturity-badge" :class="getMaturityClass(data[`${s.key}_score`])">
                {{ data[`${s.key}_level`] || getCalculatedLevel(data[`${s.key}_score`]) }}
              </span>
            </td>
            <td class="chevron-cell">
              <span class="inspect-text">{{ expandedSection === s.key ? 'Hide ▲' : 'Inspect ▼' }}</span>
            </td>
          </tr>
          
          <!-- Expanded Transparent Q&A Row -->
          <tr v-if="expandedSection === s.key" class="details-row">
            <td colspan="4">
              <div class="qa-details-container">
                <!-- Section Calculation Summary Banner -->
                <div class="section-calc-summary">
                  <span class="scs-title">Calculation for {{ s.label }}:</span>
                  <span class="scs-formula">
                    {{ getSectionCalcFormula(s) }}
                  </span>
                </div>

                <!-- Questions List -->
                <div v-for="(q, qi) in s.questions" :key="q.field" class="qa-item">
                  <div class="qa-top-row">
                    <div class="qa-q-text">
                      <span class="qa-index">{{ q.field.toUpperCase() }}</span>
                      {{ q.text }}
                    </div>
                  </div>

                  <div class="qa-scoring-breakdown">
                    <div class="qa-response-group">
                      <span class="qa-label">Response:</span>
                      <span class="badge" :class="getAnswerBadgeClass(getAnswerValue(q.field))">
                        {{ getAnswerValue(q.field) || 'Not answered' }}
                      </span>
                    </div>

                    <div class="qa-marks-group">
                      <span class="qa-label">Marks Awarded:</span>
                      <span class="marks-pill" :class="getMarksPillClass(getAnswerValue(q.field))">
                        <strong>{{ getMarksAwarded(getAnswerValue(q.field)) }}</strong> / 4 max marks
                      </span>
                      <span class="qa-marks-calc">
                        ({{ getAnswerValue(q.field) || 'None' }} = {{ getMarksAwarded(getAnswerValue(q.field)) }} pts · weight 1.0)
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </td>
          </tr>
        </tbody>
      </template>
      
      <!-- Overall Average Reconciliation Row -->
      <tbody>
        <tr class="overall-row">
          <td>
            <div class="overall-title-wrap">
              <strong>Overall Weighted NIWI Index</strong>
              <span class="overall-subtitle">Reconciled average of 8 pillars</span>
            </div>
          </td>
          <td>
            <div class="score-progress-wrap">
              <span class="score-num">
                <strong>{{ data.overall_avg != null ? data.overall_avg : 0 }}</strong>
                <span class="score-denom"> / 20</span>
                <span class="score-avg">({{ Math.round(((data.overall_avg || 0) / 20) * 100) }}%)</span>
              </span>
              <div class="progress-bar-bg">
                <div
                  class="progress-bar-fill overall-fill"
                  :style="{ width: `${Math.min(100, ((data.overall_avg || 0) / 20) * 100)}%` }"
                ></div>
              </div>
            </div>
          </td>
          <td>
            <span class="maturity-badge overall-badge" :class="getMaturityClass(data.overall_avg)">
              {{ data.overall_level || getCalculatedLevel(data.overall_avg) }}
            </span>
          </td>
          <td></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, computed } from "vue";

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
  dbSections: {
    type: Array,
    default: null,
  },
});

const expandedSection = ref(null);

function toggleSection(key) {
  expandedSection.value = expandedSection.value === key ? null : key;
}

function getInitials(name) {
  if (!name) return 'EMP';
  const clean = name.replace(/[^a-zA-Z0-9\s]/g, '').trim();
  const words = clean.split(/\s+/);
  if (words.length >= 2) {
    return (words[0][0] + words[1][0]).toUpperCase();
  }
  return clean.slice(0, 2).toUpperCase() || 'EMP';
}

function getAnswerBadgeClass(val) {
  if (!val) return 'badge-notsure';
  const v = String(val).toLowerCase().trim();
  if (v === 'yes') return 'badge-yes';
  if (v === 'partially') return 'badge-partially';
  if (v === 'no') return 'badge-no';
  return 'badge-notsure';
}

function getMaturityClass(score) {
  if (score === undefined || score === null || score === 'NA') return 'badge-notsure';
  const s = parseFloat(score);
  if (s <= 6) return 'badge-no';
  if (s <= 14) return 'badge-partially';
  return 'badge-yes';
}

function getCalculatedLevel(score) {
  if (score === undefined || score === null || score === 'NA') return 'Not applicable';
  const s = parseFloat(score);
  if (s <= 6) return 'Level 1 — Foundational';
  if (s <= 14) return 'Level 2 — Early Progress';
  return 'Level 3 — Developing';
}

function getMarksAwarded(val) {
  if (!val) return 0;
  const v = String(val).toLowerCase().trim();
  if (v === 'yes') return 4;
  if (v === 'partially') return 2;
  return 0; // No, Not Sure, NA
}

function getMarksPillClass(val) {
  const marks = getMarksAwarded(val);
  if (marks === 4) return 'marks-full';
  if (marks === 2) return 'marks-partial';
  return 'marks-zero';
}

function getAnswerValue(field) {
  if (!props.data) return null;
  if (props.data[field] != null && props.data[field] !== '') return props.data[field];
  if (props.data.answers && typeof props.data.answers === 'object' && props.data.answers[field] != null) {
    return props.data.answers[field];
  }
  return null;
}

function getSectionCalcFormula(sec) {
  let total = 0;
  const items = sec.questions.map(q => {
    const ans = getAnswerValue(q.field);
    const marks = getMarksAwarded(ans);
    total += marks;
    return `${q.field.toUpperCase()}: ${marks}pts (${ans || 'Unanswered'})`;
  });
  return `${items.join(' + ')} = ${total} / 20 marks earned (${Math.round((total / 20) * 100)}%)`;
}

// ─── Canonical NIWI Standard Sections (Q5–Q44) ─────────
const FALLBACK_SECTIONS = [
  {
    key: "lc",
    label: "Leadership & Culture",
    questions: [
      { field: "q5",  text: "Does your organisation have a clearly defined neurodiversity inclusion strategy with specific, time-bound objectives?" },
      { field: "q6",  text: "Is a senior leader (C-suite or equivalent) explicitly accountable for neurodiversity inclusion?" },
      { field: "q7",  text: "Do senior leaders receive training on neuro-inclusion and actively model inclusive behaviors?" },
      { field: "q8",  text: "Do you have an active neurodiversity-focused employee resource group (ERG) or network that is supported and heard?" },
      { field: "q9",  text: "Does your organisation publicly communicate its commitment to neuro-inclusion through actions and reporting?" }
    ]
  },
  {
    key: "ro",
    label: "Recruitment & Onboarding",
    questions: [
      { field: "q10", text: "Are job descriptions clear, concise, and aligned with the actual role, minimising jargon?" },
      { field: "q11", text: "Is the application process transparent and supportive, with multiple contact options to reduce anxiety?" },
      { field: "q12", text: "Do selection processes include practical or skills-based assessments rather than relying solely on interviews?" },
      { field: "q13", text: "Are interviews flexible and inclusive, with options like sharing questions in advance or alternative formats?" },
      { field: "q14", text: "Are new hires supported before starting with structured communication and early adjustment conversations?" }
    ]
  },
  {
    key: "we",
    label: "Work Environment & Adjustments",
    questions: [
      { field: "q15", text: "Is there a clear, accessible process for employees to request reasonable adjustments without stigma?" },
      { field: "q16", text: "Are flexible working arrangements (hours, locations, patterns) actively available and supported?" },
      { field: "q17", text: "Are managers trained and empowered to understand, implement, and maintain reasonable adjustments?" },
      { field: "q18", text: "Are assistive technologies, ergonomic equipment, and productivity software easily accessible?" },
      { field: "q19", text: "Are adjustment requests handled promptly with periodic reviews to ensure ongoing effectiveness?" }
    ]
  },
  {
    key: "be",
    label: "Built Environment & Sensory",
    questions: [
      { field: "q20", text: "Are quiet, low-stimulation focus areas or decompression spaces accessible to all employees?" },
      { field: "q21", text: "Has the organisation addressed lighting, acoustic control, and sensory triggers across physical workspaces?" },
      { field: "q22", text: "Is clear, consistent signage and intuitive wayfinding implemented throughout physical facilities?" },
      { field: "q23", text: "Are employees allowed to personalise workstation sensory aspects (lighting levels, noise controls, seating)?" },
      { field: "q24", text: "Has a structured sensory or physical accessibility audit been conducted within the past two years?" }
    ]
  },
  {
    key: "tm",
    label: "Talent Management & Development",
    questions: [
      { field: "q25", text: "Are performance management and appraisal criteria designed to reward objective outcomes rather than conformity?" },
      { field: "q26", text: "Do neurodivergent employees have equitable access to learning, skill development, and career advancement?" },
      { field: "q27", text: "Are strengths-based career pathways and coaching models integrated into talent progression?" },
      { field: "q28", text: "Are dedicated mentorship or sponsorship opportunities available for neurodivergent professionals?" },
      { field: "q29", text: "Is employee retention and progression data tracked across diverse demographic groups to identify disparities?" }
    ]
  },
  {
    key: "ca",
    label: "Communication & Accessibility",
    questions: [
      { field: "q30", text: "Are corporate communications written in plain, unambiguous language free from unnecessary jargon?" },
      { field: "q31", text: "Is critical company information and training delivered in multiple accessible formats (written, video, visual)?" },
      { field: "q32", text: "Are meeting agendas, materials, and expectations distributed in advance to enable cognitive preparation?" },
      { field: "q33", text: "Are digital tools, intranet systems, and software platforms audited for digital accessibility standards?" },
      { field: "q34", text: "Can employees easily specify their preferred communication channels and collaborative styles?" }
    ]
  },
  {
    key: "pc",
    label: "Products & Customer Experience",
    questions: [
      { field: "q35", text: "Are client-facing products, digital portals, and services designed with neuro-inclusive user experience in mind?" },
      { field: "q36", text: "Are neurodivergent customers or community advocates included in product feedback, testing, and co-design?" },
      { field: "q37", text: "Are frontline and customer support teams trained to assist neurodivergent clients respectfully and effectively?" },
      { field: "q38", text: "Do digital customer touchpoints comply with international accessibility standards (such as WCAG AA)?" },
      { field: "q39", text: "Is there a transparent, low-friction pathway for customers to request adjustments or alternative communication formats?" }
    ]
  },
  {
    key: "sp",
    label: "Suppliers & Procurement",
    questions: [
      { field: "q40", text: "Does your procurement process incorporate neurodiversity and inclusive employment criteria for vendors?" },
      { field: "q41", text: "Are external contractors and suppliers expected to uphold basic workplace inclusion standards?" },
      { field: "q42", text: "Does your organisation actively identify and partner with neurodiversity-led social enterprises and suppliers?" },
      { field: "q43", text: "Is supplier DEI and inclusion alignment evaluated as part of recurring vendor performance reviews?" },
      { field: "q44", text: "Does your organisation share neuro-inclusive practices and resource toolkits with supply chain partners?" }
    ]
  }
];

const sections = computed(() =>
  props.dbSections && props.dbSections.length > 0 ? props.dbSections : FALLBACK_SECTIONS
);
</script>

<style scoped>
.score-breakdown-wrapper {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* Respondent Meta Header */
.respondent-meta-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #F8FAFC;
  border: 1.5px solid #E2E8F0;
  border-radius: 12px;
  padding: 12px 16px;
  flex-wrap: wrap;
  gap: 12px;
}

.rmh-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rmh-avatar {
  width: 42px;
  height: 42px;
  border-radius: 8px;
  background: var(--primary, #161057);
  color: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.95rem;
  letter-spacing: 0.05em;
  flex-shrink: 0;
}

.rmh-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.rmh-name {
  font-family: var(--font-heading, 'Fraunces', serif);
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--primary, #161057);
}

.rmh-method-tag {
  font-size: 0.72rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 99px;
}
.rmh-method-tag.direct { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
.rmh-method-tag.invitation { background: #fdf4ff; color: #9333ea; border: 1px solid #f0abfc; }

.rmh-weight-tag {
  font-size: 0.72rem;
  font-weight: 600;
  color: #475569;
  background: #E2E8F0;
  padding: 2px 8px;
  border-radius: 99px;
}

.rmh-details {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.8rem;
  color: #64748B;
  margin-top: 3px;
  flex-wrap: wrap;
}

.rmh-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.rmh-score-box {
  display: flex;
  align-items: baseline;
  gap: 2px;
}
.rmh-score-num {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--primary, #161057);
  font-family: var(--font-heading, 'Fraunces', serif);
}
.rmh-score-denom {
  font-size: 0.85rem;
  color: #64748B;
  font-weight: 600;
}

/* Scoring Note */
.scoring-explanation-note {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: #F0FDF4;
  border: 1px solid #BBF7D0;
  border-radius: 8px;
  padding: 10px 14px;
  font-size: 0.82rem;
  color: #166534;
  line-height: 1.45;
}
.scoring-explanation-note svg {
  flex-shrink: 0;
  margin-top: 2px;
  color: #04907C;
}

/* Table */
.scores-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
  background: #FFFFFF;
  border: 1.5px solid rgba(22, 16, 87, 0.12);
  border-radius: 10px;
  overflow: hidden;
}

.scores-table th {
  padding: 10px 14px;
  text-align: left;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--primary, #161057);
  background: #F8FAFC;
  border-bottom: 2px solid var(--primary, #161057);
  letter-spacing: 0.04em;
}

.section-row {
  cursor: pointer;
  border-bottom: 1px solid #E2E8F0;
  transition: background 0.15s ease;
}
.section-row:hover { background: #F8FAFC; }
.section-row.is-expanded { background: #F1F5F9; }

.section-row td {
  padding: 10px 14px;
  vertical-align: middle;
}

.section-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sec-title {
  display: block;
  font-size: 0.88rem;
  color: var(--primary, #161057);
}

.sec-dim-code {
  display: block;
  font-size: 0.7rem;
  color: #64748B;
  text-transform: uppercase;
  font-weight: 600;
}

.bullet-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent, #04907C);
  flex-shrink: 0;
}

/* Progress bar */
.score-progress-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}

.score-num {
  font-family: 'Geist', monospace;
  font-size: 0.85rem;
  font-weight: 700;
  min-width: 65px;
  color: var(--primary, #161057);
}

.progress-bar-bg {
  flex: 1;
  max-width: 120px;
  height: 8px;
  background: #E2E8F0;
  border-radius: 99px;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--accent, #04907C);
  border-radius: 99px;
  transition: width 0.3s ease;
}
.overall-fill {
  background: var(--primary, #161057);
}

/* Inspect button */
.chevron-cell {
  text-align: center;
}
.inspect-text {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--primary, #161057);
  background: #FFFFFF;
  border: 1px solid #CBD5E1;
  padding: 3px 8px;
  border-radius: 6px;
  transition: all 0.15s ease;
}
.section-row:hover .inspect-text {
  background: var(--primary, #161057);
  color: #FFFFFF;
  border-color: var(--primary, #161057);
}

/* Maturity badges */
.maturity-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 9px;
  border-radius: 99px;
  font-size: 0.72rem;
  font-weight: 700;
  border: 1px solid currentColor;
}
.badge-yes {
  background: #D1FAE5;
  color: #065F46;
  border-color: #A7F3D0;
}
.badge-partially {
  background: #FEF3C7;
  color: #92400E;
  border-color: #FDE68A;
}
.badge-no {
  background: #FEE2E2;
  color: #991B1B;
  border-color: #FECACA;
}
.badge-notsure {
  background: #F1F5F9;
  color: #475569;
  border-color: #CBD5E1;
}

/* Details Expansion */
.details-row td {
  padding: 0 !important;
  background: #FAFBFD;
  border-bottom: 2px solid #CBD5E1;
}

.qa-details-container {
  padding: 14px 18px;
  border-left: 4px solid var(--accent, #04907C);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-calc-summary {
  background: #F0FDF4;
  border: 1px solid #BBF7D0;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 0.8rem;
  color: #166534;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.scs-title {
  font-weight: 700;
}
.scs-formula {
  font-family: 'Geist', monospace;
  font-size: 0.75rem;
  color: #047857;
}

.qa-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-bottom: 10px;
  border-bottom: 1px dashed #E2E8F0;
}
.qa-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.qa-q-text {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--primary, #161057);
  line-height: 1.45;
}
.qa-index {
  font-family: 'Geist', monospace;
  font-weight: 800;
  color: #64748B;
  background: #E2E8F0;
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 0.75rem;
  margin-right: 6px;
}

.qa-scoring-breakdown {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  padding-left: 28px;
}

.qa-response-group, .qa-marks-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.qa-label {
  font-size: 0.72rem;
  font-weight: 700;
  color: #64748B;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.marks-pill {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 6px;
  border: 1px solid currentColor;
}
.marks-full {
  background: #ECFDF5;
  color: #047857;
  border-color: #A7F3D0;
}
.marks-partial {
  background: #FFFBEB;
  color: #B45309;
  border-color: #FDE68A;
}
.marks-zero {
  background: #FEE2E2;
  color: #991B1B;
  border-color: #FECACA;
}

.qa-marks-calc {
  font-size: 0.75rem;
  color: #64748B;
  font-family: 'Geist', monospace;
}

/* Overall Row */
.overall-row td {
  background: #F8FAFC;
  padding: 14px;
  border-top: 2px solid var(--primary, #161057);
}

.overall-title-wrap {
  display: flex;
  flex-direction: column;
}
.overall-title-wrap strong {
  font-size: 0.95rem;
  color: var(--primary, #161057);
}
.overall-subtitle {
  font-size: 0.72rem;
  color: #64748B;
}

.overall-badge {
  font-size: 0.75rem;
}
</style>
