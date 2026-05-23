<template>
  <div class="form-page">

    <!-- Success screen -->
    <div v-if="submitted" class="success-wrap">
      <div class="success-box">
        <div class="success-icon">✓</div>
        <h2>Audit Submitted</h2>
        <p>Thank you for completing the Neurvex Audit for <strong>{{ form.company_name }}</strong>.<br/>You will receive your results by email shortly.</p>
        <router-link to="/admin" class="admin-link-small">Admin →</router-link>
      </div>
    </div>

    <div v-else class="form-inner">
      <!-- Header -->
      <header class="form-header">
        <div class="form-logo">
          <span class="form-logo-mark">✦</span>
          <span>Neurvex Audit</span>
        </div>
        <button class="fill-btn" @click="fillTestData" type="button">⚡ Fill Test Data</button>
      </header>

      <!-- Step content -->
      <div class="step-wrap">
        <div class="step-layout">

        <!-- Progress — left sidebar -->
        <aside class="progress-sidebar">
          <div class="progress-wrap">
            <div class="progress-header">
              <span class="progress-phase">{{ progressPhase }}</span>
              <span class="progress-pct">{{ Math.round(progressPct) }}%</span>
              <span class="progress-count">{{ currentStep + 1 }} / {{ totalSteps }}</span>
            </div>
            <div class="progress-track progress-track--vertical">
              <div class="progress-rail">
                <div class="progress-fill" :style="{ height: progressPct + '%' }"></div>
              </div>
              <div class="progress-steps">
                <button
                  v-for="(step, i) in progressSteps"
                  :key="step.id"
                  type="button"
                  :class="['progress-step', i === currentStep ? 'active' : '', i < currentStep ? 'done' : '']"
                  :title="step.label"
                  :disabled="i > currentStep"
                  @click="goToStep(i)"
                >
                  <span class="progress-step-dot">
                    <span v-if="i < currentStep" class="step-check">✓</span>
                    <span v-else>{{ i + 1 }}</span>
                  </span>
                  <span class="progress-step-label">{{ step.short }}</span>
                </button>
              </div>
            </div>
          </div>
        </aside>

        <div class="step-center">
        <div class="step-main">
        <div class="step-card" :key="currentStep">
          <div class="step-card-head">
            <div v-if="currentStep === 0" class="step-tag">Getting Started</div>
            <div v-else class="step-tag">Section {{ currentStep }} of 8</div>
            <h1>{{ currentStep === 0 ? 'Tell us about you' : currentSection.title }}</h1>
            <p class="step-sub">
              {{ currentStep === 0
                ? "We'll use this to personalise your audit report."
                : "Select the answer that best reflects your organisation's current position." }}
            </p>
          </div>

          <div ref="questionsScroll" class="questions-scroll">
            <div v-if="currentStep === 0" class="fields-grid">
              <div class="field">
                <label>Full Name *</label>
                <input v-model="form.name" type="text" placeholder="Jane Smith" :class="{ error: errors.name }" />
                <span v-if="errors.name" class="field-err">Required</span>
              </div>
              <div class="field">
                <label>Designation / Job Role *</label>
                <input v-model="form.designation" type="text" placeholder="e.g. HR Manager" :class="{ error: errors.designation }" />
                <span v-if="errors.designation" class="field-err">Required</span>
              </div>
              <div class="field">
                <label>Organisation Name *</label>
                <input v-model="form.company_name" type="text" placeholder="Acme Ltd" :class="{ error: errors.company_name }" />
                <span v-if="errors.company_name" class="field-err">Required</span>
              </div>
              <div class="field">
                <label>Work Email Address *</label>
                <input v-model="form.email" type="email" placeholder="jane@acme.com" :class="{ error: errors.email }" />
                <span v-if="errors.email" class="field-err">{{ errors.emailMsg || 'Required' }}</span>
              </div>
              <div class="field">
                <label>Contact Number (Optional)</label>
                <input v-model="form.contact_number" type="tel" placeholder="+44 7700 000000" />
              </div>
            </div>

            <div v-else class="questions-list">
              <div v-for="(q, qi) in currentSection.questions" :key="q.field" class="q-block">
                <div class="q-number">Q{{ (currentStep - 1) * 5 + qi + 1 }}</div>
                <p class="q-text">{{ q.text }}</p>
                <div class="options">
                  <button
                    v-for="opt in options" :key="opt"
                    type="button"
                    :class="['opt-btn', form[q.field] === opt ? 'selected' : '']"
                    @click="form[q.field] = opt"
                  >{{ opt }}</button>
                </div>
                <span v-if="errors[q.field]" class="field-err">Please select an answer</span>
              </div>
            </div>
          </div>
          
          <div class="step-actions">
            <div class="step-nav">
              <button v-if="currentStep > 0" class="btn-back" @click="currentStep--" type="button">← Back</button>
              <div v-else></div>

              <button
                v-if="currentStep < totalSteps - 1"
                class="btn-next"
                @click="nextStep"
                type="button"
              >
                {{ currentStep === 0 ? 'Start Audit →' : 'Next →' }}
              </button>
              <button
                v-else
                class="btn-submit"
                @click="submit"
                :disabled="submitting"
                type="button"
              >
                {{ submitting ? 'Submitting…' : 'Submit Audit ✓' }}
              </button>
            </div>
            <div v-if="submitError" class="alert alert-error">{{ submitError }}</div>
          </div>
        </div>

        </div>

        <!-- Section context panel (right) -->
        <aside class="step-aside" :key="currentStep">
          <div class="aside-card">
            <div class="aside-icon">{{ currentPanel.icon }}</div>
            <div class="aside-tag">{{ currentPanel.tag }}</div>
            <h2 class="aside-title">{{ currentPanel.title }}</h2>
            <p class="aside-summary">{{ currentPanel.summary }}</p>

            <div class="aside-block">
              <h3>Why this matters</h3>
              <p>{{ currentPanel.why }}</p>
            </div>

            <ul v-if="currentPanel.points?.length" class="aside-points">
              <li v-for="(point, i) in currentPanel.points" :key="i">{{ point }}</li>
            </ul>

            <div v-if="currentPanel.tip" class="aside-tip">
              <span class="tip-label">Tip</span>
              <p>{{ currentPanel.tip }}</p>
            </div>

            <div v-if="currentStep > 0" class="aside-progress-mini">
              <span>{{ sectionAnsweredCount }} of {{ currentSection.questions.length }} answered</span>
              <div class="mini-bar">
                <div class="mini-fill" :style="{ width: sectionProgressPct + '%' }"></div>
              </div>
            </div>
          </div>
        </aside>
        </div>
        </div>
      </div>

      <div class="form-footer">
        <router-link to="/admin" class="admin-link-small">Admin →</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick } from "vue";
import { submitAudit } from "../api";

const submitted       = ref(false);
const submitting      = ref(false);
const submitError     = ref("");
const currentStep     = ref(0);
const questionsScroll = ref(null);
const errors      = reactive({});
const options     = ["Yes", "Partially", "No", "Not Sure"];

const step0Panel = {
  icon: "✦",
  tag: "Welcome",
  title: "Your ND Inclusion journey",
  summary: "This audit maps how neuroinclusive your organisation is across eight dimensions — from leadership to your supply chain.",
  why: "Honest answers help us benchmark your maturity and deliver a tailored report with clear, actionable recommendations.",
  points: [
    "Takes about 15–20 minutes to complete",
    "40 questions across 8 themed sections",
    "No wrong answers — reflect where you are today",
  ],
  tip: "Gather input from HR, facilities, or employee networks if you can — a broader perspective gives a truer picture.",
};

const sections = [
  {
    title: "Leadership & Culture",
    icon: "◆",
    summary: "Inclusion starts at the top. Leadership sets the tone, allocates resources, and signals what the organisation truly values.",
    why: "Without visible executive commitment, neurodiversity initiatives often stall — employees notice when inclusion is only on paper.",
    points: ["Executive sponsorship", "Policy & strategy alignment", "Visible role models"],
    tip: "Look beyond policy documents — consider what leaders actually say and do in meetings and communications.",
    questions: [
      { field: "q5",  text: "Does your organisation have a named senior leader or executive sponsor responsible for neurodiversity inclusion?" },
      { field: "q6",  text: "Is neurodiversity inclusion explicitly referenced in your organisation's values, strategy, or DEI policy?" },
      { field: "q7",  text: "Have senior leaders received education or training on neurodiversity in the past 12 months?" },
      { field: "q8",  text: "Does your organisation publicly communicate its commitment to neurodiversity inclusion?" },
      { field: "q9",  text: "Are neurodivergent employees represented in leadership or decision-making roles?" },
    ],
  },
  {
    title: "Recruitment & Onboarding",
    icon: "◇",
    summary: "The hiring funnel is where many neurodivergent candidates are lost — rigid processes and unclear expectations create unnecessary barriers.",
    why: "Inclusive recruitment widens your talent pool and reduces early attrition from candidates who could thrive with small adjustments.",
    points: ["Inclusive job design", "Flexible interviews", "Structured onboarding"],
    tip: "Small changes — sharing interview questions in advance or offering written tasks — can make a big difference without lowering standards.",
    questions: [
      { field: "q10", text: "Are job descriptions reviewed to remove unnecessarily restrictive language or requirements?" },
      { field: "q11", text: "Are alternative interview formats offered to candidates who request them?" },
      { field: "q12", text: "Are reasonable adjustments discussed proactively during the recruitment process?" },
      { field: "q13", text: "Is onboarding structured, clear, and provided in multiple formats?" },
      { field: "q14", text: "Are hiring managers trained to conduct inclusive, bias-aware interviews?" },
    ],
  },
  {
    title: "Work Environment & Adjustments",
    icon: "▣",
    summary: "Day-to-day work practices determine whether neurodivergent employees can perform at their best — or spend energy masking and compensating.",
    why: "Clear adjustment pathways and manager confidence reduce friction, build trust, and improve retention.",
    points: ["Adjustment requests", "Flexible working", "Manager capability"],
    tip: "The best adjustments are often low-cost — noise-cancelling headphones, flexible hours, or written follow-ups after meetings.",
    questions: [
      { field: "q15", text: "Is there a clear, accessible process for employees to request reasonable adjustments?" },
      { field: "q16", text: "Are flexible working arrangements available and actively supported?" },
      { field: "q17", text: "Are managers trained to understand and implement reasonable adjustments?" },
      { field: "q18", text: "Are assistive technologies or tools available to employees who need them?" },
      { field: "q19", text: "Are adjustment requests handled promptly and without stigma?" },
    ],
  },
  {
    title: "Built Environment & Sensory",
    icon: "◎",
    summary: "Physical and sensory environments affect focus, comfort, and wellbeing — especially for people who are sensitive to noise, light, or crowding.",
    why: "Environmental design is often overlooked in DEI work, yet it directly impacts productivity and whether people feel safe at work.",
    points: ["Quiet spaces", "Sensory-aware design", "Personalisation"],
    tip: "Walk through your office at peak hours — notice noise levels, lighting glare, and whether escape routes feel obvious.",
    questions: [
      { field: "q20", text: "Are quiet or low-stimulation spaces available for employees who need them?" },
      { field: "q21", text: "Has your organisation considered lighting, acoustics, and sensory factors in workspace design?" },
      { field: "q22", text: "Is clear, consistent wayfinding and signage in place throughout your premises?" },
      { field: "q23", text: "Are employees able to personalise their workstations to meet sensory needs?" },
      { field: "q24", text: "Has a sensory or environmental audit been conducted in the past two years?" },
    ],
  },
  {
    title: "Talent Management & Development",
    icon: "↑",
    summary: "Career growth systems can unintentionally penalise different working styles — from annual reviews to unstructured promotion conversations.",
    why: "Fair talent processes ensure neurodivergent employees are developed and retained, not overlooked for roles they could excel in.",
    points: ["Fair appraisals", "Equal development access", "Retention insight"],
    tip: "Review whether performance criteria reward only one style of communication or collaboration.",
    questions: [
      { field: "q25", text: "Are performance appraisal processes reviewed to ensure they do not disadvantage neurodivergent employees?" },
      { field: "q26", text: "Do neurodivergent employees have equal access to learning and development opportunities?" },
      { field: "q27", text: "Are strengths-based approaches used in talent management and career development?" },
      { field: "q28", text: "Are mentoring or coaching programmes available and accessible to neurodivergent employees?" },
      { field: "q29", text: "Is retention data monitored to identify whether neurodivergent employees leave at higher rates?" },
    ],
  },
  {
    title: "Communication & Accessibility",
    icon: "◈",
    summary: "How information flows internally shapes who can participate fully — unclear emails, last-minute meetings, and jargon all create friction.",
    why: "Accessible communication is a daily inclusion practice, not a one-off training — it benefits everyone, not only neurodivergent staff.",
    points: ["Plain language", "Multi-format info", "Digital accessibility"],
    tip: "Agendas sent 24 hours ahead and recordings of key meetings are simple wins with wide impact.",
    questions: [
      { field: "q30", text: "Are internal communications written in plain, clear language and free from jargon?" },
      { field: "q31", text: "Is information provided in multiple formats where possible?" },
      { field: "q32", text: "Are meeting agendas shared in advance to support employees who benefit from preparation time?" },
      { field: "q33", text: "Are digital tools and platforms used by your organisation tested for accessibility?" },
      { field: "q34", text: "Are employees able to request communication adjustments?" },
    ],
  },
  {
    title: "Products & Customer Experience",
    icon: "◉",
    summary: "Inclusion extends beyond your workforce — customers and users experience your brand through products, services, and support channels.",
    why: "Neuroinclusive design improves usability for all users and reduces complaints, abandonment, and reputational risk.",
    points: ["User-centred design", "Accessible digital products", "Trained support teams"],
    tip: "Involve neurodivergent users in usability testing early — you'll catch issues that compliance checklists miss.",
    questions: [
      { field: "q35", text: "Are your customer-facing products and services designed with neurodivergent users in mind?" },
      { field: "q36", text: "Are neurodivergent customers or users involved in product testing or feedback processes?" },
      { field: "q37", text: "Are customer service staff trained to support neurodivergent customers effectively?" },
      { field: "q38", text: "Do your digital products meet recognised accessibility standards?" },
      { field: "q39", text: "Is there a clear process for neurodivergent customers to request adjustments or alternative formats?" },
    ],
  },
  {
    title: "Suppliers & Procurement",
    icon: "⬡",
    summary: "Your supply chain amplifies your inclusion impact — procurement choices signal whether inclusion is embedded or only internal-facing.",
    why: "Supplier standards extend your values outward and help build an ecosystem where neurodiversity-led businesses can thrive.",
    points: ["Procurement criteria", "Contract expectations", "Supply chain collaboration"],
    tip: "Start by adding one inclusion question to your standard RFP template — small steps scale over time.",
    questions: [
      { field: "q40", text: "Does your procurement process include questions about suppliers' neurodiversity inclusion practices?" },
      { field: "q41", text: "Are suppliers expected to meet minimum neurodiversity inclusion standards as part of your contracts?" },
      { field: "q42", text: "Do you actively seek to work with neurodiversity-led or neurodiversity-friendly suppliers?" },
      { field: "q43", text: "Is neurodiversity inclusion performance reviewed as part of supplier relationship management?" },
      { field: "q44", text: "Does your organisation share neurodiversity inclusion best practice with its supply chain?" },
    ],
  },
];

const totalSteps     = sections.length + 1; // 0 = details, 1-8 = sections
const currentSection = computed(() => sections[currentStep.value - 1]);
const progressPct    = computed(() => ((currentStep.value) / (totalSteps - 1)) * 100);

const sectionShortNames = [
  "Leadership", "Recruit", "Workplace", "Sensory",
  "Talent", "Comms", "Products", "Suppliers",
];

const progressSteps = [
  { id: "start", short: "Start", label: "Your details" },
  ...sections.map((s, i) => ({
    id: `s${i + 1}`,
    short: sectionShortNames[i],
    label: s.title,
  })),
];

const progressPhase = computed(() => {
  if (currentStep.value === 0) return "Getting started";
  return `Section ${currentStep.value} — ${currentSection.value.title}`;
});

const currentPanel = computed(() => {
  if (currentStep.value === 0) return step0Panel;
  const s = currentSection.value;
  return {
    icon: s.icon,
    tag: `Section ${currentStep.value} of 8`,
    title: s.title,
    summary: s.summary,
    why: s.why,
    points: s.points,
    tip: s.tip,
  };
});

const sectionAnsweredCount = computed(() => {
  if (currentStep.value === 0) return 0;
  return currentSection.value.questions.filter(q => form[q.field]).length;
});

const sectionProgressPct = computed(() => {
  if (currentStep.value === 0) return 0;
  const total = currentSection.value.questions.length;
  return (sectionAnsweredCount.value / total) * 100;
});

function goToStep(i) {
  if (i <= currentStep.value) currentStep.value = i;
}

watch(currentStep, async () => {
  await nextTick();
  questionsScroll.value?.scrollTo({ top: 0, behavior: "smooth" });
});

const allQuestionFields = sections.flatMap(s => s.questions.map(q => q.field));
const form = reactive({
  name: "", designation: "", company_name: "", email: "", contact_number: "",
  ...Object.fromEntries(allQuestionFields.map(f => [f, ""])),
});

function validateStep() {
  Object.keys(errors).forEach(k => delete errors[k]);
  if (currentStep.value === 0) {
    if (!form.name)         errors.name         = true;
    if (!form.designation)  errors.designation  = true;
    if (!form.company_name) errors.company_name = true;
    
    if (!form.email) {
      errors.email = true;
      errors.emailMsg = "Required";
    } else {
      const blockedDomains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "icloud.com"];
      const emailDomain = form.email.split("@")[1]?.toLowerCase();
      if (blockedDomains.includes(emailDomain)) {
        errors.email = true;
        errors.emailMsg = "Please use a company email address";
      }
    }
  } else {
    const section = sections[currentStep.value - 1];
    section.questions.forEach(q => { if (!form[q.field]) errors[q.field] = true; });
  }
  return Object.keys(errors).length === 0;
}

function nextStep() {
  if (validateStep()) currentStep.value++;
}

function fillTestData() {
  const firstNames = ["Alice", "James", "Priya", "Omar", "Sophie", "Liam", "Zara", "Noah"];
  const lastNames  = ["Smith", "Patel", "Johnson", "Ahmed", "Williams", "Khan", "Brown", "Lee"];
  const companies  = ["Acme Ltd", "BrightCo", "Nexora Inc", "Orbital Group", "Vertex Solutions", "Horizon Corp"];
  const roles      = ["HR Director", "DEI Lead", "Operations Manager", "CEO", "Head of Talent"];

  const rnd = arr => arr[Math.floor(Math.random() * arr.length)];

  form.name           = `${rnd(firstNames)} ${rnd(lastNames)}`;
  form.designation    = rnd(roles);
  form.company_name   = rnd(companies);
  form.email          = "aakash.padyachi@orchvate.com";
  form.contact_number = `+44 77${Math.floor(10000000 + Math.random() * 89999999)}`;

  allQuestionFields.forEach(f => { form[f] = rnd(options); });
}

async function submit() {
  
  if (!validateStep()) return;
  submitting.value  = true;
  submitError.value = "";
  try {
    await submitAudit({ ...form });
    submitted.value = true;
    window.scrollTo({ top: 0, behavior: "smooth" });
  } catch (e) {
    submitError.value = e.message;
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
.form-page {
  flex: 1;
  width: 100%;
  height: 100%;
  min-height: 0;
  overflow: hidden;
  background: var(--c-bg);
  background-image:
    linear-gradient(to right, rgba(180,175,165,0.35) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(180,175,165,0.35) 1px, transparent 1px);
  background-size: 32px 32px;
  display: flex; flex-direction: column;
}

.form-inner {
  display: flex; flex-direction: column;
  flex: 1; width: 100%;
  min-height: 0;
  overflow: hidden;
}

/* Header */
.form-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 1rem 2rem;
  border-bottom: 2px solid var(--c-primary-dark);
  background: rgba(245,242,235,0.95);
  backdrop-filter: blur(8px);
  flex-shrink: 0; z-index: 10;
}
.form-logo { display: flex; align-items: center; gap: 0.5rem; font-weight: 800; font-size: 1rem; color: var(--c-primary-dark); font-family: 'Playfair Display', serif; }
.form-logo-mark { font-size: 1.1rem; color: var(--c-accent); background: var(--c-primary-dark); width: 28px; height: 28px; border-radius: 6px; display: grid; place-items: center; }
.fill-btn {
  background: var(--c-primary-dark); color: var(--c-accent);
  border: 2px solid var(--c-primary-dark); border-radius: 99px;
  padding: 0.4rem 1rem; font-size: 0.82rem; font-weight: 700;
  cursor: pointer; transition: all 0.15s; font-family: 'Playfair Display', serif;
  box-shadow: 3px 3px 0 var(--c-accent);
}
.fill-btn:hover { transform: translate(-2px,-2px); box-shadow: 5px 5px 0 var(--c-accent); }
.fill-btn:hover { background: #333; }

/* Step layout — progress left | form + aside right */
.step-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 0;
  overflow: hidden;
  padding: 1.25rem 2rem 0.75rem;
  width: 100%;
}

.step-layout {
  display: grid;
  grid-template-columns: 200px minmax(0, 1fr);
  gap: 1.5rem;
  width: 100%;
  max-width: 1500px;
  height: 100%;
  min-height: 0;
  margin: 0 auto;
  align-items: stretch;
}

.step-center {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(320px, 420px);
  gap: 1.75rem;
  min-width: 0;
  min-height: 0;
  height: 100%;
}

.step-main {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
  height: 100%;
  overflow: hidden;
}

.step-card {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--c-white);
  border-radius: 20px;
  padding: 0;
  border: 2px solid var(--c-primary-dark);
  width: 100%;
}

.step-card-head {
  flex-shrink: 0;
  padding: 2rem 2.5rem 0;
}

.questions-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  overscroll-behavior: contain;
  padding: 1.25rem 2.5rem 2rem;
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.questions-scroll::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

.step-actions {
  flex-shrink: 0;
  padding: 1rem 2.5rem 1.5rem;
  margin-top: 0;
  border-top: 1px solid #E2DDD4;
}

/* Progress — left sidebar */
.progress-sidebar {
  min-height: 0;
  height: 100%;
  overflow-y: auto;
  align-self: stretch;
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.progress-sidebar::-webkit-scrollbar { display: none; }
.progress-wrap {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 1.15rem 1rem 1.25rem;
  background: var(--c-white);
  border: 2px solid var(--c-primary-dark);
  border-radius: 16px;
  box-shadow: 4px 4px 0 var(--c-accent);
}
.progress-header {
  display: flex; flex-direction: column; gap: 0.35rem;
  margin-bottom: 1.1rem; padding-bottom: 1rem;
  border-bottom: 1.5px solid #E2DDD4;
}
.progress-phase {
  font-size: 0.82rem; font-weight: 800; color: var(--c-primary-dark);
  font-family: 'Playfair Display', serif; letter-spacing: -0.02em;
  line-height: 1.3;
}
.progress-pct {
  font-size: 1.1rem; font-weight: 800; color: var(--c-primary-dark);
  font-family: 'Playfair Display', serif;
}
.progress-count {
  font-size: 0.72rem; font-weight: 700; color: #888;
}
.progress-track--vertical {
  --progress-dot: 26px;
  --progress-rail: 4px;
  --progress-pad: 0.4rem;
  position: relative;
  flex: 1;
}
.progress-track--vertical .progress-rail {
  position: absolute;
  left: calc((var(--progress-dot) - var(--progress-rail)) / 2);
  top: calc(var(--progress-pad) + var(--progress-dot) / 2);
  bottom: calc(var(--progress-pad) + var(--progress-dot) / 2);
  width: var(--progress-rail);
  box-sizing: border-box;
  background: #E2DDD4;
  border-radius: 99px;
  border: 1px solid var(--c-primary-dark);
  overflow: hidden;
  z-index: 0;
  pointer-events: none;
}
.progress-track--vertical .progress-fill {
  width: 100%;
  height: 0;
  min-height: 0;
  background: linear-gradient(180deg, var(--c-accent), #A8D820);
  border-radius: 99px;
  transition: height 0.45s cubic-bezier(0.4, 0, 0.2, 1);
}
.progress-track--vertical .progress-steps {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
  position: relative;
  z-index: 1;
  list-style: none;
}
.progress-track--vertical .progress-step {
  display: grid;
  grid-template-columns: var(--progress-dot) 1fr;
  align-items: center;
  column-gap: 0.65rem;
  background: none;
  border: none;
  cursor: pointer;
  padding: var(--progress-pad) 0.35rem var(--progress-pad) 0;
  text-align: left;
  width: 100%;
  border-radius: 8px;
  transition: background 0.15s;
}
.progress-track--vertical .progress-step:hover:not(:disabled) {
  background: var(--c-bg);
}
.progress-step:disabled { cursor: not-allowed; opacity: 0.5; }
.progress-step.done:not(:disabled), .progress-step.active { cursor: pointer; opacity: 1; }
.progress-track--vertical .progress-step-dot {
  width: var(--progress-dot);
  height: var(--progress-dot);
  border-radius: 50%;
  background: var(--c-white);
  border: 2px solid var(--c-primary-dark);
  display: grid;
  place-items: center;
  font-size: 0.68rem;
  font-weight: 800;
  color: #888;
  transition: all 0.25s;
  position: relative;
  z-index: 1;
}
.progress-step.done .progress-step-dot {
  background: var(--c-accent); color: var(--c-primary-dark);
}
.progress-step.active .progress-step-dot {
  background: var(--c-primary-dark); color: var(--c-accent);
  box-shadow: 0 0 0 3px rgba(200,241,53,0.45);
}
.step-check { font-size: 0.7rem; line-height: 1; }
.progress-step-label {
  font-size: 0.68rem; font-weight: 700; color: #999;
  line-height: 1.25;
}
.progress-step.active .progress-step-label,
.progress-step.done .progress-step-label { color: var(--c-primary-dark); font-weight: 800; }

/* Aside panel */
.step-aside {
  min-height: 0;
  height: 100%;
  overflow-y: auto;
  align-self: stretch;
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.step-aside::-webkit-scrollbar { display: none; }
.aside-card {
  background: var(--c-primary-dark); color: var(--c-white);
  border-radius: 20px; padding: 1.75rem;
  border: 2px solid var(--c-primary-dark);
  box-shadow: 6px 6px 0 var(--c-accent);
  animation: asideIn 0.35s ease;
  min-height: 100%;
  display: flex;
  flex-direction: column;
}
@keyframes asideIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.aside-icon {
  width: 44px; height: 44px; border-radius: 12px;
  background: var(--c-accent); color: var(--c-primary-dark);
  display: grid; place-items: center;
  font-size: 1.2rem; font-weight: 800; margin-bottom: 1rem;
  border: 2px solid var(--c-white);
}
.aside-tag {
  display: inline-block; font-size: 0.68rem; font-weight: 800;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--c-accent); margin-bottom: 0.5rem;
}
.aside-title {
  font-size: 1.35rem; font-weight: 800; line-height: 1.25;
  margin-bottom: 0.75rem; color: var(--c-white);
  font-family: 'Playfair Display', serif; letter-spacing: -0.02em;
}
.aside-summary {
  font-size: 0.88rem; line-height: 1.6; color: rgba(255,255,255,0.75);
  margin-bottom: 1.25rem;
}
.aside-block h3 {
  font-size: 0.7rem; font-weight: 800; text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--c-accent); margin-bottom: 0.4rem;
}
.aside-block p {
  font-size: 0.85rem; line-height: 1.55; color: rgba(255,255,255,0.85);
  margin-bottom: 1rem;
}
.aside-points {
  list-style: none; margin: 0 0 1.25rem; padding: 0;
  display: flex; flex-direction: column; gap: 0.5rem;
}
.aside-points li {
  font-size: 0.82rem; color: rgba(255,255,255,0.9);
  padding-left: 1.1rem; position: relative; line-height: 1.45;
}
.aside-points li::before {
  content: ""; position: absolute; left: 0; top: 0.45em;
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--c-accent);
}
.aside-tip {
  background: rgba(200,241,53,0.12);
  border: 1.5px solid rgba(200,241,53,0.35);
  border-radius: 12px; padding: 0.85rem 1rem; margin-bottom: 1rem;
}
.tip-label {
  display: block; font-size: 0.65rem; font-weight: 800;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: var(--c-accent); margin-bottom: 0.35rem;
}
.aside-tip p { font-size: 0.82rem; line-height: 1.5; color: rgba(255,255,255,0.9); margin: 0; }
.aside-progress-mini {
  padding-top: 1rem; border-top: 1px solid rgba(255,255,255,0.15);
  margin-top: auto;
}
.aside-progress-mini span {
  font-size: 0.75rem; color: rgba(255,255,255,0.55);
  display: block; margin-bottom: 0.5rem;
}
.mini-bar {
  height: 6px; background: rgba(255,255,255,0.15);
  border-radius: 99px; overflow: hidden;
}
.mini-fill {
  height: 100%; background: var(--c-accent);
  border-radius: 99px; transition: width 0.3s ease;
}

.step-tag { display: inline-block; background: var(--c-accent); color: var(--c-primary-dark); font-size: 0.7rem; font-weight: 800; padding: 0.2rem 0.7rem; border-radius: 99px; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.85rem; border: 1.5px solid var(--c-primary-dark); font-family: 'Playfair Display', serif; }
.step-card-head h1 { font-size: 1.8rem; font-weight: 800; color: var(--c-primary-dark); letter-spacing: -0.03em; margin-bottom: 0.35rem; font-family: 'Playfair Display', serif; }
.step-sub { color: #999; font-size: 0.875rem; margin-bottom: 0; }

/* Details fields */
.fields-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.field label { display: block; font-size: 0.72rem; font-weight: 800; color: var(--c-primary-dark); margin-bottom: 0.35rem; text-transform: uppercase; letter-spacing: 0.06em; font-family: 'Playfair Display', serif; }
.field input {
  width: 100%; padding: 0.7rem 0.9rem;
  border: 2px solid #E2DDD4; border-radius: 10px;
  font-size: 0.9rem; background: var(--c-bg); color: var(--c-primary-dark);
  transition: border-color 0.15s; font-family: inherit;
}
.field input:focus { outline: none; border-color: var(--c-primary-dark); background: var(--c-white); }
.field input.error { border-color: #ff4444; }
.field-err { color: #ff4444; font-size: 0.78rem; margin-top: 0.25rem; display: block; }

/* Questions */
.questions-list { display: flex; flex-direction: column; gap: 1.5rem; padding-bottom: 0.5rem; }
.q-block:last-child { padding-bottom: 0.25rem; }
.q-number { font-size: 0.68rem; font-weight: 800; color: var(--c-accent); background: var(--c-primary-dark); display: inline-block; padding: 0.15rem 0.55rem; border-radius: 5px; margin-bottom: 0.4rem; letter-spacing: 0.06em; font-family: 'Playfair Display', serif; }
.q-text { font-size: 0.95rem; font-weight: 500; color: var(--c-primary-dark); line-height: 1.55; margin-bottom: 0.75rem; }
.options { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.opt-btn {
  padding: 0.45rem 1rem; border-radius: 99px;
  border: 1.5px solid #E2DDD4; background: var(--c-bg);
  font-size: 0.85rem; font-weight: 500; cursor: pointer; color: #555;
  transition: all 0.15s;
}
.opt-btn:hover { border-color: var(--c-primary-dark); color: var(--c-primary-dark); }
.opt-btn.selected { background: var(--c-primary-dark); color: var(--c-accent); border-color: var(--c-primary-dark); font-weight: 700; }

/* Navigation */
.step-nav { display: flex; align-items: center; justify-content: space-between; width: 100%; }
.btn-back {
  background: var(--c-white); border: 2px solid var(--c-primary-dark); border-radius: 99px;
  padding: 0.65rem 1.4rem; font-size: 0.875rem; font-weight: 700;
  cursor: pointer; color: var(--c-primary-dark); transition: all 0.15s;
  font-family: 'Playfair Display', serif; box-shadow: 3px 3px 0 var(--c-primary-dark);
}
.btn-back:hover { transform: translate(-2px,-2px); box-shadow: 5px 5px 0 var(--c-primary-dark); }
.btn-next {
  background: var(--c-primary-dark); color: var(--c-white); border: 2px solid var(--c-primary-dark); border-radius: 99px;
  padding: 0.7rem 1.75rem; font-size: 0.9rem; font-weight: 800;
  cursor: pointer; transition: all 0.15s; font-family: 'Playfair Display', serif;
  box-shadow: 3px 3px 0 var(--c-accent);
}
.btn-next:hover { transform: translate(-2px,-2px); box-shadow: 5px 5px 0 var(--c-accent); }
.btn-submit {
  background: var(--c-accent); color: var(--c-primary-dark); border: 2px solid var(--c-primary-dark); border-radius: 99px;
  padding: 0.7rem 1.75rem; font-size: 0.9rem; font-weight: 800;
  cursor: pointer; transition: all 0.15s; font-family: 'Playfair Display', serif;
  box-shadow: 3px 3px 0 var(--c-primary-dark);
}
.btn-submit:hover:not(:disabled) { transform: translate(-2px,-2px); box-shadow: 5px 5px 0 var(--c-primary-dark); }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; box-shadow: none; }

/* Footer */
.form-footer {
  flex-shrink: 0;
  text-align: center;
  padding: 0.5rem 0 0.75rem;
}
.admin-link-small { color: #bbb; font-size: 0.8rem; text-decoration: none; }
.admin-link-small:hover { color: var(--c-primary-dark); }

/* Success */
.success-wrap { flex: 1; display: flex; align-items: center; justify-content: center; padding: 2rem; }
.success-box { background: var(--c-white); border-radius: 16px; padding: 3rem 2.5rem; text-align: center; border: 1px solid #E2DDD4; max-width: 440px; width: 100%; }
.success-icon { width: 64px; height: 64px; background: var(--c-accent); border-radius: 50%; display: inline-grid; place-items: center; font-size: 1.8rem; margin-bottom: 1.25rem; }
.success-box h2 { font-size: 1.5rem; font-weight: 800; color: var(--c-primary-dark); margin-bottom: 0.75rem; }
.success-box p  { color: #666; line-height: 1.6; font-size: 0.9rem; margin-bottom: 1.5rem; }

.alert { padding: 0.75rem 1rem; border-radius: 8px; font-size: 0.875rem; margin-top: 1rem; }
.alert-error { background: #FFF0F0; color: #C0392B; border: 1px solid #FFCACA; }

@media (max-width: 900px) {
  .step-wrap { padding: 1rem 1rem 0.5rem; }
  .step-layout {
    grid-template-columns: 72px minmax(0, 1fr);
    gap: 0.75rem;
    max-width: 100%;
  }
  .progress-wrap { padding: 0.75rem 0.5rem; box-shadow: 3px 3px 0 var(--c-accent); }
  .progress-header { display: none; }
  .progress-step-label { display: none; }
  .progress-track--vertical { --progress-dot: 22px; }
  .progress-track--vertical .progress-step-dot { font-size: 0.6rem; }
  .step-center {
    grid-template-columns: 1fr;
    grid-template-rows: auto minmax(0, 1fr);
    gap: 1rem;
  }
  .step-aside {
    grid-row: 1;
    order: -1;
    height: auto;
    max-height: 28vh;
    overflow-y: auto;
  }
  .step-main {
    grid-row: 2;
    min-height: 0;
  }
  .step-card-head { padding: 1.5rem 1.25rem 0; }
  .questions-scroll { padding: 1rem 1.25rem 1.5rem; }
  .progress-sidebar { overflow-y: auto; }
}

@media (max-width: 600px) {
  .fields-grid { grid-template-columns: 1fr; }
  .step-wrap { padding: 1.25rem 1rem 1rem; }
  .form-header { padding: 0.85rem 1rem; }
  .step-layout { grid-template-columns: 52px minmax(0, 1fr); }
  .progress-track--vertical { --progress-dot: 20px; }
  .progress-track--vertical .progress-step-dot { font-size: 0.58rem; }
}
</style>
