<template>
  <div class="save-continue-container">
    <button
      type="button"
      class="btn-save-draft"
      :class="{ 'is-saved': savedJustNow }"
      @click="handleSave"
      :disabled="loading"
      title="Save your assessment progress"
    >
      <span v-if="loading" class="btn-loading-state">
        <span class="spinner-dot"></span> Saving…
      </span>
      <span v-else-if="savedJustNow" class="btn-saved-state">
        <span class="btn-saved-check">✓</span> Saved
      </span>
      <span v-else class="btn-content">
        <span class="btn-text-desktop">Save Draft</span>
        <span class="btn-text-mobile">Save</span>
      </span>
    </button>

    <!-- Fading Toast Notification (Teleported to body to float smoothly above all layers) -->
    <Teleport to="body">
      <Transition name="toast-fade">
        <div
          v-if="toastMessage"
          class="save-toast-banner"
          :class="toastType"
          role="status"
          aria-live="polite"
        >
          <div class="toast-content">
            <span v-if="toastType === 'success'" class="toast-icon-check">✓</span>
            <span v-else class="toast-icon-warn">!</span>
            <span class="toast-text">{{ toastMessage }}</span>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from "vue";

const props = defineProps({
  onSave: { type: Function, required: true }
});

const loading = ref(false);
const savedJustNow = ref(false);
const toastMessage = ref("");
const toastType = ref("success"); // 'success' | 'warn'
let toastTimer = null;

function showToast(message, type = "success", durationMs = 2600) {
  if (toastTimer) clearTimeout(toastTimer);
  toastMessage.value = message;
  toastType.value = type;
  toastTimer = setTimeout(() => {
    toastMessage.value = "";
  }, durationMs);
}

async function handleSave() {
  if (loading.value) return;
  loading.value = true;
  try {
    await props.onSave();
    savedJustNow.value = true;
    showToast("Draft saved successfully", "success", 2600);
    setTimeout(() => {
      savedJustNow.value = false;
    }, 2400);
  } catch (e) {
    const errorMsg = e.message || "Please enter your email to save your draft progress.";
    showToast(errorMsg, "warn", 3500);
  } finally {
    loading.value = false;
  }
}

onUnmounted(() => {
  if (toastTimer) clearTimeout(toastTimer);
});
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

.btn-save-draft.is-saved {
  background: rgba(0, 144, 112, 0.10);
  border-color: #009070;
  color: #009070;
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

.btn-saved-state {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  color: #009070;
  font-weight: 600;
}

.btn-saved-check {
  font-size: 0.95rem;
  font-weight: 700;
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
</style>

<!-- Unscoped styles for Teleported toast notification -->
<style>
.save-toast-banner {
  position: fixed;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100000;
  display: inline-flex;
  align-items: center;
  padding: 0.75rem 1.4rem;
  border-radius: 99px;
  font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: 0.01em;
  pointer-events: none;
  user-select: none;
  box-shadow: 0 12px 30px -4px rgba(18, 0, 80, 0.32), 0 4px 10px rgba(0, 0, 0, 0.08);
}

.save-toast-banner.success {
  background: #120050;
  color: #FFFFFF;
  border: 1px solid rgba(200, 243, 29, 0.35);
}

.save-toast-banner.warn {
  background: #4A1515;
  color: #FFFFFF;
  border: 1px solid rgba(239, 68, 68, 0.4);
}

.toast-content {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
}

.toast-icon-check {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #009070;
  color: #FFFFFF;
  font-size: 0.75rem;
  font-weight: 800;
  flex-shrink: 0;
}

.toast-icon-warn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #EF4444;
  color: #FFFFFF;
  font-size: 0.75rem;
  font-weight: 800;
  flex-shrink: 0;
}

.toast-text {
  line-height: 1.3;
}

/* Smooth fade and slide animation */
.toast-fade-enter-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.toast-fade-leave-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.toast-fade-enter-from {
  opacity: 0;
  transform: translate(-50%, 16px) scale(0.94);
}

.toast-fade-leave-to {
  opacity: 0;
  transform: translate(-50%, -8px) scale(0.96);
}

@media (max-width: 600px) {
  .save-toast-banner {
    bottom: 24px;
    width: calc(100% - 32px);
    max-width: 360px;
    justify-content: center;
    padding: 0.7rem 1.1rem;
    font-size: 0.85rem;
  }
}
</style>
