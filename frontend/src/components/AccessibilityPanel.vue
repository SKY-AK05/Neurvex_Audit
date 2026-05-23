<template>
  <div class="accessibility-panel-wrap">
    <button
      class="trigger-btn"
      @click="togglePanel"
      aria-haspopup="dialog"
      :aria-expanded="isOpen"
      aria-label="Toggle accessibility settings panel"
      ref="triggerBtn"
    >
      ♿
    </button>

    <div
      v-if="isOpen"
      class="panel-card"
      role="dialog"
      aria-modal="true"
      aria-label="Accessibility Settings"
      @keydown.esc="closePanel"
      ref="panelRef"
      tabindex="-1"
    >
      <h3>Accessibility Settings</h3>
      
      <div class="option-row">
        <label for="dyslexia-toggle">Dyslexia-friendly Font</label>
        <button
          id="dyslexia-toggle"
          class="toggle-switch"
          :class="{ active: dyslexiaMode }"
          @click="toggleDyslexia"
          :aria-pressed="dyslexiaMode"
        >
          {{ dyslexiaMode ? "On" : "Off" }}
        </button>
      </div>

      <div class="option-row">
        <label for="lineheight-toggle">Increased Line Height</label>
        <button
          id="lineheight-toggle"
          class="toggle-switch"
          :class="{ active: largeLineHeight }"
          @click="toggleLineHeight"
          :aria-pressed="largeLineHeight"
        >
          {{ largeLineHeight ? "On" : "Off" }}
        </button>
      </div>

      <div class="option-row">
        <label for="contrast-toggle">High Contrast Theme</label>
        <button
          id="contrast-toggle"
          class="toggle-switch"
          :class="{ active: highContrast }"
          @click="toggleHighContrast"
          :aria-pressed="highContrast"
        >
          {{ highContrast ? "On" : "Off" }}
        </button>
      </div>

      <button @click="closePanel" class="btn btn-secondary close-btn">Close Panel</button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from "vue";
import { useAccessibility } from "../composables/useAccessibility";

const {
  dyslexiaMode,
  largeLineHeight,
  highContrast,
  toggleDyslexia,
  toggleLineHeight,
  toggleHighContrast
} = useAccessibility();

const isOpen = ref(false);
const triggerBtn = ref(null);
const panelRef = ref(null);

function togglePanel() {
  isOpen.value = !isOpen.value;
  if (isOpen.value) {
    nextTick(() => {
      // Focus on the panel when opened for keyboard accessibility
      panelRef.value?.focus();
    });
  }
}

function closePanel() {
  isOpen.value = false;
  triggerBtn.value?.focus();
}
</script>

<style scoped>
.accessibility-panel-wrap { position: fixed; bottom: 20px; right: 20px; z-index: 1000; }
.trigger-btn {
  width: 48px; height: 48px; border-radius: 50%; background: var(--c-primary-dark);
  color: white; border: 2px solid white; font-size: 1.5rem; cursor: pointer;
  box-shadow: 0 4px 10px rgba(0,0,0,0.2); display: flex; align-items: center; justify-content: center;
}
.panel-card {
  position: absolute; bottom: 60px; right: 0; width: 280px; background: white;
  border: 2px solid var(--c-primary-dark); padding: 1.5rem; border-radius: 12px;
  box-shadow: 4px 4px 0 var(--c-primary-dark); display: flex; flex-direction: column; gap: 1rem;
}
.panel-card h3 { font-family: 'Playfair Display', serif; font-size: 1.1rem; margin-bottom: 0.25rem; color: var(--c-primary-dark); }
.option-row { display: flex; justify-content: space-between; align-items: center; }
.option-row label { font-size: 0.85rem; font-weight: bold; color: var(--c-primary-dark); }
.toggle-switch {
  padding: 0.35rem 0.75rem; border: 2px solid var(--c-primary-dark); border-radius: 8px;
  background: #f0f0f0; font-size: 0.8rem; font-weight: bold; cursor: pointer; transition: all 0.15s; color: var(--c-primary-dark);
}
.toggle-switch.active { background: var(--c-accent-retro); }
.close-btn { width: 100%; margin-top: 0.5rem; }
</style>
