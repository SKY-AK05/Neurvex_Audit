import { ref, watch, onUnmounted } from "vue";

const THIRTY_DAYS_MS = 30 * 24 * 60 * 60 * 1000; // 30 days
const DEBOUNCE_SYNC_MS = 1000; // 1s responsive debounce

export function useDraftSaving(formData, currentStep, API_BASE = "/api") {
  const isSaving = ref(false);
  const saveError = ref("");
  const saveStatus = ref("saved"); // 'idle' | 'saving' | 'saved' | 'error'
  const resumeUrl = ref("");
  const draftId = ref(null);
  const draftRestored = ref(false);
  let lastSyncedEmail = "";

  let debounceTimer = null;
  let resetStatusTimer = null;

  function restoreLocalDraft() {
    const saved = localStorage.getItem("nd_draft_state");
    if (!saved) {
      clearDraft();
      return false;
    }

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
        if (parsed.formData && parsed.formData.email) {
          lastSyncedEmail = parsed.formData.email.trim().toLowerCase();
        }
        draftRestored.value = true;
        saveStatus.value = "saved";
        saveError.value = "";
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

    // If user edited their email since last sync, existing draftId belonged to the previous email
    if (lastSyncedEmail && email.toLowerCase() !== lastSyncedEmail) {
      draftId.value = null;
      localStorage.removeItem("nd_draft_id");
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
      if (!response.ok) {
        // Self-heal: If 403 Forbidden (ownership mismatch) or 404 Not Found (stale/deleted draft),
        // disassociate the stale draft_id, clear it from localStorage, and retry once to create a fresh draft under the current email.
        if ((response.status === 403 || response.status === 404) && draftId.value) {
          console.warn(`Draft ${draftId.value} rejected (${response.status}: ${data.detail}). Creating fresh draft for ${email}.`);
          draftId.value = null;
          localStorage.removeItem("nd_draft_id");

          const retryRes = await fetch(`${API_BASE}/drafts/save`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              draft_id: null,
              email: email,
              company_name: formData.company_name || "Assessment",
              form_state: formData,
              current_step: currentStep.value,
              send_email: sendEmail
            })
          });
          const retryData = await retryRes.json();
          if (!retryRes.ok) throw new Error(retryData.detail || "Failed to save draft.");

          draftId.value = retryData.draft_id;
          localStorage.setItem("nd_draft_id", retryData.draft_id);
          resumeUrl.value = retryData.resume_url;
          saveStatus.value = "saved";
          saveError.value = "";
          lastSyncedEmail = email.toLowerCase();
          saveToLocal();
          return retryData.resume_url;
        }
        throw new Error(data.detail || "Failed to save draft.");
      }

      draftId.value = data.draft_id;
      localStorage.setItem("nd_draft_id", data.draft_id);
      resumeUrl.value = data.resume_url;
      saveStatus.value = "saved";
      saveError.value = "";
      lastSyncedEmail = email.toLowerCase();
      saveToLocal();
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
    saveError.value = "";
    lastSyncedEmail = "";
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
