<template>
  <div class="save-continue-container">
    <button type="button" class="btn btn-outline" @click="handleSave" :disabled="loading">
      {{ loading ? "Saving..." : "Save and Continue Later" }}
    </button>

    <!-- Modal dialog for resume url -->
    <div v-if="showModal" class="save-modal-overlay" @click="showModal = false">
      <div class="save-modal-card" @click.stop>
        <h3>Audit Saved!</h3>
        <p>You can close this tab and resume your audit anytime within the next 7 days using the link below:</p>
        
        <div class="link-box">
          <input type="text" readonly :value="url" ref="linkInput" />
          <button @click="copyLink" class="btn btn-primary">
            {{ copied ? "Copied!" : "Copy Link" }}
          </button>
        </div>

        <button @click="showModal = false" class="btn btn-secondary close-btn">Done</button>
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
    alert("Could not save progress. Please ensure you filled in your name and email on step 1.");
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
.save-continue-container { display: inline-block; }
.save-modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.6); display: flex; justify-content: center; align-items: center; z-index: 1000;
}
.save-modal-card {
  background: white; padding: 2rem; border-radius: 16px; border: 2px solid var(--c-primary-dark);
  box-shadow: 4px 4px 0 var(--c-primary-dark); max-width: 500px; width: 90%; text-align: center;
}
.save-modal-card h3 { font-family: 'Playfair Display', serif; font-size: 1.5rem; margin-bottom: 0.75rem; color: var(--c-primary-dark); }
.save-modal-card p { font-size: 0.9rem; color: #666; margin-bottom: 1.5rem; line-height: 1.5; }
.link-box { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
.link-box input {
  flex: 1; padding: 0.6rem 0.8rem; border: 2px solid var(--c-primary-dark); border-radius: 8px; font-size: 0.85rem; background: #fff; color: #333;
}
.close-btn { margin-top: 1rem; width: 100%; }
</style>
