import { ref, watch, onUnmounted } from "vue";

const THIRTY_DAYS_MS = 30 * 24 * 60 * 60 * 1000; // 30 days
const DEBOUNCE_SYNC_MS = 1000; // 1s responsive debounce

export function useDraftSaving(formData, currentStep, API_BASE = "/api") {
  const isSaving = ref(false);
  const saveError = ref("");
  const saveStatus = ref("saved"); // 'idle' | 'saving' | 'saved' | 'error'
  const resumeUrl = ref("");
  const draftId = ref(localStorage.getItem("nd_draft_id") || null);
  const draftRestored = ref(false);

  let debounceTimer = null;
  let resetStatusTimer = null;

  function restoreLocalDraft() {
    const saved = localStorage.getItem("nd_draft_state");
    if (!saved) return false;

    const savedAt = parseInt(localStorage.getItem("nd_saved_at") || "0", 10);
    const isExpired = savedAt > 0 && (Date.now() - savedAt > THIRTY_DAYS_MS);

    if (isExpired) {
      clearDraft();
      return false;
    }

    try {
      const parsed = JSON.parse(saved);
      if (parsed && parsed.formData) {
        Object.assign(formData, parsed.formData);
        if (typeof parsed.currentStep === "number" && parsed.currentStep > 0) {
          currentStep.value = parsed.currentStep;
        }
        if (parsed.draftId) {
          draftId.value = parsed.draftId;
        }
        draftRestored.value = true;
        saveStatus.value = "saved";
        localStorage.removeItem("nd_resume_ready");
        return true;
      }
    } catch (e) {
      console.error("Failed to parse local draft", e);
    }
    return false;
  }

  function saveToLocal() {
    const payload = {
      formData: { ...formData },
      currentStep: currentStep.value,
      draftId: draftId.value,
    };
    localStorage.setItem("nd_draft_state", JSON.stringify(payload));
    localStorage.setItem("nd_saved_at", String(Date.now()));
  }

  async function syncToBackend(sendEmail = false) {
    const email = (formData.email || "").trim();
    if (!email) {
      saveToLocal();
      isSaving.value = false;
      saveStatus.value = "saved";
      return "";
    }

    isSaving.value = true;
    saveStatus.value = "saving";
    saveError.value = "";

    try {
      const response = await fetch(`${API_BASE}/drafts/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          draft_id: draftId.value || null,
          email: email,
          company_name: formData.company_name || "Assessment",
          form_state: formData,
          current_step: currentStep.value,
          send_email: sendEmail
        })
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Failed to save draft.");

      draftId.value = data.draft_id;
      localStorage.setItem("nd_draft_id", data.draft_id);
      resumeUrl.value = data.resume_url;
      saveStatus.value = "saved";
      return data.resume_url;
    } catch (e) {
      saveError.value = e.message;
      saveStatus.value = "error";
      if (sendEmail) throw e;
      return "";
    } finally {
      isSaving.value = false;
    }
  }

  // As user types or changes an answer: immediately shows loading/saving, then flips to saved
  function triggerAutoSave() {
    saveToLocal();
    isSaving.value = true;
    saveStatus.value = "saving";

    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(async () => {
      if (formData.email && formData.email.trim()) {
        await syncToBackend(false);
      } else {
        // Saved locally to browser cache
        isSaving.value = false;
        saveStatus.value = "saved";
      }
    }, DEBOUNCE_SYNC_MS);
  }

  function clearDraft() {
    localStorage.removeItem("nd_draft_state");
    localStorage.removeItem("nd_draft_id");
    localStorage.removeItem("nd_resume_ready");
    localStorage.removeItem("nd_resume_at");
    localStorage.removeItem("nd_saved_at");
    draftId.value = null;
    resumeUrl.value = "";
    draftRestored.value = false;
    saveStatus.value = "saved";
  }

  // Watch for step changes: flush save immediately
  watch(currentStep, () => {
    saveToLocal();
    if (formData.email && formData.email.trim()) {
      if (debounceTimer) clearTimeout(debounceTimer);
      syncToBackend(false);
    }
  });

  // Watch for form changes: trigger auto-save (loads and saves as user types)
  watch(formData, triggerAutoSave, { deep: true });

  const localInterval = setInterval(saveToLocal, 30000);

  onUnmounted(() => {
    clearInterval(localInterval);
    if (debounceTimer) clearTimeout(debounceTimer);
    if (resetStatusTimer) clearTimeout(resetStatusTimer);
  });

  return {
    isSaving,
    saveError,
    saveStatus,
    resumeUrl,
    draftId,
    draftRestored,
    restoreLocalDraft,
    saveToLocal,
    syncToBackend,
    clearDraft,
  };
}
