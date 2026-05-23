import { ref, onMounted } from "vue";

export function useAccessibility() {
  const dyslexiaMode = ref(false);
  const largeLineHeight = ref(false);
  const highContrast = ref(false);

  function loadSettings() {
    const saved = localStorage.getItem("nd_accessibility");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        dyslexiaMode.value = !!parsed.dyslexiaMode;
        largeLineHeight.value = !!parsed.largeLineHeight;
        highContrast.value = !!parsed.highContrast;
      } catch (e) {
        console.error("Accessibility settings parse failed", e);
      }
    }
  }

  function applySettings() {
    const body = document.body;
    
    if (dyslexiaMode.value) {
      body.classList.add("accessibility-dyslexia");
    } else {
      body.classList.remove("accessibility-dyslexia");
    }

    if (largeLineHeight.value) {
      body.classList.add("accessibility-lineheight");
    } else {
      body.classList.remove("accessibility-lineheight");
    }

    if (highContrast.value) {
      body.classList.add("accessibility-highcontrast");
    } else {
      body.classList.remove("accessibility-highcontrast");
    }

    localStorage.setItem("nd_accessibility", JSON.stringify({
      dyslexiaMode: dyslexiaMode.value,
      largeLineHeight: largeLineHeight.value,
      highContrast: highContrast.value
    }));
  }

  function toggleDyslexia() {
    dyslexiaMode.value = !dyslexiaMode.value;
    applySettings();
  }

  function toggleLineHeight() {
    largeLineHeight.value = !largeLineHeight.value;
    applySettings();
  }

  function toggleHighContrast() {
    highContrast.value = !highContrast.value;
    applySettings();
  }

  onMounted(() => {
    loadSettings();
    applySettings();
  });

  return {
    dyslexiaMode,
    largeLineHeight,
    highContrast,
    toggleDyslexia,
    toggleLineHeight,
    toggleHighContrast
  };
}
