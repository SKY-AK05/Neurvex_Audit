import { ref, watch, onUnmounted } from "vue";

const RESUME_SESSION_MS = 30 * 60 * 1000; // 30 minutes

export function useDraftSaving(formData, currentStep, API_BASE = "/api") {
  const isSaving = ref(false);
  const saveError = ref("");
  const resumeUrl = ref("");
  const draftId = ref(localStorage.getItem("nd_draft_id") || null);

  // Restore from LocalStorage — ONLY if the user arrived via a resume link.
  //
  // Flow:
  //   Fresh visit  → wipe any leftover draft, form starts blank.
  //   Resume link  → ResumeDraft.vue sets "nd_resume_ready" + "nd_resume_at" timestamp,
  //                  we restore the draft and start a 30-minute session window.
  //   After 30 min → draft is treated as expired; next load starts blank.
  //   Start Fresh  → call clearDraft() which wipes everything immediately.
  function restoreLocalDraft() {
    const resumeReady = localStorage.getItem("nd_resume_ready");

    if (!resumeReady) {
      // Fresh visit — wipe any leftover draft so the form is always blank
      localStorage.removeItem("nd_draft_state");
      localStorage.removeItem("nd_draft_id");
      localStorage.removeItem("nd_resume_at");
      return;
    }

    // Check 30-minute session window
    const resumedAt = parseInt(localStorage.getItem("nd_resume_at") || "0", 10);
    const expired = Date.now() - resumedAt > RESUME_SESSION_MS;

    // Consume the flag immediately (single-use regardless of expiry)
    localStorage.removeItem("nd_resume_ready");

    if (expired) {
      localStorage.removeItem("nd_draft_state");
      localStorage.removeItem("nd_draft_id");
      localStorage.removeItem("nd_resume_at");
      return;
    }

    const saved = localStorage.getItem("nd_draft_state");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        Object.assign(formData, parsed.formData);
        currentStep.value = parsed.currentStep;
        if (parsed.draftId) draftId.value = parsed.draftId;
      } catch (e) {
        console.error("Failed to parse local draft", e);
      }
    }
  }

  // Auto-save to LocalStorage (includes draftId so it survives page reloads within session)
  function saveToLocal() {
    const payload = {
      formData: { ...formData },
      currentStep: currentStep.value,
      draftId: draftId.value,
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
    localStorage.removeItem("nd_resume_ready");
    localStorage.removeItem("nd_resume_at");
    draftId.value = null;
    resumeUrl.value = "";
  }

  // 30s auto-save to localStorage
  const localInterval = setInterval(saveToLocal, 30000);

  // Also save on every form/step change
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
    clearDraft,
  };
}
