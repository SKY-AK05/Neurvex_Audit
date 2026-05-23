<template>
  <div class="rich-editor" :class="{ readonly: readonly }">
    <div class="toolbar">
      <div class="toolbar-tools">
        <!-- Text formatting tools for the live preview -->
        <template v-if="mode === 'visual' && !readonly">
          <button type="button" @click="format('bold')" title="Bold"><b>B</b></button>
          <button type="button" @click="format('italic')" title="Italic"><i>I</i></button>
          <button type="button" @click="format('underline')" title="Underline"><u>U</u></button>
          <span class="toolbar-divider"></span>
          <button type="button" @click="format('insertUnorderedList')" title="Bullet list">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="9" y1="6" x2="20" y2="6"/><line x1="9" y1="12" x2="20" y2="12"/><line x1="9" y1="18" x2="20" y2="18"/><circle cx="4" cy="6" r="1" fill="currentColor"/><circle cx="4" cy="12" r="1" fill="currentColor"/><circle cx="4" cy="18" r="1" fill="currentColor"/></svg>
          </button>
        </template>
        <span class="preview-label" v-else-if="mode === 'visual' && readonly">Read-only Email Preview</span>
        <span class="preview-label" v-else>HTML Source Editor</span>
      </div>

      <!-- Visual / HTML toggle -->
      <div class="mode-toggle">
        <button
          type="button"
          :class="['mode-btn', mode === 'visual' ? 'mode-active' : '']"
          @click="setMode('visual')"
        >Preview / Edit</button>
        <button
          v-if="!readonly"
          type="button"
          :class="['mode-btn', mode === 'html' ? 'mode-active' : '']"
          @click="setMode('html')"
        >HTML</button>
      </div>
    </div>

    <!-- Live Preview Iframe -->
    <iframe
      v-show="mode === 'visual'"
      class="preview-iframe"
      ref="iframeRef"
      @load="onIframeLoad"
      frameborder="0"
      title="Email Preview"
    ></iframe>

    <!-- HTML Source Textarea -->
    <textarea
      v-show="mode === 'html' && !readonly"
      v-model="htmlSource"
      class="html-source"
      spellcheck="false"
      @input="onHtmlInput"
    ></textarea>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from "vue";

const props = defineProps({
  modelValue: { type: String, default: "" },
  readonly:   { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue"]);

const mode = ref("visual");
const htmlSource = ref(props.modelValue || "");
const iframeRef = ref(null);
let isInternalUpdate = false;

function setMode(next) {
  mode.value = next;
  if (next === 'visual') {
    renderIframe(htmlSource.value);
  }
}

function onHtmlInput() {
  isInternalUpdate = true;
  emit("update:modelValue", htmlSource.value);
  setTimeout(() => { isInternalUpdate = false; }, 50);
}

function format(command) {
  if (iframeRef.value?.contentDocument) {
    iframeRef.value.contentDocument.execCommand(command, false, null);
    iframeRef.value.contentWindow.focus();
    syncFromIframe();
  }
}

function syncFromIframe() {
  const doc = iframeRef.value?.contentDocument;
  if (!doc) return;
  isInternalUpdate = true;
  const updatedHtml = "<!DOCTYPE html>\n" + doc.documentElement.outerHTML;
  htmlSource.value = updatedHtml;
  emit("update:modelValue", updatedHtml);
  setTimeout(() => { isInternalUpdate = false; }, 50);
}

function onIframeLoad() {
  // If we just loaded, it might be the initial blank state. We handle rendering manually in renderIframe.
}

function renderIframe(html) {
  if (!iframeRef.value) return;
  const doc = iframeRef.value.contentDocument;
  if (!doc) return;

  doc.open();
  doc.write(html || " ");
  doc.close();

  if (!props.readonly) {
    // Make body editable
    doc.body.contentEditable = "true";
    
    // Hide outline when focused
    const style = doc.createElement('style');
    style.textContent = `
      body[contenteditable] { outline: none; }
      body[contenteditable]:focus { outline: none; }
    `;
    doc.head.appendChild(style);

    // Listen for edits
    doc.body.addEventListener("input", syncFromIframe);
    doc.body.addEventListener("keyup", syncFromIframe);
  }
}

watch(() => props.modelValue, (val) => {
  if (!isInternalUpdate && val !== htmlSource.value) {
    htmlSource.value = val || "";
    if (mode.value === 'visual') {
      renderIframe(htmlSource.value);
    }
  }
});

onMounted(() => {
  if (mode.value === 'visual') {
    setTimeout(() => renderIframe(htmlSource.value), 50);
  }
});
</script>

<style scoped>
.rich-editor {
  border: 2px solid var(--c-primary-dark);
  border-radius: 16px;
  overflow: hidden;
  background: var(--c-white);
  display: flex;
  flex-direction: column;
  height: 600px; /* Fixed height for email preview */
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.5rem 0.65rem;
  background: var(--c-primary-dark);
  flex-wrap: wrap;
  flex-shrink: 0;
}

.toolbar-tools {
  display: flex;
  align-items: center;
  gap: 0.15rem;
  padding: 0.35rem 0.5rem;
}

.toolbar-tools button {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  border: none;
  background: transparent;
  color: rgba(255,255,255,0.75);
  cursor: pointer;
  display: grid;
  place-items: center;
  font-size: 0.85rem;
  transition: all 0.12s;
  font-family: 'Geist', sans-serif;
}
.toolbar-tools button:hover:not(:disabled) {
  background: rgba(255,255,255,0.12);
  color: var(--c-white);
}
.toolbar-tools button:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.toolbar-divider {
  width: 1px;
  height: 18px;
  background: rgba(255,255,255,0.2);
  margin: 0 0.2rem;
}

.preview-label {
  color: var(--c-white);
  font-family: 'Geist', sans-serif;
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.mode-toggle {
  display: flex;
  gap: 0;
  flex-shrink: 0;
}

.mode-btn {
  padding: 0.45rem 0.85rem;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  border: 1px solid rgba(255,255,255,0.35);
  background: transparent;
  color: rgba(255,255,255,0.7);
  cursor: pointer;
  font-family: 'Geist', sans-serif;
  transition: all 0.15s;
}
.mode-btn:first-child { border-radius: 4px 0 0 4px; }
.mode-btn:last-child { border-radius: 0 4px 4px 0; border-left: none; }
.mode-btn.mode-active {
  background: var(--c-accent);
  color: var(--c-primary-dark);
  border-color: var(--c-accent);
}
.mode-btn:hover:not(.mode-active) {
  color: var(--c-white);
  background: rgba(255,255,255,0.08);
}

.preview-iframe {
  width: 100%;
  flex-grow: 1;
  border: none;
  background: #F4F2F0; /* Match email bg */
}

.html-source {
  display: block;
  width: 100%;
  flex-grow: 1;
  padding: 1rem 1.25rem;
  border: none;
  resize: none;
  font-family: 'Courier New', Consolas, monospace;
  font-size: 0.8rem;
  line-height: 1.55;
  color: var(--c-primary-dark);
  background: #faf9f6;
  box-sizing: border-box;
}
.html-source:focus { outline: none; background: var(--c-white); }
</style>
