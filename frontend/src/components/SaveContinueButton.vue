<template>
  <div class="save-continue-container">
    <button type="button" class="btn-save-draft" @click="handleSave" :disabled="loading">
      <span v-if="loading" class="btn-loading-state">
        <span class="spinner-dot"></span> Saving…
      </span>
      <span v-else class="btn-content">
        <span class="btn-text-desktop">Save Draft</span>
        <span class="btn-text-mobile">Save</span>
      </span>
    </button>

    <!-- Modal dialog for resume url -->
    <div v-if="showModal" class="save-modal-overlay" @click="showModal = false">
      <div class="save-modal-card" @click.stop>
        <div class="modal-badge-icon">✓</div>
        <h3>Assessment Progress Saved!</h3>
        <p>You can close this tab and resume your assessment anytime within the next <strong>30 days</strong> using your secure link:</p>
        
        <div class="link-box">
          <input type="text" readonly :value="url" ref="linkInput" @click="$event.target.select()" />
          <button @click="copyLink" class="btn-copy-link" type="button">
            {{ copied ? "Copied!" : "Copy Link" }}
          </button>
        </div>

        <p class="modal-hint">We recommend copying or bookmarking this link to return right where you left off.</p>

        <button @click="showModal = false" class="btn-modal-done" type="button">Done</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";

const props = defineProps({
  onSave: { type: Function, required: true }
});

const loading = ref(false);
const showModal = ref(false);
const url = ref("");
const copied = ref(false);
const linkInput = ref(null);

async function handleSave() {
  loading.value = true;
  try {
    const resumeUrl = await props.onSave();
    url.value = resumeUrl;
    showModal.value = true;
  } catch (e) {
    alert(e.message || "Could not save progress. Please ensure your email is entered.");
  } finally {
    loading.value = false;
  }
}

function copyLink() {
  if (linkInput.value) {
    linkInput.value.select();
    navigator.clipboard.writeText(url.value).then(() => {
      copied.value = true;
      setTimeout(() => { copied.value = false; }, 2000);
    });
  }
}
</script>

<style scoped>
.save-continue-container {
  display: inline-flex;
  align-items: center;
}

.btn-save-draft {
  background: #FFFFFF;
  color: var(--c-primary-dark, #161057);
  border: 1.5px solid rgba(22, 16, 87, 0.20);
  border-radius: 99px;
  padding: 0.65rem 1.4rem;
  min-height: 44px;
  font-size: 0.925rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: inherit;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  white-space: nowrap;
  box-shadow: 0 1px 3px rgba(22, 16, 87, 0.05);
  box-sizing: border-box;
}

.btn-save-draft:hover:not(:disabled) {
  background: rgba(4, 144, 124, 0.08);
  border-color: #04907C;
  color: #04907C;
  transform: translateY(-1px);
  box-shadow: 0 3px 8px rgba(4, 144, 124, 0.15);
}

.btn-save-draft:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-content {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.btn-icon {
  font-size: 0.85rem;
}

.btn-loading-state {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  color: #04907C;
}

.spinner-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #04907C;
  animation: pulseDot 1s infinite ease-in-out;
}

@keyframes pulseDot {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50% { opacity: 1; transform: scale(1.2); }
}

.btn-text-mobile {
  display: none;
}

@media (max-width: 600px) {
  .btn-text-desktop {
    display: none;
  }
  .btn-text-mobile {
    display: inline;
  }
  .btn-save-draft {
    padding: 0.45rem 0.9rem;
    font-size: 0.8rem;
  }
}

/* Modal dialog */
.save-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(22, 16, 87, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
  padding: 1rem;
}

.save-modal-card {
  background: #FFFFFF;
  padding: 2.25rem 2rem 1.75rem;
  border-radius: 20px;
  border: 1px solid rgba(22, 16, 87, 0.10);
  box-shadow: 0 20px 40px rgba(22, 16, 87, 0.16);
  max-width: 480px;
  width: 100%;
  text-align: center;
  box-sizing: border-box;
  animation: modalPop 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes modalPop {
  from { opacity: 0; transform: scale(0.95) translateY(8px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}

.modal-badge-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(4, 144, 124, 0.12);
  color: #04907C;
  font-size: 1.5rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 1rem;
}

.save-modal-card h3 {
  font-family: 'Fraunces', serif;
  font-size: 1.35rem;
  margin: 0 0 0.5rem;
  color: var(--c-primary-dark, #161057);
}

.save-modal-card p {
  font-size: 0.9rem;
  color: #475569;
  margin: 0 0 1.25rem;
  line-height: 1.5;
}

.link-box {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  width: 100%;
  box-sizing: border-box;
}

.link-box input {
  flex: 1;
  min-width: 0;
  padding: 0.65rem 0.85rem;
  border: 1.5px solid #CBD5E1;
  border-radius: 10px;
  font-size: 0.85rem;
  background: #F8FAFC;
  color: #1E293B;
  outline: none;
}

.link-box input:focus {
  border-color: #04907C;
  background: #FFFFFF;
}

.btn-copy-link {
  background: #04907C;
  color: #FFFFFF;
  border: none;
  border-radius: 10px;
  padding: 0.65rem 1.15rem;
  font-weight: 700;
  font-size: 0.85rem;
  cursor: pointer;
  transition: background 0.15s ease;
  white-space: nowrap;
}

.btn-copy-link:hover {
  background: #037363;
}

.modal-hint {
  font-size: 0.78rem !important;
  color: #94A3B8 !important;
  margin-bottom: 1.25rem !important;
}

.btn-modal-done {
  background: #F1F5F9;
  color: #334155;
  border: 1px solid #CBD5E1;
  border-radius: 10px;
  padding: 0.65rem 1.5rem;
  font-weight: 600;
  cursor: pointer;
  width: 100%;
  font-size: 0.9rem;
  transition: background 0.15s ease;
}

.btn-modal-done:hover {
  background: #E2E8F0;
}

@media (max-width: 500px) {
  .save-modal-card {
    padding: 1.5rem 1.15rem;
  }
  .link-box {
    flex-direction: column;
  }
  .link-box input, .btn-copy-link {
    width: 100%;
    box-sizing: border-box;
  }
}
</style>
