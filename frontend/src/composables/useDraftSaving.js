import { ref, watch, onUnmounted } from "vue";

export function useDraftSaving(formData, currentStep, API_BASE = "/api") {
  const isSaving = ref(false);
  const saveError = ref("");
  const resumeUrl = ref("");
  const draftId = ref(localStorage.getItem("nd_draft_id") || null);

  // Restore from LocalStorage on load
  function restoreLocalDraft() {
    const saved = localStorage.getItem("nd_draft_state");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        Object.assign(formData, parsed.formData);
        currentStep.value = parsed.currentStep;
      } catch (e) {
        console.error("Failed to parse local draft", e);
      }
    }
  }

  // Auto-save to LocalStorage
  function saveToLocal() {
    const payload = {
      formData: { ...formData },
      currentStep: currentStep.value
    };
    localStorage.setItem("nd_draft_state", JSON.stringify(payload));
  }

  // Sync to Backend
  async function syncToBackend() {
    isSaving.value = true;
    saveError.value = "";
    try {
      const response = await fetch(`${API_BASE}/drafts/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          draft_id: draftId.value || null,
          email: formData.email,
          company_name: formData.company_name,
          form_state: formData,
          current_step: currentStep.value
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Failed to save draft.");
      
      draftId.value = data.draft_id;
      localStorage.setItem("nd_draft_id", data.draft_id);
      resumeUrl.value = data.resume_url;
      return data.resume_url;
    } catch (e) {
      saveError.value = e.message;
      throw e;
    } finally {
      isSaving.value = false;
    }
  }

  function clearDraft() {
    localStorage.removeItem("nd_draft_state");
    localStorage.removeItem("nd_draft_id");
    draftId.value = null;
    resumeUrl.value = "";
  }

  // 30s Auto-save trigger
  const localInterval = setInterval(saveToLocal, 30000);

  // Track manual step changes to save locally
  watch([formData, currentStep], saveToLocal, { deep: true });

  onUnmounted(() => {
    clearInterval(localInterval);
  });

  return {
    isSaving,
    saveError,
    resumeUrl,
    draftId,
    restoreLocalDraft,
    saveToLocal,
    syncToBackend,
    clearDraft
  };
}
