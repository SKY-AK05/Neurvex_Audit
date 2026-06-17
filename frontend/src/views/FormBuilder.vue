<template>
  <div class="form-builder-page">
    <div class="page-header">
      <div class="header-left">
        <div>
          <h1>Form Builder</h1>
          <p>Manage questionnaire sections, questions, and scoring.</p>
        </div>
      </div>
      <div class="header-actions">
        <button class="btn btn-primary" @click="openSectionModal()">+ Add Section</button>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading form structure...</div>
    
    <div v-else class="sections-list">
      <div v-for="section in sections" :key="section.id" class="card section-card">
        <div class="section-header">
          <div class="section-info">
            <span class="section-icon">{{ section.icon }}</span>
            <h2 class="section-title">{{ section.title }}</h2>
            <span class="section-code">({{ section.section_code }})</span>
          </div>
          <div class="section-actions">
            <button class="btn btn-outline btn-sm" @click="openSectionModal(section)">Edit Section</button>
            <button class="btn btn-outline btn-sm" @click="openQuestionModal(section.id)">+ Add Question</button>
          </div>
        </div>
        
        <div class="questions-list">
          <div v-if="!section.questions || section.questions.length === 0" class="empty-questions">
            No questions in this section yet.
          </div>
          <div v-else v-for="question in section.questions" :key="question.id" class="question-row">
            <div class="q-left">
              <div class="q-title"><strong>{{ question.field_name }}</strong>: {{ question.short_title }}</div>
              <div class="q-text">{{ question.question_text }}</div>
            </div>
            <div class="q-right">
              <button class="btn btn-outline btn-sm" @click="openQuestionModal(section.id, question)">Edit</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Section Modal -->
    <div v-if="showSectionModal" class="modal-overlay" @click.self="closeSectionModal">
      <div class="modal-content">
        <h2>{{ editingSection?.id ? 'Edit Section' : 'Add Section' }}</h2>
        <div class="modal-body">
          <div class="field">
            <label>Section Code (e.g. lc)</label>
            <input v-model="sectionForm.section_code" type="text" />
          </div>
          <div class="field">
            <label>Title</label>
            <input v-model="sectionForm.title" type="text" />
          </div>
          <div class="field">
            <label>Icon</label>
            <input v-model="sectionForm.icon" type="text" />
          </div>
          <div class="field">
            <label>Order Index</label>
            <input v-model.number="sectionForm.order_index" type="number" />
          </div>
          <div class="field">
            <label>Summary</label>
            <textarea v-model="sectionForm.summary" rows="2"></textarea>
          </div>
          <div class="field">
            <label>Why It Matters</label>
            <textarea v-model="sectionForm.why_it_matters" rows="2"></textarea>
          </div>
          <div class="field">
            <label>Tip</label>
            <textarea v-model="sectionForm.tip" rows="2"></textarea>
          </div>
          <div class="field">
            <label>Gating Question (Optional)</label>
            <input v-model="sectionForm.gating_question" type="text" />
          </div>
          <div class="field">
            <label>Gating Field (e.g. has_physical_workspace)</label>
            <input v-model="sectionForm.gating_field" type="text" />
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="closeSectionModal">Cancel</button>
          <button class="btn btn-primary" @click="saveSection">Save</button>
        </div>
      </div>
    </div>

    <!-- Question Modal -->
    <div v-if="showQuestionModal" class="modal-overlay" @click.self="closeQuestionModal">
      <div class="modal-content modal-large">
        <h2>{{ editingQuestion?.id ? 'Edit Question' : 'Add Question' }}</h2>
        <div class="modal-body">
          <div class="field">
            <label>Field Name (e.g. q5)</label>
            <input v-model="questionForm.field_name" type="text" />
          </div>
          <div class="field">
            <label>Short Title</label>
            <input v-model="questionForm.short_title" type="text" />
          </div>
          <div class="field">
            <label>Question Text</label>
            <textarea v-model="questionForm.question_text" rows="3"></textarea>
          </div>
          <div class="field">
            <label>Order Index</label>
            <input v-model.number="questionForm.order_index" type="number" />
          </div>
          
          <div class="score-mapping">
            <h3>Score Mapping</h3>
            <p style="font-size: 0.8rem; color: #666; margin-bottom: 1rem;">Map each answer to a score.</p>
            <div v-for="(val, key) in questionForm.score_mapping" :key="key" class="score-row">
              <span class="score-key">{{ key }}</span>
              <input type="number" v-model.number="questionForm.score_mapping[key]" class="score-input" />
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="closeQuestionModal">Cancel</button>
          <button class="btn btn-primary" @click="saveQuestion">Save</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const sections = ref([]);
const loading = ref(true);

const showSectionModal = ref(false);
const editingSection = ref(null);
const sectionForm = ref({});

const showQuestionModal = ref(false);
const editingQuestion = ref(null);
const currentSectionId = ref(null);
const questionForm = ref({});

async function loadData() {
  loading.value = true;
  try {
    const res = await fetch("/api/form/sections");
    if (res.ok) {
      sections.value = await res.json();
    }
  } catch (err) {
    console.error(err);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadData();
});

// SECTION
function openSectionModal(section = null) {
  editingSection.value = section;
  if (section) {
    sectionForm.value = { ...section };
  } else {
    sectionForm.value = {
      section_code: "", title: "", icon: "◆", summary: "", why_it_matters: "", tip: "", 
      gating_question: "", gating_field: "", order_index: sections.value.length + 1
    };
  }
  showSectionModal.value = true;
}

function closeSectionModal() {
  showSectionModal.value = false;
}

async function saveSection() {
  try {
    const isEdit = !!editingSection.value;
    const url = isEdit ? `/api/form/sections/${editingSection.value.id}` : "/api/form/sections";
    const method = isEdit ? "PUT" : "POST";
    
    // Convert empty strings to null for gating fields
    const payload = { ...sectionForm.value };
    if (!payload.gating_question) payload.gating_question = null;
    if (!payload.gating_field) payload.gating_field = null;

    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    
    if (res.ok) {
      closeSectionModal();
      loadData();
    } else {
      const err = await res.json();
      alert("Error saving section: " + JSON.stringify(err));
    }
  } catch(e) {
    alert("Error: " + e.message);
  }
}

// QUESTION
function openQuestionModal(secId, question = null) {
  currentSectionId.value = secId;
  editingQuestion.value = question;
  if (question) {
    questionForm.value = { ...question, score_mapping: { ...question.score_mapping } };
  } else {
    const sec = sections.value.find(s => s.id === secId);
    const orderIdx = sec?.questions?.length ? sec.questions.length + 1 : 1;
    questionForm.value = {
      field_name: "", short_title: "", question_text: "", order_index: orderIdx,
      score_mapping: { "Yes": 4, "Partially": 2, "No": 0, "Not Sure": 0, "N/A": 0 }
    };
  }
  showQuestionModal.value = true;
}

function closeQuestionModal() {
  showQuestionModal.value = false;
}

async function saveQuestion() {
  try {
    const isEdit = !!editingQuestion.value;
    const url = isEdit ? `/api/form/questions/${editingQuestion.value.id}` : `/api/form/sections/${currentSectionId.value}/questions`;
    const method = isEdit ? "PUT" : "POST";
    
    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(questionForm.value)
    });
    
    if (res.ok) {
      closeQuestionModal();
      loadData();
    } else {
      const err = await res.json();
      alert("Error saving question: " + JSON.stringify(err));
    }
  } catch(e) {
    alert("Error: " + e.message);
  }
}

</script>

<style scoped>
.page-header { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 1.75rem; }
.header-left { display: flex; align-items: flex-end; gap: 2.5rem; }
.page-header h1 { font-size: 2rem; font-weight: 800; color: var(--c-primary-dark); letter-spacing: -0.03em; font-family: 'Fraunces', serif; margin-bottom: 0; line-height: 1; }
.page-header p  { color: #888; font-size: 0.875rem; margin-top: 0.4rem; margin-bottom: 0; }

.section-card {
  margin-bottom: 2rem;
  padding: 1.5rem;
}
.section-header {
  display: flex; justify-content: space-between; align-items: center;
  border-bottom: 2px solid #eee; padding-bottom: 1rem; margin-bottom: 1rem;
}
.section-info { display: flex; align-items: center; gap: 0.75rem; }
.section-icon { font-size: 1.5rem; color: var(--c-accent); }
.section-title { font-size: 1.25rem; font-weight: 800; color: var(--c-primary-dark); margin: 0; font-family: 'Fraunces', serif; }
.section-code { color: #888; font-size: 0.9rem; }
.section-actions { display: flex; gap: 0.5rem; }
.btn-sm { padding: 0.3rem 0.8rem; font-size: 0.75rem; }

.questions-list {
  display: flex; flex-direction: column; gap: 0.75rem;
}
.question-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 1rem; background: #faf9f6; border: 1px solid #ddd; border-radius: 8px;
}
.q-title { font-size: 0.95rem; color: var(--c-primary-dark); margin-bottom: 0.3rem; }
.q-text { font-size: 0.85rem; color: #666; }

.empty-questions { color: #888; font-size: 0.9rem; font-style: italic; }

/* Modals */
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0,0,0,0.5); z-index: 1000;
  display: grid; place-items: center; padding: 2rem;
}
.modal-content {
  background: var(--c-white); border-radius: 12px;
  width: 100%; max-width: 500px;
  max-height: 90vh; overflow-y: auto;
  padding: 1.5rem; border: 2px solid var(--c-primary-dark);
  box-shadow: 6px 6px 0 var(--c-primary-dark);
}
.modal-large { max-width: 700px; }
.modal-content h2 { font-size: 1.5rem; margin-bottom: 1rem; font-family: 'Fraunces', serif; }
.modal-body { display: flex; flex-direction: column; gap: 1rem; }
.modal-footer { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem; }

.score-mapping {
  background: #f5f5f5; padding: 1rem; border-radius: 8px;
}
.score-row {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 0.5rem;
}
.score-key { font-weight: 600; font-size: 0.9rem; }
.score-input { width: 80px; padding: 0.4rem; border: 1px solid #ccc; border-radius: 4px; }
</style>
