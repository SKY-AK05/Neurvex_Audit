<template>
  <div class="form-page">

    <!-- Success screen -->
    <div v-if="submitted" class="success-wrap">
      <div class="success-box">
        <div class="success-icon">✓</div>
        <h2>Audit Submitted</h2>
        <p>Thank you for completing the Neuro-Inclusive Workplace Index <strong>{{ form.company_name }}</strong>.<br/>You will receive your results by email shortly.</p>
        
        <!-- Post-submission claim account -->
        <div v-if="!hasOrgToken" class="claim-box" style="margin-top: 1.5rem; padding: 1.5rem; border: 2.5px dashed var(--c-primary-dark); border-radius: 12px; background: #FFFDF8;">
          <h4 style="font-family:'Fraunces', serif; font-size:1.1rem; color:var(--c-primary-dark); margin-bottom:0.5rem;">Claim your Organisation Account</h4>
          <p style="font-size:0.8rem; color:#666; margin-bottom:1rem; line-height:1.4;">Create a persistent account to track this audit and view your maturity score progress over time.</p>
          <router-link :to="`/org/login?email=${encodeURIComponent(form.email)}&company=${encodeURIComponent(form.company_name)}`" class="btn btn-primary" style="font-size:0.8rem; padding:0.4rem 1rem;">
            Claim Account & Get Dashboard
          </router-link>
        </div>
      </div>
    </div>

    <div v-else class="form-inner">
      <!-- Header -->
      <header class="form-header">
        <div class="form-header-left">
          <div class="form-logo" @click="onLogoClick">
            <img src="/logonew1.png" alt="" class="form-logo-img" />
            <span class="form-logo-name">Neuro-Inclusive Workplace Index</span>
          </div>
        </div>
        <div class="form-header-right">
          <div class="header-powered">
            <span class="header-powered-label">Powered by</span>
            <img src="/logo_orchvate.png" alt="Orchvate" class="header-powered-logo" />
          </div>
        </div>
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

        <div :class="['step-center', currentStep > 0 ? 'step-center--full' : '']">
        <div class="step-main">
        <div class="step-card" :key="currentStep">
          <!-- Mobile progress header -->
          <div class="mobile-progress-bar">
            <div class="mobile-progress-info">
              <span class="mobile-phase">{{ progressPhase }}</span>
              <span class="mobile-count">{{ currentStep + 1 }} / {{ totalSteps }}</span>
            </div>
            <div class="mobile-progress-track">
              <div class="mobile-progress-fill" :style="{ width: progressPct + '%' }"></div>
            </div>
          </div>

          <div class="step-card-head">
            <div class="step-head-meta">
              <div v-if="currentStep === 0" class="step-tag">Getting Started</div>
              <div v-else class="step-tag">Section {{ currentStep }} of 8</div>
              <button
                v-if="currentStep > 0 && false"
                class="mobile-info-toggle"
                @click="showMobileInfo = !showMobileInfo"
                type="button"
              >
                {{ showMobileInfo ? 'Hide Section Details ▴' : 'Show Section Details ▾' }}
              </button>
            </div>
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
              <div class="field full-width consent-wrapper">
                <label for="gdpr_consent" class="consent-label">
                  <input type="checkbox" id="gdpr_consent" v-model="form.consent_given" class="consent-checkbox" />
                  <span>I consent to the collection and processing of my organisational data in accordance with the Privacy Policy. *</span>
                </label>
                <span v-if="errors.consent_given" class="field-err" style="margin-left: 2rem;">You must provide consent to proceed.</span>
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

              <!-- Progress Saving Button -->
              <div style="display: flex; gap: 0.5rem; margin-left: 0.5rem;">
                <button v-if="currentStep > 0" class="btn-back" @click="startFresh" type="button" style="border: 2px solid #161057; color: #161057; background: transparent; padding: 0.45rem 1rem; border-radius: 99px; font-weight: 700;">↺ Start Fresh</button>
                <SaveContinueButton v-if="currentStep > 0" :onSave="syncToBackend" />
              </div>

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

        <!-- Section context panel (right) — fades out on question steps -->
        <aside :class="['step-aside', showMobileInfo ? 'mobile-show' : '', currentStep > 0 ? 'step-aside--hidden' : '']" :key="currentStep">
          <div class="aside-card">
            <div class="aside-header">
              <img src="/logonew1.png" alt="NIWI" class="aside-logo-img" />
            </div>
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

    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, nextTick, onMounted } from "vue";
import { useRouter } from "vue-router";
import { submitAudit } from "../api";
import { useDraftSaving } from "../composables/useDraftSaving";
import SaveContinueButton from "../components/SaveContinueButton.vue";

const router = useRouter();

// ── Secret admin access: click logo 10 times within 4 seconds ──
const logoClickCount = ref(0);
let logoClickTimer = null;
function onLogoClick() {
  logoClickCount.value++;
  clearTimeout(logoClickTimer);
  if (logoClickCount.value >= 10) {
    logoClickCount.value = 0;
    router.push("/portal");
    return;
  }
  logoClickTimer = setTimeout(() => { logoClickCount.value = 0; }, 4000);
}

const submitted       = ref(false);
const submitting      = ref(false);
const submitError     = ref("");
const currentStep     = ref(0);
const showMobileInfo  = ref(false);
const questionsScroll = ref(null);
const errors      = reactive({});
const options     = ["Yes", "Partially", "No", "Not Sure"];

const step0Panel = {
  icon: "✦",
  tag: "Welcome",
  title: "Neurodiversity Inclusion Audit Questionnaire",
  summary: "Neurodiversity inclusion in the workplace is an emerging priority, with ~15% of people being neurodivergent (e.g., autistic, dyslexic, ADHD) and bringing unique strengths like creativity, innovation, and attention to detail. To help C-suite executives, HR, and DEI leaders assess and improve their company's neuro-inclusivity, we present a short, structured self-audit tool that covers key segments across the employee lifecycle and customer experience, providing a holistic view of neurodiversity (ND) inclusion.",
  why: "The Questionnaire has 8 segments and each have 5 statements. Read each statement and choose the option that best reflects your current reality (not intention).",
  points: [
    "When you submit this form, it will not automatically collect your details like name and email address unless you provide it yourself.",
  ],
  tip: "",
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
      { field: "q5",  text: "We have a clearly defined neurodiversity inclusion strategy with specific, time-bound objectives (e.g., annual goals) that are actively reviewed." },
      { field: "q6",  text: "A senior leader (C-suite or equivalent) is explicitly accountable for neurodiversity inclusion, with visible ownership, cross-organisation coordination, and regular monitoring of progress." },
      { field: "q7",  text: "Senior leaders receive training on neuro-inclusion and actively model inclusive behaviors (e.g., valuing different thinking styles, encouraging psychological safety, celebrating differences)." },
      { field: "q8",  text: "We have an active neurodiversity-focused employee resource group (ERG) or network that is supported, heard, and involved in shaping initiatives and decisions." },
      { field: "q9",  text: "We publicly communicate our commitment to neuro-inclusion and demonstrate it through actions (e.g., campaigns, reporting, partnerships, inclusive employer branding)." },
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
      { field: "q10", text: "We ensure our job descriptions are clear, concise, and aligned with the actual role (tasks, expectations, outcomes), minimising jargon, with a visible commitment to inclusion." },
      { field: "q11", text: "Our application process is transparent and supportive, including clear timelines and stages, explanation of selection methods, a named contact person and multiple contact options (e.g., email, phone) to reduce uncertainty and anxiety for candidates." },
      { field: "q12", text: "Our selection processes include practical or skills-based assessments (e.g., work samples, task-based evaluations, project submissions) and do not rely solely on traditional interviews." },
      { field: "q13", text: "Our interviews are designed to be flexible and inclusive, with options such as providing accommodations, sharing questions in advance, allowing virtual formats or camera flexibility and being open to alternative or asynchronous responses and candidates are invited to share their preferred ways of working and need for reasonable adjustments if any." },
      { field: "q14", text: "Before starting, new hires are supported with a clear point of contact within the team, simple, structured communication about their role and expectations and early conversations about adjustments, so these can be in place from day one where possible." },
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
      { field: "q15", text: "Workplace adjustments are available and accessible at all stages of the employee lifecycle (e.g., recruitment, onboarding, day-to-day work, progression, and transitions)." },
      { field: "q16", text: "There are clear, well-communicated pathways for employees to request adjustments or access support, and this information is easy to find and understand across the organisation." },
      { field: "q17", text: "Managers, HR, and people teams receive training on neurodiversity and are equipped to identify, discuss, and implement appropriate workplace adjustments confidently and consistently." },
      { field: "q18", text: "Where possible, inclusive practices are built into standard ways of working (e.g., flexible communication, clear documentation, meeting norms), reducing the need for individuals to request adjustments." },
      { field: "q19", text: "Adjustment policies and processes are regularly reviewed, using employee and manager feedback as well as data (where available) to assess effectiveness and improve over time." },
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
      { field: "q20", text: "Workplace environments are designed or adapted using inclusive (universal design) principles to reduce sensory and accessibility barriers." },
      { field: "q21", text: "We consider sensory impact in environmental decisions (e.g., lighting, noise, colours, materials, odours) and take steps to minimise common stressors." },
      { field: "q22", text: "Employees have access to different types of workspaces (e.g., quiet, low-stimulation, collaborative), rather than a one-size-fits-all environment." },
      { field: "q23", text: "There are designated quiet or low-stimulation spaces available for employees to focus, take breaks, or regulate when needed." },
      { field: "q24", text: "Hybrid or remote work is not treated as the primary solution for inclusion; we also address barriers within the physical workplace and consider individual needs across different work settings." },
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
      { field: "q25", text: "Managers and team leads are trained in inclusive leadership and are expected to apply these practices in their day-to-day management." },
      { field: "q26", text: "Managers provide regular, structured feedback that is specific, evidence-based, and balanced (recognising strengths as well as areas for development)." },
      { field: "q27", text: "Employees have access to appropriate support (e.g., coaching, wellbeing resources, or specialist support where needed) to help them work effectively and build on their strengths." },
      { field: "q28", text: "Learning and development opportunities are designed to be accessible and inclusive by default (e.g., clear content, flexible formats, self-paced options, inclusive assessments)." },
      { field: "q29", text: "Regular career and development conversations take place, using a strengths-based approach, with clear development plans and appropriate support to help employees progress." },
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
      { field: "q30", text: "Employees are trained to communicate in neuro-inclusive ways, including understanding different communication styles and how to adapt for internal and external audiences." },
      { field: "q31", text: "Organisational communications are typically clear, concise, and well-structured (e.g., use of plain language, bullet points, logical flow), reducing ambiguity and cognitive load." },
      { field: "q32", text: "Information is available in accessible formats where needed (e.g., transcripts, captions, recordings, screen reader compatibility), and accessibility features are actively supported and encouraged." },
      { field: "q33", text: "We use inclusive, respectful language when communicating about neurodiversity, and aim to frame differences in a strengths-based and non-stigmatising way." },
      { field: "q34", text: "Employees and external stakeholders can give feedback on communication and accessibility, and there are clear mechanisms to review and improve based on that input." },
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
      { field: "q35", text: "Products, services, and communication channels (e.g., websites, platforms, social media, physical materials) are designed using clear, structured, and neuro-inclusive formats." },
      { field: "q36", text: "Customers are able to engage through a range of contact methods (e.g., email, phone, webchat, written communication), allowing them to choose what works best for them." },
      { field: "q37", text: "Physical customer environments are designed or adapted to reduce sensory overload where possible (e.g., managing noise, lighting, crowding, and visual stimuli)." },
      { field: "q38", text: "Employees involved in product design and customer service are trained in neurodiversity awareness and inclusive practices." },
      { field: "q39", text: "We regularly assess the neuro-inclusivity of products and customer interactions (e.g., user testing, audits, feedback) and make improvements based on what we learn." },
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
      { field: "q40", text: "Documents and communications with suppliers are clear, structured, and presented in neuro-inclusive formats across both digital and physical channels." },
      { field: "q41", text: "When assessing and selecting suppliers, we consider their commitment to inclusive practices, including neurodiversity where possible." },
      { field: "q42", text: "Employees involved in procurement and supply chain management are trained in neurodiversity awareness and inclusive practices." },
      { field: "q43", text: "Suppliers and vendors are able to engage through a range of contact methods (e.g., email, phone, written communication), supporting different communication preferences." },
      { field: "q44", text: "There are clear opportunities for suppliers and partners to provide feedback on our processes, and this feedback is used to improve inclusivity over time." },
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
  showMobileInfo.value = false;
  await nextTick();
  questionsScroll.value?.scrollTo({ top: 0, behavior: "smooth" });
});

const allQuestionFields = sections.flatMap(s => s.questions.map(q => q.field));
const form = reactive({
  name: "", designation: "", company_name: "", email: "", contact_number: "", consent_given: false,
  ...Object.fromEntries(allQuestionFields.map(f => [f, ""])),
});

const { isSaving, syncToBackend, restoreLocalDraft, clearDraft, draftId } = useDraftSaving(form, currentStep);
const hasOrgToken = computed(() => !!localStorage.getItem("org_token"));

onMounted(() => {
  restoreLocalDraft();
});

watch(() => form, (newForm) => {
  Object.keys(newForm).forEach(k => {
    if (newForm[k] && errors[k]) {
      delete errors[k];
    }
  });
}, { deep: true });

function validateStep() {
  Object.keys(errors).forEach(k => delete errors[k]);
  if (currentStep.value === 0) {
    if (!form.name)         errors.name         = true;
    if (!form.designation)  errors.designation  = true;
    if (!form.company_name) errors.company_name = true;
    if (!form.consent_given) errors.consent_given = true;
    
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

function scrollToError() {
  nextTick(() => {
    const firstError = document.querySelector('.field-err');
    if (firstError) {
      const block = firstError.closest('.q-block') || firstError.closest('.field');
      if (block) {
        block.scrollIntoView({ behavior: 'smooth', block: 'center' });
        block.classList.remove('shake-animation');
        void block.offsetWidth; // trigger reflow
        block.classList.add('shake-animation');
      }
    }
  });
}

function nextStep() {
  if (validateStep()) {
    currentStep.value++;
  } else {
    scrollToError();
  }
}


function resetForm() {
  form.name = "";
  form.designation = "";
  form.company_name = "";
  form.email = "";
  form.contact_number = "";
  form.consent_given = false;
  allQuestionFields.forEach(f => {
    form[f] = "";
  });
}

function startFresh() {
  resetForm();
  clearDraft();
  currentStep.value = 0;
  Object.keys(errors).forEach(k => delete errors[k]);
}

async function submit() {
  if (!validateStep()) {
    scrollToError();
    return;
  }
  submitting.value  = true;
  submitError.value = "";
  try {
    await submitAudit({ ...form, draft_id: draftId.value });
    clearDraft();
    resetForm();
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
    linear-gradient(to right, rgba(180,175,165,0.25) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(180,175,165,0.25) 1px, transparent 1px);
  background-size: 32px 32px;
  border-radius: 32px;
  box-shadow: 0 12px 48px rgba(0,0,0,0.3);
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
  padding: 0.6rem 2rem;
  border-bottom: 2px solid var(--c-primary-dark);
  background: var(--c-bg);
  flex-shrink: 0; z-index: 10;
}
.form-header-left { display: flex; align-items: center; gap: 1rem; }
.form-header-right { display: flex; align-items: center; gap: 1rem; margin-left: auto; }
.form-logo {
  display: flex; align-items: center; gap: 0.5rem;
  font-weight: 800; font-size: 1rem; color: var(--c-primary-dark);
  font-family: 'Fraunces', serif;
  cursor: default;
  user-select: none;
  -webkit-user-select: none;
}
.form-logo-img {
  height: 36px; width: auto; display: block; object-fit: contain;
  border-radius: 6px; flex-shrink: 0;
  pointer-events: none;
}
.form-logo-name {
  font-size: 0.95rem; font-weight: 800; color: var(--c-primary-dark);
  font-family: 'Fraunces', serif;
  cursor: default;
  user-select: none;
}
.header-powered { display: flex; align-items: center; gap: 0.4rem; }
.header-powered-label { font-size: 0.7rem; color: #aaa; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
.header-powered-logo { height: 22px; width: auto; object-fit: contain; opacity: 0.65; }

/* Step layout — progress left | form + aside right */
.step-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-height: 0;
  overflow: hidden;
  padding: 0.75rem 2rem 0.75rem;
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
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 1.75rem;
  min-width: 0;
  min-height: 0;
  height: 100%;
  transition: grid-template-columns 0.45s cubic-bezier(0.4, 0, 0.2, 1),
              gap 0.45s cubic-bezier(0.4, 0, 0.2, 1);
}
.step-center--full {
  grid-template-columns: minmax(0, 1fr) 0px;
  gap: 0;
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
  background: transparent;
  border-radius: 20px;
  padding: 0;
  border: 2px solid #161057;
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
  background: var(--c-white);
  border: 2px solid var(--c-primary-dark);
  border-radius: 16px;
  box-shadow: 4px 4px 0 rgba(22, 16, 87, 0.15);
}
.progress-sidebar::-webkit-scrollbar { display: none; }
.progress-wrap {
  display: flex;
  flex-direction: column;
  padding: 1.15rem 1rem 1.25rem;
  min-height: 100%;
}
.progress-header {
  display: flex; flex-direction: column; gap: 0.35rem;
  margin-bottom: 1.1rem; padding-bottom: 1rem;
  border-bottom: 1.5px solid #E2DDD4;
}
.progress-phase {
  font-size: 0.82rem; font-weight: 800; color: var(--c-primary-dark);
  font-family: 'Fraunces', serif; letter-spacing: -0.02em;
  line-height: 1.3;
}
.progress-pct {
  font-size: 1.1rem; font-weight: 800; color: var(--c-primary-dark);
  font-family: 'Fraunces', serif;
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
  background: linear-gradient(180deg, #161057, #2A2080);
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
  background: #161057; color: #FFFFFF;
}
.progress-step.active .progress-step-dot {
  background: var(--c-primary-dark); color: #FFFFFF;
  box-shadow: 0 0 0 3px rgba(22, 16, 87, 0.25);
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
  overflow-x: hidden;
  align-self: stretch;
  -ms-overflow-style: none;
  scrollbar-width: none;
  background: transparent;
  border-radius: 20px;
  border: 2px solid #161057;
  box-shadow: 6px 6px 0 rgba(22, 16, 87, 0.18);
  /* Smooth collapse */
  opacity: 1;
  transform: translateX(0);
  transition: opacity 0.4s ease, transform 0.4s ease, border-width 0.4s ease;
}
.step-aside--hidden {
  opacity: 0;
  transform: translateX(24px);
  pointer-events: none;
  border-width: 0;
  box-shadow: none;
}
.step-aside::-webkit-scrollbar { display: none; }
.aside-card {
  padding: 1rem 1.35rem 1.5rem;
  color: var(--c-primary-dark);
  min-height: 100%;
  display: flex;
  flex-direction: column;
  animation: asideIn 0.35s ease;
}
@keyframes asideIn {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}
.aside-header {
  display: flex;
  justify-content: flex-end;
  align-items: flex-start;
  margin-bottom: 0.5rem;
  flex-shrink: 0;
}
.aside-logo-img {
  height: 44px;
  width: auto;
  max-width: 100%;
  object-fit: contain;
  display: block;
  border-radius: 6px;
}
.aside-tag {
  display: inline-block; font-size: 0.68rem; font-weight: 800;
  text-transform: uppercase; letter-spacing: 0.08em;
  color: #161057; margin: 0 0 0.35rem;
  font-family: 'Inter', sans-serif;
}
.aside-title {
  font-size: 1.35rem; font-weight: 800; line-height: 1.25;
  margin: 0 0 0.5rem; color: var(--c-primary-dark);
  font-family: 'Inter', sans-serif; letter-spacing: -0.02em;
}
.aside-summary {
  font-size: 0.88rem; line-height: 1.6; color: #555;
  margin: 0 0 1rem;
  font-family: 'Inter', sans-serif;
}
.aside-block h3 {
  font-size: 0.7rem; font-weight: 800; text-transform: uppercase;
  letter-spacing: 0.08em; color: #161057; margin-bottom: 0.4rem;
  font-family: 'Inter', sans-serif;
}
.aside-block p {
  font-size: 0.85rem; line-height: 1.55; color: #444;
  margin-bottom: 1rem;
  font-family: 'Inter', sans-serif;
}
.aside-points {
  list-style: none; margin: 0 0 1.25rem; padding: 0;
  display: flex; flex-direction: column; gap: 0.5rem;
}
.aside-points li {
  font-size: 0.82rem; color: #333;
  padding-left: 1.1rem; position: relative; line-height: 1.45;
  font-family: 'Inter', sans-serif;
}
.aside-points li::before {
  content: ""; position: absolute; left: 0; top: 0.45em;
  width: 6px; height: 6px; border-radius: 50%;
  background: #161057;
}
.aside-progress-mini {
  padding-top: 1rem; border-top: 1px solid rgba(22, 16, 87, 0.2);
  margin-top: auto;
}
.aside-progress-mini span {
  font-size: 0.75rem; color: #888;
  display: block; margin-bottom: 0.5rem;
  font-family: 'Inter', sans-serif;
}
.mini-bar {
  height: 6px; background: rgba(22, 16, 87, 0.12);
  border-radius: 99px; overflow: hidden;
}
.mini-fill {
  height: 100%; background: #161057;
  border-radius: 99px; transition: width 0.3s ease;
}

.step-tag { display: inline-block; background: transparent; color: #161057; font-size: 0.7rem; font-weight: 800; padding: 0.2rem 0.7rem; border-radius: 99px; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 0.85rem; border: 1.5px solid #161057; font-family: 'Fraunces', serif; }
.step-card-head h1 { font-size: 1.8rem; font-weight: 800; color: var(--c-primary-dark); letter-spacing: -0.03em; margin-bottom: 0.35rem; font-family: 'Fraunces', serif; }
.step-sub { color: #999; font-size: 0.875rem; margin-bottom: 0; }

/* Details fields */
.fields-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.field label { display: block; font-size: 0.72rem; font-weight: 800; color: var(--c-primary-dark); margin-bottom: 0.35rem; text-transform: uppercase; letter-spacing: 0.06em; font-family: 'Fraunces', serif; }
.field input:not([type="checkbox"]) {
  width: 100%; padding: 0.7rem 0.9rem;
  border: 2px solid var(--c-primary-dark); border-radius: 10px;
  font-size: 0.9rem; background: var(--c-white); color: var(--c-primary-dark);
  transition: border-color 0.15s, box-shadow 0.15s; font-family: inherit;
}
.field input:not([type="checkbox"]):focus { outline: none; border-color: var(--c-primary-dark); background: var(--c-white); }
.field input:not([type="checkbox"]).error { border-color: #ff4444; }
.field-err { color: #ff4444; font-size: 0.78rem; margin-top: 0.25rem; display: block; }

/* Consent Checkbox Styling */
.consent-wrapper {
  grid-column: 1 / -1;
  margin-top: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.field label.consent-label {
  display: flex;
  gap: 0.75rem;
  align-items: flex-start;
  cursor: pointer;
  font-size: 0.75rem;
  line-height: 1.5;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--c-primary-dark);
  user-select: none;
  margin-bottom: 0;
}
.consent-checkbox {
  appearance: none;
  -webkit-appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  border: 2px solid var(--c-primary-dark);
  background-color: var(--c-white);
  cursor: pointer;
  margin-top: 2px;
  flex-shrink: 0;
  position: relative;
  transition: all 0.2s ease;
  box-shadow: 2px 2px 0 rgba(0,0,0,0.1);
}
.consent-checkbox:hover {
  border-color: var(--c-accent);
  background-color: var(--c-bg);
}
.consent-checkbox:checked {
  background-color: var(--c-primary-dark);
  border-color: var(--c-primary-dark);
  box-shadow: 2px 2px 0 var(--c-accent);
}
.consent-checkbox:checked::after {
  content: "✓";
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: var(--c-accent-retro);
  font-size: 0.85rem;
  font-weight: 900;
}
.consent-checkbox:focus-visible {
  outline: 2px solid var(--c-accent);
  outline-offset: 2px;
}

@keyframes error-shake {
  0% { transform: translateX(0); }
  25% { transform: translateX(-6px); }
  50% { transform: translateX(6px); }
  75% { transform: translateX(-6px); }
  100% { transform: translateX(0); }
}
.shake-animation {
  animation: error-shake 0.4s ease-in-out;
  border-radius: 8px;
  box-shadow: 0 0 0 2px rgba(255, 68, 68, 0.4);
}

/* Mobile progress header */
.mobile-progress-bar {
  display: none;
}
/* Step Head Meta for Mobile Info Toggle */
.step-head-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.85rem;
}
.step-head-meta .step-tag {
  margin-bottom: 0;
}
.mobile-info-toggle {
  display: none;
}

/* Questions */
.questions-list { display: flex; flex-direction: column; gap: 1.5rem; padding-bottom: 0.5rem; }
.q-block:last-child { padding-bottom: 0.25rem; }
.q-number { font-size: 0.68rem; font-weight: 800; color: #FFFFFF; background: var(--c-primary-dark); display: inline-block; padding: 0.15rem 0.55rem; border-radius: 5px; margin-bottom: 0.4rem; letter-spacing: 0.06em; font-family: 'Fraunces', serif; }
.q-text { font-size: 0.95rem; font-weight: 500; color: var(--c-primary-dark); line-height: 1.55; margin-bottom: 0.75rem; }
.options { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.opt-btn {
  padding: 0.45rem 1rem; border-radius: 99px;
  border: 1.5px solid #E2DDD4; background: var(--c-bg);
  font-size: 0.85rem; font-weight: 500; cursor: pointer; color: #555;
  transition: all 0.15s;
}
.opt-btn:hover { border-color: var(--c-primary-dark); color: var(--c-primary-dark); }
.opt-btn.selected { background: var(--c-primary-dark); color: var(--c-bg); border-color: var(--c-primary-dark); font-weight: 700; }

/* Navigation */
.step-nav { display: flex; align-items: center; justify-content: space-between; width: 100%; }
.btn-back {
  background: var(--c-white); border: 2px solid var(--c-primary-dark); border-radius: 99px;
  padding: 0.65rem 1.4rem; font-size: 0.875rem; font-weight: 700;
  cursor: pointer; color: var(--c-primary-dark); transition: all 0.15s;
  font-family: 'Fraunces', serif; box-shadow: 3px 3px 0 var(--c-primary-dark);
}
.btn-back:hover { transform: translate(-2px,-2px); box-shadow: 5px 5px 0 var(--c-primary-dark); }
.btn-next {
  background: var(--c-primary-dark); color: var(--c-white); border: 2px solid var(--c-primary-dark); border-radius: 99px;
  padding: 0.7rem 1.75rem; font-size: 0.9rem; font-weight: 800;
  cursor: pointer; transition: all 0.15s; font-family: 'Fraunces', serif;
  box-shadow: 3px 3px 0 rgba(22, 16, 87, 0.3);
}
.btn-next:hover { transform: translate(-2px,-2px); box-shadow: 5px 5px 0 rgba(22, 16, 87, 0.3); }
.btn-submit {
  background: var(--c-primary-dark); color: var(--c-white); border: 2px solid var(--c-primary-dark); border-radius: 99px;
  padding: 0.7rem 1.75rem; font-size: 0.9rem; font-weight: 800;
  cursor: pointer; transition: all 0.15s; font-family: 'Fraunces', serif;
  box-shadow: 3px 3px 0 rgba(22, 16, 87, 0.3);
}
.btn-submit:hover:not(:disabled) { transform: translate(-2px,-2px); box-shadow: 5px 5px 0 rgba(22, 16, 87, 0.3); }
.btn-submit:disabled { opacity: 0.5; cursor: not-allowed; box-shadow: none; }

/* Footer */
.form-footer {
  flex-shrink: 0;
  display: flex; align-items: center; justify-content: flex-end;
  padding: 0.5rem 5.5rem 0.75rem 2rem; /* right padding clears the fixed accessibility button (48px + 20px margin) */
  border-top: 1px solid rgba(0,0,0,0.08);
  gap: 1rem;
}
.admin-link-small { color: #bbb; font-size: 0.8rem; text-decoration: none; }
.admin-link-small:hover { color: var(--c-primary-dark); }

/* Dev toolbar — fixed bottom-left, clear of the accessibility panel (bottom-right) */
.dev-toolbar {
  position: fixed;
  bottom: 16px;
  left: 16px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  z-index: 900;
}
.dev-btn {
  height: 36px;
  padding: 0 1rem;
  border-radius: 99px;
  font-size: 0.78rem;
  font-weight: 700;
  font-family: 'DM Sans', sans-serif;
  cursor: pointer;
  border: 2px solid var(--c-primary-dark);
  transition: transform 0.12s, box-shadow 0.12s;
  white-space: nowrap;
}
.dev-btn--fill {
  background: var(--c-primary-dark);
  color: var(--c-accent);
  box-shadow: 3px 3px 0 var(--c-accent);
}
.dev-btn--fill:hover { transform: translate(-2px,-2px); box-shadow: 5px 5px 0 var(--c-accent); }
.dev-btn--fresh {
  background: #fff;
  color: var(--c-primary-dark);
  box-shadow: 3px 3px 0 var(--c-primary-dark);
}
.dev-btn--fresh:hover { transform: translate(-2px,-2px); box-shadow: 5px 5px 0 var(--c-primary-dark); }

/* Success */
.success-wrap { flex: 1; display: flex; align-items: center; justify-content: center; padding: 2rem; }
.success-box { background: var(--c-white); border-radius: 16px; padding: 3rem 2.5rem; text-align: center; border: 1px solid #E2DDD4; max-width: 440px; width: 100%; }
.success-icon { width: 64px; height: 64px; background: var(--c-accent); border-radius: 50%; display: inline-grid; place-items: center; font-size: 1.8rem; margin-bottom: 1.25rem; }
.success-box h2 { font-size: 1.5rem; font-weight: 800; color: var(--c-primary-dark); margin-bottom: 0.75rem; }
.success-box p  { color: #666; line-height: 1.6; font-size: 0.9rem; margin-bottom: 1.5rem; }

.alert { padding: 0.75rem 1rem; border-radius: 8px; font-size: 0.875rem; margin-top: 1rem; }
.alert-error { background: #FFF0F0; color: #C0392B; border: 1px solid #FFCACA; }

@media (max-width: 900px) {
  .step-wrap { padding: 0.75rem 0.75rem 0.5rem; }
  .step-layout {
    grid-template-columns: 1fr;
    gap: 0;
    max-width: 100%;
  }
  .progress-sidebar {
    display: none;
  }
  .mobile-progress-bar {
    display: block;
    padding: 1.25rem 1.75rem 0.5rem;
    background: var(--c-white);
    border-bottom: 1px solid #E2DDD4;
  }
  .mobile-progress-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.4rem;
  }
  .mobile-phase {
    font-size: 0.78rem;
    font-weight: 800;
    color: var(--c-primary-dark);
    font-family: 'Fraunces', serif;
  }
  .mobile-count {
    font-size: 0.72rem;
    font-weight: 700;
    color: #888;
  }
  .mobile-progress-track {
    height: 6px;
    background: #E2DDD4;
    border-radius: 99px;
    overflow: hidden;
    border: 1.5px solid var(--c-primary-dark);
  }
  .mobile-progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #161057, #2A2080);
    border-radius: 99px;
    transition: width 0.45s ease;
  }

  .step-center {
    grid-template-columns: 1fr;
    grid-template-rows: auto minmax(0, 1fr);
    gap: 0.75rem;
  }
  .step-aside {
    display: none;
  }
  .step-aside.mobile-show {
    display: block;
    grid-row: 1;
    order: -1;
    height: auto;
    max-height: 38vh;
    overflow-y: auto;
    margin-bottom: 0.5rem;
  }
  .step-main {
    grid-row: 2;
    min-height: 0;
  }
  .step-card-head { padding: 1.5rem 1.75rem 0; }
  .questions-scroll { padding: 1rem 1.75rem 1.5rem; }
  
  .mobile-info-toggle {
    display: inline-flex;
    align-items: center;
    background: transparent;
    color: var(--c-accent);
    border: none;
    box-shadow: none;
    font-size: 0.75rem;
    font-weight: 700;
    cursor: pointer;
    text-decoration: underline;
    text-underline-offset: 3px;
    padding: 0;
    font-family: var(--font-body);
  }
  .mobile-info-toggle:hover {
    color: var(--c-primary-light);
  }
}

@media (max-width: 600px) {
  .fields-grid { grid-template-columns: 1fr; }
  .step-wrap { padding: 0.75rem 0.5rem 0.5rem; }
  .form-header { padding: 0.85rem 1rem; }
  
  .mobile-progress-bar {
    padding: 1.25rem 1.25rem 0.5rem;
  }
  .step-card-head { padding: 1.25rem 1.25rem 0; }
  .step-card-head h1 { font-size: 1.25rem; }
  .questions-scroll { padding: 1rem 1.25rem 1.25rem; }
  .q-text { font-size: 0.88rem; line-height: 1.45; }
  
  .step-tag {
    font-size: 0.65rem;
    padding: 0.15rem 0.55rem;
    border-width: 1px;
    margin-bottom: 0;
  }

  .options {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
    width: 100%;
  }
  .opt-btn {
    width: 100%;
    text-align: center;
    padding: 0.5rem;
    font-size: 0.8rem;
    border-radius: 8px;
  }
  
  .step-actions {
    padding: 0.75rem 1.25rem;
  }
  .step-nav {
    display: flex;
    flex-direction: row;
    gap: 0.5rem;
    align-items: center;
    justify-content: space-between;
    width: 100%;
  }
  .btn-back, .btn-next, .btn-submit, .save-continue-container :deep(.btn) {
    height: 38px;
    padding: 0.4rem 0.7rem;
    font-size: 0.8rem;
    font-weight: 700;
    border-radius: 8px;
    border: 1.5px solid var(--c-primary-dark);
    box-shadow: 2px 2px 0 var(--c-primary-dark);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin: 0;
  }
  .btn-back {
    flex: 1;
    min-width: 60px;
    max-width: 75px;
  }
  .save-continue-container {
    flex: 1.8;
    display: inline-block;
    width: auto;
  }
  .save-continue-container :deep(.btn) {
    width: 100%;
  }
  .btn-next, .btn-submit {
    flex: 1.8;
    min-width: 80px;
    box-shadow: 2px 2px 0 var(--c-accent);
  }
  .btn-submit {
    box-shadow: 2px 2px 0 var(--c-primary-dark);
  }

  .form-footer {
    padding: 0.4rem 1rem 0.5rem;
    justify-content: flex-end;
    align-items: center;
  }
  .dev-btn {
    height: 32px;
    padding: 0 0.75rem;
    font-size: 0.72rem;
  }
}
</style>
