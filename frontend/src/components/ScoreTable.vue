<template>
  <table class="scores-table">
    <thead>
      <tr>
        <th style="width: 32%">Section</th>
        <th style="width: 35%">Score & Progress</th>
        <th style="width: 28%">Maturity Level</th>
        <th style="width: 5%; text-align: center"></th>
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
            {{ s.label }}
          </td>
          <td>
            <div class="score-progress-wrap">
              <span class="score-num">{{ data[`${s.key}_score`] }}/20</span>
              <div class="progress-bar-bg">
                <div
                  class="progress-bar-fill"
                  :style="{ width: (data[`${s.key}_score`] / 20 * 100) + '%' }"
                ></div>
              </div>
            </div>
          </td>
          <td>
            <span class="maturity-badge" :class="getMaturityClass(data[`${s.key}_score`])">
              {{ data[`${s.key}_level`] }}
            </span>
          </td>
          <td class="chevron-cell">
            <span class="chevron-icon" :class="{ 'rotated': expandedSection === s.key }">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
            </span>
          </td>
        </tr>
        
        <!-- Expanded Q&A Row -->
        <tr v-if="expandedSection === s.key" class="details-row">
          <td colspan="4">
            <div class="qa-details-container">
              <div v-for="(q, qi) in s.questions" :key="q.field" class="qa-item">
                <div class="qa-q-text">
                  <span class="qa-index">Q{{ qi + 1 }}.</span>
                  {{ q.text }}
                </div>
                <div class="qa-answer-row">
                  <span class="qa-label">Response:</span>
                  <span class="badge" :class="getAnswerBadgeClass(data[q.field])">
                    {{ data[q.field] || 'Not answered' }}
                  </span>
                </div>
              </div>
            </div>
          </td>
        </tr>
      </tbody>
    </template>
    
    <!-- Overall Average row -->
    <tbody>
      <tr class="overall-row">
        <td>Overall Average</td>
        <td>
          <div class="score-progress-wrap">
            <span class="score-num">{{ data.overall_avg }}/20</span>
            <div class="progress-bar-bg">
              <div
                class="progress-bar-fill overall-fill"
                :style="{ width: (data.overall_avg / 20 * 100) + '%' }"
              ></div>
            </div>
          </div>
        </td>
        <td>
          <span class="maturity-badge overall-badge" :class="getMaturityClass(Math.round(data.overall_avg))">
            {{ data.overall_level }}
          </span>
        </td>
        <td></td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
import { ref } from "vue";

defineProps({ data: Object });

const expandedSection = ref(null);

function toggleSection(key) {
  expandedSection.value = expandedSection.value === key ? null : key;
}

function getAnswerBadgeClass(val) {
  if (!val) return 'badge-notsure';
  const v = val.toLowerCase();
  if (v === 'yes') return 'badge-yes';
  if (v === 'partially') return 'badge-partially';
  if (v === 'no') return 'badge-no';
  return 'badge-notsure';
}

function getMaturityClass(score) {
  if (score === undefined || score === null) return 'badge-notsure';
  if (score <= 6) return 'badge-no';
  if (score <= 14) return 'badge-partially';
  return 'badge-yes';
}

const sections = [
  {
    key: "lc",
    label: "Leadership & Culture",
    questions: [
      { field: "q5",  text: "Does your organisation have a named senior leader or executive sponsor responsible for neurodiversity inclusion?" },
      { field: "q6",  text: "Is neurodiversity inclusion explicitly referenced in your organisation's values, strategy, or DEI policy?" },
      { field: "q7",  text: "Have senior leaders received education or training on neurodiversity in the past 12 months?" },
      { field: "q8",  text: "Does your organisation publicly communicate its commitment to neurodiversity inclusion?" },
      { field: "q9",  text: "Are neurodivergent employees represented in leadership or decision-making roles?" }
    ]
  },
  {
    key: "ro",
    label: "Recruitment & Onboarding",
    questions: [
      { field: "q10", text: "Are job descriptions reviewed to remove unnecessarily restrictive language or requirements?" },
      { field: "q11", text: "Are alternative interview formats offered to candidates who request them?" },
      { field: "q12", text: "Are reasonable adjustments discussed proactively during the recruitment process?" },
      { field: "q13", text: "Is onboarding structured, clear, and provided in multiple formats?" },
      { field: "q14", text: "Are hiring managers trained to conduct inclusive, bias-aware interviews?" }
    ]
  },
  {
    key: "we",
    label: "Work Environment & Adjustments",
    questions: [
      { field: "q15", text: "Is there a clear, accessible process for employees to request reasonable adjustments?" },
      { field: "q16", text: "Are flexible working arrangements available and actively supported?" },
      { field: "q17", text: "Are managers trained to understand and implement reasonable adjustments?" },
      { field: "q18", text: "Are assistive technologies or tools available to employees who need them?" },
      { field: "q19", text: "Are adjustment requests handled promptly and without stigma?" }
    ]
  },
  {
    key: "be",
    label: "Built Environment & Sensory",
    questions: [
      { field: "q20", text: "Are quiet or low-stimulation spaces available for employees who need them?" },
      { field: "q21", text: "Has your organisation considered lighting, acoustics, and sensory factors in workspace design?" },
      { field: "q22", text: "Is clear, consistent wayfinding and signage in place throughout your premises?" },
      { field: "q23", text: "Are employees able to personalise their workstations to meet sensory needs?" },
      { field: "q24", text: "Has a sensory or environmental audit been conducted in the past two years?" }
    ]
  },
  {
    key: "tm",
    label: "Talent Management & Development",
    questions: [
      { field: "q25", text: "Are performance appraisal processes reviewed to ensure they do not disadvantage neurodivergent employees?" },
      { field: "q26", text: "Do neurodivergent employees have equal access to learning and development opportunities?" },
      { field: "q27", text: "Are strengths-based approaches used in talent management and career development?" },
      { field: "q28", text: "Are mentoring or coaching programmes available and accessible to neurodivergent employees?" },
      { field: "q29", text: "Is retention data monitored to identify whether neurodivergent employees leave at higher rates?" }
    ]
  },
  {
    key: "ca",
    label: "Communication & Accessibility",
    questions: [
      { field: "q30", text: "Are internal communications written in plain, clear language and free from jargon?" },
      { field: "q31", text: "Is information provided in multiple formats where possible?" },
      { field: "q32", text: "Are meeting agendas shared in advance to support employees who benefit from preparation time?" },
      { field: "q33", text: "Are digital tools and platforms used by your organisation tested for accessibility?" },
      { field: "q34", text: "Are employees able to request communication adjustments?" }
    ]
  },
  {
    key: "pc",
    label: "Products & Customer Experience",
    questions: [
      { field: "q35", text: "Are your customer-facing products and services designed with neurodivergent users in mind?" },
      { field: "q36", text: "Are neurodivergent customers or users involved in product testing or feedback processes?" },
      { field: "q37", text: "Are customer service staff trained to support neurodivergent customers effectively?" },
      { field: "q38", text: "Do your digital products meet recognised accessibility standards?" },
      { field: "q39", text: "Is there a clear process for neurodivergent customers to request adjustments or alternative formats?" }
    ]
  },
  {
    key: "sp",
    label: "Suppliers & Procurement",
    questions: [
      { field: "q40", text: "Does your procurement process include questions about suppliers' neurodiversity inclusion practices?" },
      { field: "q41", text: "Are suppliers expected to meet minimum neurodiversity inclusion standards as part of your contracts?" },
      { field: "q42", text: "Do you actively seek to work with neurodiversity-led or neurodiversity-friendly suppliers?" },
      { field: "q43", text: "Is neurodiversity inclusion performance reviewed as part of supplier relationship management?" },
      { field: "q44", text: "Does your organisation share neurodiversity inclusion best practice with its supply chain?" }
    ]
  }
];
</script>

<style scoped>
.scores-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}
.scores-table th {
  padding: 0.8rem 1rem;
  text-align: left;
  font-size: 0.72rem;
  font-weight: 700;
  color: #aaa;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid #E2DDD4;
}

.scores-table tbody {
  border-bottom: 1px solid var(--c-bg);
}

.section-row {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.section-row:hover {
  background: #FAFAF7;
}

.section-row.is-expanded {
  background: #FCFCFA;
}

.section-row td {
  padding: 1rem 1rem;
  color: #333;
}

.section-name {
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.6rem;
}

.bullet-dot {
  width: 6px;
  height: 6px;
  background: var(--c-primary-dark);
  border-radius: 50%;
  display: inline-block;
}

.section-row.is-expanded .bullet-dot {
  background: var(--c-accent);
  box-shadow: 0 0 0 2px rgba(200, 241, 53, 0.4);
}

/* Score and Progress Bar style */
.score-progress-wrap {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.score-num {
  font-family: 'Geist', monospace;
  font-size: 0.85rem;
  font-weight: 700;
  min-width: 42px;
  color: var(--c-primary-dark);
}

.progress-bar-bg {
  flex: 1;
  max-width: 130px;
  height: 10px;
  background: var(--c-bg);
  border: 1.5px solid var(--c-primary-dark);
  border-radius: 99px;
  overflow: hidden;
  position: relative;
}

.progress-bar-fill {
  height: 100%;
  background: var(--c-accent);
  border-radius: 99px;
  transition: width 0.45s cubic-bezier(0.16, 1, 0.3, 1);
}

.overall-fill {
  background: var(--c-primary-dark);
}

/* Maturity badges */
.maturity-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.2rem 0.65rem;
  border-radius: 99px;
  font-size: 0.75rem;
  font-weight: 700;
  border: 1.5px solid currentColor;
  font-family: 'Playfair Display', serif;
}

/* Color mappings for badge */
.badge-yes {
  background: #EDFFD4;
  color: #3A7A00;
  border-color: #3A7A00;
}

.badge-partially {
  background: #FFF8DC;
  color: #8B6914;
  border-color: #8B6914;
}

.badge-no {
  background: #FFF0F0;
  color: #C0392B;
  border-color: #C0392B;
}

.badge-notsure {
  background: var(--c-bg);
  color: #666;
  border-color: #888;
}

/* Chevron */
.chevron-cell {
  text-align: center;
}

.chevron-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  color: #aaa;
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), color 0.15s;
}

.section-row:hover .chevron-icon {
  color: var(--c-primary-dark);
}

.chevron-icon.rotated {
  transform: rotate(180deg);
  color: var(--c-primary-dark);
}

/* Q&A expansion */
.details-row {
  background: #FCFCFA;
}

.details-row td {
  padding: 0 !important;
  border-bottom: 1px solid #E2DDD4;
}

.qa-details-container {
  padding: 1.25rem 1.5rem 1.5rem 2.2rem;
  border-left: 4px solid var(--c-accent);
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  animation: slideDown 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-5px); }
  to { opacity: 1; transform: translateY(0); }
}

.qa-item {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding-bottom: 0.85rem;
  border-bottom: 1px dashed #F2EFE8;
}

.qa-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.qa-q-text {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--c-primary-dark);
  line-height: 1.5;
}

.qa-index {
  font-family: 'Geist', monospace;
  font-weight: 800;
  color: #888;
  margin-right: 0.25rem;
}

.qa-answer-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.qa-label {
  font-size: 0.72rem;
  font-weight: 700;
  color: #aaa;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-family: 'Geist', monospace;
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 0.15rem 0.6rem;
  border-radius: 99px;
  font-size: 0.72rem;
  font-weight: 700;
  border: 1.5px solid currentColor;
  font-family: 'Playfair Display', serif;
}

/* Overall row overrides */
.overall-row td {
  background: var(--c-bg);
  font-weight: 800;
  color: var(--c-primary-dark);
  border-bottom: none;
  padding: 1.2rem 1rem;
}
.overall-row td:first-child {
  border-radius: 10px 0 0 10px;
}
.overall-row td:last-child {
  border-radius: 0 10px 10px 0;
}

.overall-badge {
  font-size: 0.78rem;
  border-width: 2px;
}
</style>
