<template>
  <div class="theme-tweaker" :class="{ open: isOpen }">
    <button class="tweaker-toggle" @click="isOpen = !isOpen">
      <svg v-if="!isOpen" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
      <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
    </button>
    <div v-if="isOpen" class="tweaker-panel">
      <h3>Theme Colors</h3>
      <div class="color-control" v-for="color in colors" :key="color.var">
        <label :for="color.var">{{ color.name }}</label>
        <div class="input-wrap">
          <input type="color" :id="color.var" v-model="color.value" @input="updateVar(color.var, color.value)" />
          <input type="text" v-model="color.value" @input="updateVar(color.var, color.value)" />
        </div>
      </div>
      
      <div class="bulk-input">
        <label>Paste Colors (Markdown / Key-Value)</label>
        <textarea v-model="bulkColors" @input="applyBulkColors" rows="7" placeholder="Primary: #161057&#10;Secondary: #4A5A89&#10;Main: #009070&#10;Accent: #20C0B0&#10;Retro: #FFFFFF&#10;Background: #F0F0F0&#10;White: #FFFFFF"></textarea>
      </div>
      
      <div class="actions">
        <button class="action-btn" @click="saveTheme">💾 Save Theme</button>
        <div class="dice-actions">
          <button class="action-btn dice-btn" @click="shufflePalette" title="Shuffle existing colors">🎲 Shuffle</button>
          <button class="action-btn dice-btn" @click="randomizeAll" title="Generate random hex colors">🎲 Random</button>
        </div>
        <button class="reset-btn" @click="resetToOriginal">Reset to Original Theme</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';

const isOpen = ref(false);
const bulkColors = ref(`Primary: #161057
Secondary: #4A5A89
Main: #04907C
Accent: #20C0B0
Retro: #FFF8F2
Background: #F5F2EB
White: #FFFFFF`);

const colors = ref([
  { name: 'Primary Dark Blue', var: '--c-primary-dark', value: '#161057' },
  { name: 'Secondary Blue', var: '--c-primary-light', value: '#4A5A89' },
  { name: 'Main Teal', var: '--c-accent', value: '#04907C' },
  { name: 'Accent Teal', var: '--c-accent-secondary', value: '#20C0B0' },
  { name: 'Retro Accent', var: '--c-accent-retro', value: '#FFF8F2' },
  { name: 'Background', var: '--c-bg', value: '#F5F2EB' },
  { name: 'White / Cards', var: '--c-white', value: '#FFFFFF' }
]);

function updateVar(cssVar, val) {
  document.documentElement.style.setProperty(cssVar, val);
}

const originalTheme = {
  '--c-primary-dark': '#1A1A1A',
  '--c-primary-light': '#333333',
  '--c-accent': '#C8F135',
  '--c-accent-secondary': '#A8D115',
  '--c-accent-retro': '#FFFFFF',
  '--c-bg': '#F5F2EB',
  '--c-white': '#FFFFFF'
};

function resetToOriginal() {
  colors.value.forEach(c => {
    c.value = originalTheme[c.var];
    updateVar(c.var, c.value);
  });
  localStorage.removeItem('theme_colors');
}

function saveTheme() {
  const toSave = {};
  colors.value.forEach(c => {
    toSave[c.var] = c.value;
  });
  localStorage.setItem('theme_colors', JSON.stringify(toSave));
  alert('Theme saved to local storage!');
}

function shufflePalette() {
  // Extract current hex values
  let currentHexes = colors.value.map(c => c.value);
  
  // Fisher-Yates Shuffle
  for (let i = currentHexes.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [currentHexes[i], currentHexes[j]] = [currentHexes[j], currentHexes[i]];
  }

  // Re-assign randomly
  colors.value.forEach((c, index) => {
    c.value = currentHexes[index];
    updateVar(c.var, c.value);
  });
}

function randomizeAll() {
  colors.value.forEach(c => {
    // Generate random hex
    const randomHex = '#' + Math.floor(Math.random()*16777215).toString(16).padStart(6, '0').toUpperCase();
    c.value = randomHex;
    updateVar(c.var, c.value);
  });
}

function applyBulkColors() {
  const text = bulkColors.value.toLowerCase();
  
  // Keywords to map to CSS variables
  const mappings = {
    'primary': '--c-primary-dark',
    'dark': '--c-primary-dark',
    'secondary': '--c-primary-light',
    'main': '--c-accent',
    'teal': '--c-accent',
    'accent': '--c-accent',
    'retro': '--c-accent-retro',
    'lime': '--c-accent-retro',
    'background': '--c-bg',
    'bg': '--c-bg',
    'white': '--c-white',
    'card': '--c-white'
  };

  // Find all patterns of (optional word before hex) + hex code
  const regex = /(?:([a-z ]+?)\s*[:=\-]\s*)?(#[0-9a-f]{6}|#[0-9a-f]{3})/gi;
  let match;
  let seqIndex = 0;

  while ((match = regex.exec(text)) !== null) {
    const keyword = match[1] ? match[1].trim() : null;
    const hex = match[2].toUpperCase();
    
    let targetVar = null;
    
    if (keyword) {
      for (const [key, cssVar] of Object.entries(mappings)) {
        if (keyword.includes(key)) {
          targetVar = cssVar;
          break;
        }
      }
    }
    
    if (targetVar) {
      // Smart mapped update
      const colorObj = colors.value.find(c => c.var === targetVar);
      if (colorObj) {
        colorObj.value = hex;
        updateVar(colorObj.var, colorObj.value);
      }
    } else {
      // Fallback sequential update if no keyword matched
      if (seqIndex < colors.value.length) {
        colors.value[seqIndex].value = hex;
        updateVar(colors.value[seqIndex].var, colors.value[seqIndex].value);
        seqIndex++;
      }
    }
  }
}

onMounted(() => {
  const saved = localStorage.getItem('theme_colors');
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      colors.value.forEach(c => {
        if (parsed[c.var]) {
          c.value = parsed[c.var];
        }
      });
    } catch(e) {
      console.error("Could not parse saved theme", e);
    }
  }
  
  // Apply the loaded or default colors
  colors.value.forEach(c => {
    updateVar(c.var, c.value);
  });
});
</script>

<style scoped>
.theme-tweaker {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.tweaker-toggle {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: var(--c-primary-dark);
  color: var(--c-white);
  border: 2px solid var(--c-accent);
  box-shadow: 0 4px 12px rgba(0,0,0,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: transform 0.2s;
}

.tweaker-toggle:hover {
  transform: scale(1.05);
}

.tweaker-panel {
  background: var(--c-white);
  border: 2px solid var(--c-primary-dark);
  border-radius: 12px;
  padding: 1.2rem;
  margin-bottom: 1rem;
  width: 280px;
  box-shadow: 4px 4px 0 var(--c-accent);
  max-height: 80vh;
  overflow-y: auto;
}

.tweaker-panel h3 {
  font-family: 'Playfair Display', serif;
  font-size: 1.1rem;
  margin-bottom: 1rem;
  color: var(--c-primary-dark);
  border-bottom: 1px solid #ccc;
  padding-bottom: 0.5rem;
}

.color-control {
  margin-bottom: 0.8rem;
}

.color-control label {
  display: block;
  font-size: 0.75rem;
  font-weight: 700;
  margin-bottom: 0.3rem;
  color: var(--c-primary-dark);
}

.input-wrap {
  display: flex;
  gap: 0.5rem;
}

.input-wrap input[type="color"] {
  width: 32px;
  height: 32px;
  padding: 0;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
}

.input-wrap input[type="text"] {
  flex: 1;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 0.2rem 0.5rem;
  font-family: monospace;
  font-size: 0.8rem;
}

.actions {
  margin-top: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.dice-actions {
  display: flex;
  gap: 0.5rem;
}

.action-btn, .reset-btn {
  width: 100%;
  padding: 0.5rem;
  background: var(--c-bg);
  border: 1px solid var(--c-primary-dark);
  color: var(--c-primary-dark);
  border-radius: 6px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s;
  font-size: 0.85rem;
}

.dice-btn {
  flex: 1;
}

.action-btn:hover, .reset-btn:hover {
  background: var(--c-primary-dark);
  color: var(--c-white);
}

.reset-btn {
  margin-top: 0.5rem;
  background: #FFF0F0;
  border-color: #C0392B;
  color: #C0392B;
}

.reset-btn:hover {
  background: #C0392B;
  color: #FFF;
}

.bulk-input {
  margin-top: 1rem;
  margin-bottom: 0.5rem;
  padding-top: 1rem;
  border-top: 1px dashed #ccc;
}
.bulk-input label {
  display: block;
  font-size: 0.75rem;
  font-weight: 700;
  margin-bottom: 0.4rem;
  color: var(--c-primary-dark);
}
.bulk-input textarea {
  width: 100%;
  border: 1px solid #ccc;
  border-radius: 4px;
  padding: 0.5rem;
  font-family: monospace;
  font-size: 0.8rem;
  resize: vertical;
}

@media (max-width: 600px) {
  .theme-tweaker {
    bottom: 12px;
    right: 12px;
  }
  .tweaker-toggle {
    width: 38px;
    height: 38px;
    border-width: 1.5px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.25);
  }
  .tweaker-toggle svg {
    width: 16px;
    height: 16px;
  }
}
</style>
