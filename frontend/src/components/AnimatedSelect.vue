<template>
  <div class="animated-select" ref="containerRef" :class="{ 'is-open': isOpen, 'has-error': error }">
    <div
      class="select-trigger"
      :class="{ error: error, active: isOpen }"
      tabindex="0"
      role="combobox"
      :aria-expanded="isOpen"
      :aria-haspopup="'listbox'"
      @click="toggleDropdown"
      @keydown.down.prevent="onKeyDown"
      @keydown.up.prevent="onKeyUp"
      @keydown.enter.prevent="onKeyEnter"
      @keydown.esc.prevent="closeDropdown"
    >
      <span v-if="modelValue" class="selected-text">{{ modelValue }}</span>
      <span v-else class="placeholder-text">{{ placeholder || 'Select an option' }}</span>
      <svg class="chevron-icon" :class="{ rotated: isOpen }" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polyline points="6 9 12 15 18 9"></polyline>
      </svg>
    </div>

    <Transition name="dropdown-fade">
      <div v-if="isOpen" class="dropdown-menu" role="listbox">
        <div class="options-list" ref="optionsListRef">
          <div
            v-for="(opt, idx) in options"
            :key="opt"
            class="option-item"
            :class="{
              'is-selected': opt === modelValue,
              'is-highlighted': idx === highlightIndex
            }"
            role="option"
            :aria-selected="opt === modelValue"
            @click="selectOption(opt)"
            @mouseenter="highlightIndex = idx"
          >
            <span>{{ opt }}</span>
            <span v-if="opt === modelValue" class="check-mark">✓</span>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue';

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  options: {
    type: Array,
    default: () => []
  },
  placeholder: {
    type: String,
    default: 'Select an option'
  },
  error: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:modelValue', 'change']);

const isOpen = ref(false);
const highlightIndex = ref(0);
const containerRef = ref(null);
const optionsListRef = ref(null);

function toggleDropdown() {
  if (isOpen.value) {
    closeDropdown();
  } else {
    openDropdown();
  }
}

function openDropdown() {
  isOpen.value = true;
  highlightIndex.value = Math.max(0, props.options.indexOf(props.modelValue));
  nextTick(() => {
    scrollHighlightedIntoView();
    // Scroll dropdown into view if cut off
    scrollDropdownIntoView();
  });
}

function scrollDropdownIntoView() {
  nextTick(() => {
    if (!containerRef.value) return;
    const dropdownMenu = containerRef.value.querySelector('.dropdown-menu');
    if (!dropdownMenu) return;
    
    const rect = dropdownMenu.getBoundingClientRect();
    const viewportHeight = window.innerHeight;
    
    // Check if dropdown is cut off at bottom
    if (rect.bottom > viewportHeight) {
      const scrollAmount = rect.bottom - viewportHeight + 20; // 20px padding
      window.scrollBy({ top: scrollAmount, behavior: 'smooth' });
    }
  });
}

function closeDropdown() {
  isOpen.value = false;
}

function selectOption(opt) {
  emit('update:modelValue', opt);
  emit('change', opt);
  closeDropdown();
}

function onKeyDown() {
  if (!isOpen.value) {
    openDropdown();
    return;
  }
  if (highlightIndex.value < props.options.length - 1) {
    highlightIndex.value++;
    scrollHighlightedIntoView();
  }
}

function onKeyUp() {
  if (highlightIndex.value > 0) {
    highlightIndex.value--;
    scrollHighlightedIntoView();
  }
}

function onKeyEnter() {
  if (isOpen.value && props.options.length > 0) {
    const selected = props.options[highlightIndex.value];
    if (selected) {
      selectOption(selected);
    }
  } else {
    openDropdown();
  }
}

function scrollHighlightedIntoView() {
  nextTick(() => {
    if (!optionsListRef.value) return;
    const highlightedEl = optionsListRef.value.querySelector('.is-highlighted');
    if (highlightedEl) {
      highlightedEl.scrollIntoView({ block: 'nearest' });
    }
  });
}

function handleClickOutside(e) {
  if (containerRef.value && !containerRef.value.contains(e.target)) {
    closeDropdown();
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside);
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
});
</script>

<style scoped>
.animated-select {
  position: relative;
  width: 100%;
}

.select-trigger {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  max-width: 420px;
  padding: 0.55rem 0.75rem;
  background-color: #FFFFFF;
  border: 1.5px solid #3B82F6;
  border-radius: 8px;
  font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
  font-size: 0.85rem;
  color: #120050;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
  min-height: 38px;
  box-sizing: border-box;
}

.select-trigger:hover {
  border-color: #2563EB;
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.1);
}

.select-trigger:focus-visible,
.select-trigger.active {
  outline: none;
  border-color: #2563EB;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.select-trigger.error {
  border-color: #E53E3E;
  background-color: #FFF5F5;
}

.placeholder-text {
  color: #8C827A;
}

.selected-text {
  color: #120050;
  font-weight: 500;
}

.chevron-icon {
  color: #555;
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
  margin-left: 0.4rem;
  width: 16px;
  height: 16px;
}

.chevron-icon.rotated {
  transform: rotate(180deg);
  color: #2563EB;
}

/* Enhanced Dropdown Animations */
.dropdown-menu {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  max-width: 420px;
  background: #FFFFFF;
  border: 1.5px solid #3B82F6;
  border-radius: 8px;
  box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.2), 0 8px 10px -6px rgba(59, 130, 246, 0.15);
  z-index: 100;
  overflow: hidden;
  transform-origin: top center;
}

/* Smooth Dropdown Transition */
.dropdown-fade-enter-active {
  animation: dropdownSlideIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.dropdown-fade-leave-active {
  animation: dropdownSlideOut 0.2s cubic-bezier(0.4, 0, 1, 1);
}

@keyframes dropdownSlideIn {
  from {
    opacity: 0;
    transform: translateY(-8px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes dropdownSlideOut {
  from {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
  to {
    opacity: 0;
    transform: translateY(-8px) scale(0.96);
  }
}

.options-list {
  max-height: 280px;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0.35rem 0;
  scrollbar-width: thin;
  scrollbar-color: rgba(59, 130, 246, 0.3) rgba(59, 130, 246, 0.08);
}

.options-list::-webkit-scrollbar {
  width: 8px;
}

.options-list::-webkit-scrollbar-track {
  background: rgba(59, 130, 246, 0.05);
  border-radius: 4px;
  margin: 4px 0;
}

.options-list::-webkit-scrollbar-thumb {
  background: rgba(59, 130, 246, 0.3);
  border-radius: 4px;
  transition: background 0.2s;
}

.options-list::-webkit-scrollbar-thumb:hover {
  background: rgba(59, 130, 246, 0.5);
}

.option-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.55rem 0.85rem;
  font-size: 0.85rem;
  color: #120050;
  cursor: pointer;
  transition: all 0.15s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.option-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 2.5px;
  background: #3B82F6;
  transform: scaleY(0);
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.option-item:hover::before,
.option-item.is-highlighted::before {
  transform: scaleY(1);
}

.option-item:hover,
.option-item.is-highlighted {
  background-color: #EFF6FF;
  color: #2563EB;
  padding-left: 1rem;
}

.option-item.is-selected {
  background-color: #EFF6FF;
  color: #2563EB;
  font-weight: 600;
}

.check-mark {
  color: #3B82F6;
  font-weight: bold;
  font-size: 1rem;
}

.no-results {
  padding: 1rem 0.85rem;
  text-align: center;
  color: #8C827A;
  font-size: 0.82rem;
}
</style>
