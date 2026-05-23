# 🎨 ThemeTweaker — Live CSS Variable Editor

A plug-and-play Vue 3 component that adds a floating color editor to any website.
Change, randomize, save, and reset your theme in real-time without touching any code.

---

## ✨ Features

- 🎨 **Live color editing** — Color picker + hex input per variable
- 💾 **Save to localStorage** — Theme persists across page refreshes
- 🎲 **Shuffle** — Rotates your existing colors between variables
- 🎲 **Random** — Generates wild random hex colors
- ↩️ **Reset** — One click back to original theme
- 📋 **Bulk paste** — Paste a color palette in text format and it auto-applies

---

## 🚀 Setup (Vue 3 Project)

### Step 1 — Copy the component

Copy `ThemeTweaker.vue` into your project:

```
your-project/
└── src/
    └── components/
        └── ThemeTweaker.vue   ← paste here
```

---

### Step 2 — Define CSS variables in your root stylesheet

Add your color tokens to your global CSS file (`index.css`, `App.vue <style>`, etc.):

```css
:root {
  --c-primary-dark:      #120050;
  --c-primary-light:     #1A1A80;
  --c-accent:            #009070;
  --c-accent-secondary:  #20C0B0;
  --c-accent-retro:      #C8F31D;
  --c-bg:                #F0F0F0;
  --c-white:             #FFFFFF;
}
```

---

### Step 3 — Import and mount in App.vue

```vue
<template>
  <div>
    <!-- your app content -->
    <router-view />

    <!-- Add ThemeTweaker at the bottom -->
    <ThemeTweaker />
  </div>
</template>

<script setup>
import ThemeTweaker from './components/ThemeTweaker.vue';
</script>
```

---

### Step 4 — Use the variables in your CSS

Replace any hardcoded colors in your components with the CSS variables:

```css
/* Before */
background: #120050;
color: #FFFFFF;

/* After */
background: var(--c-primary-dark);
color: var(--c-white);
```

---

## 📋 Bulk Paste Format

To use the **Paste Colors** box, paste in this exact format.
You can also ask an AI *"Give me a dark cyberpunk theme in this format"* and paste the result directly:

```
Primary: #120050
Secondary: #1A1A80
Main: #009070
Accent: #20C0B0
Retro: #C8F31D
Background: #F0F0F0
White: #FFFFFF
```

### Supported Keywords

| Keyword       | Maps to CSS Variable    |
|---------------|-------------------------|
| `primary`     | `--c-primary-dark`      |
| `dark`        | `--c-primary-dark`      |
| `secondary`   | `--c-primary-light`     |
| `main`        | `--c-accent`            |
| `teal`        | `--c-accent`            |
| `accent`      | `--c-accent`            |
| `retro`       | `--c-accent-retro`      |
| `lime`        | `--c-accent-retro`      |
| `background`  | `--c-bg`                |
| `bg`          | `--c-bg`                |
| `white`       | `--c-white`             |
| `card`        | `--c-white`             |

> **Tip:** If no keyword is found, hex codes are applied sequentially top-to-bottom.

---

## 🎨 To Customize CSS Variables

Open `ThemeTweaker.vue` and edit two sections:

### 1. The `colors` array (controls the editor UI)

```js
const colors = ref([
  { name: 'Primary Dark Blue', var: '--c-primary-dark',     value: '#120050' },
  { name: 'Secondary Blue',    var: '--c-primary-light',    value: '#1A1A80' },
  { name: 'Main Teal',         var: '--c-accent',           value: '#009070' },
  { name: 'Accent Teal',       var: '--c-accent-secondary', value: '#20C0B0' },
  { name: 'Retro Lime Accent', var: '--c-accent-retro',     value: '#C8F31D' },
  { name: 'Background Gray',   var: '--c-bg',               value: '#F0F0F0' },
  { name: 'White / Cards',     var: '--c-white',            value: '#FFFFFF' },
]);
```

### 2. The `originalTheme` object (controls the Reset button)

```js
const originalTheme = {
  '--c-primary-dark':     '#1A1A1A',
  '--c-primary-light':    '#333333',
  '--c-accent':           '#C8F135',
  '--c-accent-secondary': '#A8D115',
  '--c-accent-retro':     '#C8F31D',
  '--c-bg':               '#F5F2EB',
  '--c-white':            '#FFFFFF'
};
```

---

## 📂 File Location

After setup, your folder structure should look like this:

```
your-project/
├── src/
│   ├── components/
│   │   └── ThemeTweaker.vue
│   ├── App.vue              ← import + mount here
│   └── index.css            ← define :root variables here
```

---

## ⚙️ Requirements

| Requirement | Version  |
|-------------|----------|
| Vue         | `^3.x`   |
| Vite        | `^4.x` + |
| Browser     | Any modern browser with CSS variable support |

No extra npm packages required. Zero dependencies.
