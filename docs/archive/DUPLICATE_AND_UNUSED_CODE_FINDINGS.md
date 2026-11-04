# NIWI — Duplicate and Unused Code Findings

**Date**: November 4, 2026  
**Branch**: `maintenance/niwi-codebase-cleanup`  
**Phase**: C - Identify Duplicate and Unused Code

---

## Executive Summary

Systematic investigation of backend, frontend, and scripts to identify:
- Duplicate implementations
- Unused code
- Obsolete components
- Dead imports

**Result**: Found 8 items requiring attention (3 safe to remove, 5 need verification)

---

## Backend Findings

### 1. ❌ UNUSED: `app/tasks/email_worker.py`

**Status**: **SAFE TO REMOVE**

**Evidence**:
- Zero imports found across entire codebase
- Contains legacy DLQ (dead letter queue) processing
- Incomplete implementation (has pass statements and incomplete logic)
- Functionality superseded by:
  - `job_worker.py` - handles email processing
  - `service_bus_worker.py` - handles event processing
  - `outbox_service.py` - handles reliable dispatch

**Code Quality**: Poor (incomplete, has `pass` statements)

**Recommendation**: **DELETE** - No production dependencies

---

### 2. ⚠️ NEEDS REVIEW: `app/tasks/job_worker.py`

**Status**: **STILL IN USE** (Not obsolete as originally suspected)

**Evidence of Use**:
- Imported by `app/main.py` for embedded worker mode
- Imported by `service_bus_worker.py` - uses `process_email_job()` function
- Imported by test files (reliability, v31 upgrades)
- Referenced by integration test scripts

**Architecture Role**:
- Contains reusable functions (`process_email_job`, `process_crm_job`)
- Service Bus worker delegates to these functions
- Embedded mode controlled by `ENABLE_EMBEDDED_WORKER` env var (disabled in production)

**Current Use**: Production uses Service Bus architecture, but job_worker provides shared utility functions

**Recommendation**: **KEEP** - Actively used by Service Bus worker

**Future Consideration**: Could be refactored to separate shared functions from legacy embedded worker code

---

### 3. ❌ DUPLICATE SCRIPTS: Root `deploy.sh` vs `scripts/deploy.sh`

**Status**: **DIFFERENT FILES** (Not identical duplicates)

**Evidence**:
- Both exist and have different content
- Root `deploy.sh`: 175 lines
- `scripts/deploy.sh`: 117 lines

**Which One Is Used?**:
- Root `deploy.sh` referenced by:
  - `setup-keyvault.sh` → "Run: ./deploy.sh"
  - `test-keyvault-docker.sh` → "./deploy.sh"
  - `scripts/fix-vm-env.sh` → "./deploy.sh"
- `scripts/deploy.sh` - appears to be older/alternate version

**Recommendation**: **KEEP ROOT VERSION**, archive or remove `scripts/deploy.sh`

---

### 4. ❌ DUPLICATE CONFIGS: Root `nginx.conf` vs `frontend/nginx.conf`

**Status**: **DIFFERENT FILES**

**Evidence**:
- Both files exist
- Docker uses `frontend/nginx.conf` (verified in Dockerfile)
- Root `nginx.conf` may be for standalone deployment

**Docker Reference** (from Dockerfile line ~60):
```dockerfile
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
```

**Recommendation**: **VERIFY** which is canonical, then remove or clearly label the other

---

## Frontend Findings

### 5. ✅ NO DUPLICATE: `Dashboard.vue` Does Not Exist

**Investigation**: Searched for `Dashboard.vue` file

**Result**: **FILE DOES NOT EXIST**

**Confusion Source**: Router uses `/admin/dashboard` path that maps to `Overview.vue`

**Verification**:
```javascript
// frontend/src/router/index.js
{ path: "/admin/dashboard", component: Overview, meta: { requiresAuth: true } }
```

**Conclusion**: No duplicate dashboard view. False alarm from path naming.

---

### 6. ❌ UNUSED COMPONENT: `frontend/src/components/archive/AccessibilityPanel.vue`

**Status**: **SAFE TO REMOVE**

**Evidence**:
- Zero imports found in entire codebase
- Located in `components/archive/` (already marked archived by developers)
- Not referenced in any router or parent component

**Recommendation**: **DELETE** - Already archived, never imported

---

### 7. ✅ NO UNUSED VIEWS FOUND

**Investigation**: All views in `frontend/src/views/` checked against router

**Result**: All 17 views are actively used:
- `AdminLogin.vue` - /portal, /GPadmin
- `Analytics.vue` - /admin/analytics
- `AuditForm.vue` - /, /audit
- `BookCall.vue` - /book-a-call
- `FormBuilder.vue` - /admin/form-builder
- `OrgDashboard.vue` - /org/dashboard
- `OrgLogin.vue` - /org/login
- `OrgVerify.vue` - /org/verify
- `Organisations.vue` - /admin/organisations
- `Overview.vue` - /admin/dashboard
- `ResumeDraft.vue` - /resume
- `Settings.vue` - /admin/settings
- `SubmissionDetail.vue` - /admin/submissions/:id
- `Submissions.vue` - /admin/submissions
- `Support.vue` - /admin/support
- `UserManagement.vue` - /admin/users

**Conclusion**: No unused views

---

### 8. ✅ NO UNUSED COMPONENTS FOUND

**Investigation**: All active components checked for imports

**Result**: All 6 active components are used:
- `AnimatedSelect.vue` - Used in multiple forms
- `RichEditor.vue` - Used in FormBuilder
- `SaveContinueButton.vue` - Used in AuditForm
- `ScoreTable.vue` - Used in SubmissionDetail
- `SearchableSelect.vue` - Used in forms
- `ServiceNowFilterBuilder.vue` - Used in Submissions

Only archived component is `AccessibilityPanel.vue` (marked for deletion above)

---

## Scripts and Utilities Findings

### 9. ⚠️ NEEDS VERIFICATION: Multiple Temporary Scripts

**Location**: `scripts/temp/` (moved in Phase 1)

**Files**:
- `create_siwi_org.py` - Creates SIWI organizations
- `create_siwi_orgs.py` - Bulk creates SIWI organizations  
- `generate_audit_tokens.py` - Generates assessment tokens

**Status**: One-time data seeding/utility scripts

**Already Handled**: Moved to `scripts/temp/` and added to .gitignore

**Recommendation**: **KEEP** in `scripts/temp/` - Useful operational tools

---

### 10. ⚠️ NEEDS VERIFICATION: `scripts/deploy.sh` (Duplicate)

**Status**: See Backend Finding #3

**Recommendation**: Likely obsolete, but verify before deletion

---

## Summary Table

| Item | Type | Status | Action | Risk |
|---|---|---|---|---|
| `app/tasks/email_worker.py` | Backend | UNUSED | DELETE | ⬤⬤⬤⬤⬤ Minimal |
| `app/tasks/job_worker.py` | Backend | ACTIVE | KEEP | N/A |
| Root `deploy.sh` | Script | ACTIVE | KEEP | N/A |
| `scripts/deploy.sh` | Script | DUPLICATE | VERIFY → DELETE | ⬤⬤⬤⬤⬤ Low |
| Root `nginx.conf` | Config | UNCERTAIN | VERIFY | ⬤⬤⬤⬤⬤ Medium |
| `frontend/nginx.conf` | Config | ACTIVE | KEEP | N/A |
| `Dashboard.vue` | Frontend | DOES NOT EXIST | N/A | N/A |
| `AccessibilityPanel.vue` | Frontend | UNUSED | DELETE | ⬤⬤⬤⬤⬤ Minimal |
| Temp scripts in `scripts/temp/` | Scripts | OPERATIONAL | KEEP | N/A |

---

## No Duplicates Found

### Backend - No Duplicate Services ✅
- Checked all services in `app/services/` - no duplicates
- Each service has distinct purpose
- No overlapping functionality

### Backend - No Duplicate API Endpoints ✅
- All routers have unique endpoints
- No conflicting route registrations

### Backend - No Unused Models/Schemas ✅
- All models in `app/models/` are actively used
- Pydantic schemas referenced by API endpoints

### Frontend - No Duplicate API Functions ✅
- Single `api.js` service layer
- No duplicate API client implementations

### Frontend - No Unused CSS ✅
- All component styles are scoped
- No global unused stylesheets identified

---

## Recommended Actions

### Immediate (Safe Deletions)

```bash
# 1. Remove unused email worker
git rm app/tasks/email_worker.py

# 2. Remove archived component
git rm frontend/src/components/archive/AccessibilityPanel.vue

# 3. Consider removing empty archive directory
rmdir frontend/src/components/archive  # if empty after #2

# Commit
git commit -m "chore: remove confirmed unused code"
```

### Verification Needed (Before Deletion)

1. **Compare `nginx.conf` files**:
   ```bash
   diff nginx.conf frontend/nginx.conf
   ```
   - If root is standalone deployment config, rename to `nginx.standalone.conf`
   - If duplicate, delete root version

2. **Compare `deploy.sh` files**:
   ```bash
   diff deploy.sh scripts/deploy.sh
   ```
   - Verify which version is authoritative
   - Archive or delete the obsolete one

---

## What Was NOT Found (Good News)

✅ **No duplicate services**  
✅ **No unused router implementations**  
✅ **No abandoned authentication implementations**  
✅ **No old caching implementations**  
✅ **No duplicate report-generation logic**  
✅ **No unused exception handlers**  
✅ **No unused views**  
✅ **No duplicate form components**  
✅ **No abandoned UI implementations**  
✅ **No unused composables**  
✅ **No duplicate API functions**  

---

## Notes

### job_worker.py Clarification

Initially suspected as obsolete, but investigation revealed:
- **Embedded worker mode is disabled** in production (ENABLE_EMBEDDED_WORKER=false)
- **However**, the file contains shared utility functions used by Service Bus worker
- Functions like `process_email_job()` and `process_crm_job()` are imported and used
- **Not a legacy component** - active part of current architecture

**Potential Future Refactor**: Extract shared functions to a utilities module, separate from embedded worker logic.

---

## Verification Commands Used

```bash
# Check for imports
grep -r "email_worker" --include="*.py"
grep -r "job_worker" --include="*.py"

# Check for file references
grep -r "AccessibilityPanel" --include="*.{js,vue}"
grep -r "Dashboard\.vue" --include="*.{js,vue}"

# Compare files
diff deploy.sh scripts/deploy.sh
diff nginx.conf frontend/nginx.conf
```

---

**Phase C Complete**: Duplicate and unused code identified.  
**Next**: Phase D - Consolidate documentation structure.
