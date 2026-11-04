# NIWI — Phase 1 Codebase Cleanup Plan

**Date**: November 4, 2026  
**Branch**: `maintenance/niwi-codebase-cleanup`  
**Original Commit**: `57a4e92e4ba0b52acbe18e6b428400c24707ba2f`

---

## Executive Summary

Based on the comprehensive architecture audit, this document outlines the specific cleanup actions to establish a clean, maintainable NIWI codebase. The cleanup is organized by priority and risk level.

**Total Files Scanned**: 500+ (excluding node_modules, .venv)  
**Documentation Files**: 120+ markdown files  
**Performance Reports**: 100+ JSON/MD pairs  
**Primary Focus**: Documentation consolidation, obsolete file removal, git hygiene

---

## Priority 1: Low-Risk, High-Impact Cleanup (IMMEDIATE)

### 1.1 Documentation Consolidation

**Problem**: 120+ markdown files scattered across multiple locations with significant duplication

**Actions**:
1. Create organized `docs/` structure
2. Move all historical `NIWI_*_REPORT.md` files to `docs/archive/historical-reports/`
3. Consolidate API documentation (remove duplicates)
4. Update root README to be concise project entry point
5. Create `DOCUMENTATION_INDEX.md` as navigation aid

**Risk Level**: ⬤⬤⬤⬤⬤ MINIMAL (moving files, not deleting)

**Files to Move** (15 root-level reports):
```
NIWI_IMPLEMENTATION_REPORT.md → docs/archive/historical-reports/
NIWI_SERVICE_BUS_IMPLEMENTATION_REPORT.md → docs/archive/historical-reports/
NIWI_CURRENT_ARCHITECTURE_AUDIT.md → docs/archive/historical-reports/
NIWI_PRE_IMPLEMENTATION_AUDIT.md → docs/archive/historical-reports/
NIWI_POST_DEPLOYMENT_VERIFICATION.md → docs/archive/historical-reports/
NIWI_INDEPENDENT_PRODUCTION_VERIFICATION_REPORT.md → docs/archive/historical-reports/
NIWI_FINAL_RELIABILITY_AUDIT.md → docs/archive/historical-reports/
NIWI_TESTING_AND_PERFORMANCE_REPORT.md → docs/archive/historical-reports/
NIWI_PERFORMANCE_REMEDIATION_PLAN.md → docs/archive/historical-reports/
NIWI_DATABASE_OPTIMISATION_REPORT.md → docs/archive/historical-reports/
NIWI_AZURE_SERVICE_BUS_ARCHITECTURE.md → docs/architecture/
NIWI_SERVICE_BUS_TEST_REPORT.md → docs/archive/historical-reports/
NIWI_SERVICE_BUS_DEPLOYMENT_AND_ROLLBACK.md → docs/operations/
NIWI_DEPLOYMENT_AND_ROLLBACK_GUIDE.md → docs/operations/
upgrade_v3_1 (1).md → docs/archive/upgrades/
```

### 1.2 Git Hygiene

**Problem**: Build artifacts and virtual environments tracked or untracked inconsistently

**Actions**:
1. Add `.venv311/` to `.gitignore`
2. Add `.pytest_cache/` to `.gitignore`
3. Remove tracked `.pytest_cache/README.md`
4. Add temporary Vite config files pattern to `.gitignore`
5. Clean up untracked performance reports

**Risk Level**: ⬤⬤⬤⬤⬤ MINIMAL (git hygiene)

**.gitignore additions needed**:
```
# Python virtual environments
.venv/
.venv311/
venv/
env/

# Pytest cache
.pytest_cache/
__pycache__/

# Vite temporary files
*.timestamp-*.mjs

# Performance test reports (keep in tests/performance/reports/ but exclude from commits)
tests/performance/reports/*.json
tests/performance/reports/*.md
```

### 1.3 Remove Temporary Build Artifacts

**Problem**: Vite timestamp files committed to repository

**Actions**:
Delete 3 temporary Vite config files:
```
frontend/vite.config.js.timestamp-1779387089083-be3c91a5bbfb9.mjs
frontend/vite.config.js.timestamp-1780637751362-8e361798d73b5.mjs
frontend/vite.config.js.timestamp-1781760518532-d84da34639227.mjs
```

**Risk Level**: ⬤⬤⬤⬤⬤ MINIMAL (generated files)

---

## Priority 2: Medium-Risk Obsolete File Removal (VERIFY FIRST)

### 2.1 Obsolete Job Worker

**File**: `app/tasks/job_worker.py`

**Status**: Superseded by Azure Service Bus architecture

**Verification Required**:
1. Confirm `ENABLE_EMBEDDED_WORKER=false` in all environments
2. Verify no direct imports of `job_worker` in active code
3. Confirm Service Bus worker is handling all background jobs

**Risk Level**: ⬤⬤⬤⬤⬤ LOW (if verified unused)

**Action**: Remove after verification

### 2.2 Duplicate Scripts

**File**: Root `deploy.sh` (duplicate of `scripts/deploy.sh`)

**Verification Required**:
1. Check if CI/CD references root `deploy.sh`
2. Check if any documentation references root version
3. Verify `scripts/deploy.sh` is identical or superset

**Risk Level**: ⬤⬤⬤⬤⬤ LOW

**Action**: Remove root version, keep `scripts/deploy.sh`

### 2.3 Superseded SQL Scripts

**Files**:
```
sql/create_table.sql (superseded by migrations)
sql/install_all.sql (superseded by migrate.py)
sql/fix_missing_columns.sql (one-time fix, likely already applied)
```

**Verification Required**:
1. Confirm migrations 002-019 cover all schema requirements
2. Verify `fix_missing_columns.sql` was applied historically
3. Check if `install_all.sql` is referenced anywhere

**Risk Level**: ⬤⬤⬤⬤⬤ MEDIUM (database-related)

**Action**: Move to `sql/archive/` rather than delete

### 2.4 Obsolete Nginx Configuration

**File**: Root `nginx.conf` (possibly superseded by `frontend/nginx.conf`)

**Verification Required**:
1. Confirm Docker only uses `frontend/nginx.conf`
2. Check if any deployment process uses root `nginx.conf`
3. Verify they are not complementary configurations

**Risk Level**: ⬤⬤⬤⬤⬤ MEDIUM (infrastructure)

**Action**: Archive if confirmed unused

---

## Priority 3: Performance Report Archival (RECOMMENDED)

### 3.1 Archive Historical Performance Reports

**Problem**: 100+ JSON/MD report pairs in `tests/performance/reports/`

**Strategy**: Keep most recent baseline for each VU level, archive rest

**Recommended Retention**:
- Keep: Most recent report for VU levels: 10, 20, 40, 60, 80, 100
- Archive: All other reports to `tests/performance/reports/archive/`

**Risk Level**: ⬤⬤⬤⬤⬤ MINIMAL (test artifacts)

**Space Savings**: ~5-10 MB

---

## Priority 4: Untracked File Assessment (NEEDS REVIEW)

### 4.1 Untracked Python Scripts

**Files**:
```
create_siwi_org.py
create_siwi_orgs.py
generate_audit_tokens.py
```

**Questions**:
1. What is SIWI? (Different from NIWI?)
2. Are these one-time data seeding scripts?
3. Should they be tracked or added to .gitignore?

**Risk Level**: ⬤⬤⬤⬤⬤ UNKNOWN

**Action**: NEEDS_MANUAL_REVIEW - User input required

### 4.2 Untracked Performance Test Scripts

**Files**:
```
tests/performance/run-workflow-tests.ps1
tests/performance/run-manual-workflow-tests.ps1
tests/performance/run-token-workflow-tests.ps1
tests/performance/audit_tokens.txt
```

**Questions**:
1. Should these be tracked for documentation?
2. Is `audit_tokens.txt` sensitive data?

**Risk Level**: ⬤⬤⬤⬤⬤ LOW

**Action**: NEEDS_MANUAL_REVIEW - Likely track scripts, gitignore tokens

---

## Priority 5: Component Review (REQUIRES INVESTIGATION)

### 5.1 Frontend Components Archive

**Location**: `frontend/src/components/archive/`

**Action Required**: List contents and verify nothing is imported

**Risk Level**: ⬤⬤⬤⬤⬤ LOW (already archived by developers)

### 5.2 Potential Duplicate View

**File**: `frontend/src/views/Dashboard.vue`

**Question**: Is this a duplicate of `Overview.vue`?

**Verification**: Check if imported anywhere in router or other views

**Risk Level**: ⬤⬤⬤⬤⬤ LOW

---

## Priority 6: Documentation Consolidation Details

### 6.1 Proposed Documentation Structure

```
docs/
├── README.md                          # Documentation index (NEW)
│
├── architecture/
│   ├── README.md                      # Architecture overview
│   ├── SYSTEM_ARCHITECTURE.md         # Consolidated system architecture
│   ├── BACKEND_ARCHITECTURE.md        # Backend deep dive
│   ├── FRONTEND_ARCHITECTURE.md       # Frontend deep dive
│   ├── DATABASE_ARCHITECTURE.md       # Database and migrations
│   └── SERVICE_BUS_ARCHITECTURE.md    # (Move from root NIWI_AZURE_SERVICE_BUS_ARCHITECTURE.md)
│
├── api/
│   ├── README.md                      # API documentation index
│   ├── API_REFERENCE.md               # Consolidated API reference
│   ├── AUTHENTICATION.md              # Auth documentation
│   ├── ERROR_CODES.md                 # Error reference
│   └── EXAMPLES.md                    # Request/response examples
│   # (Consolidate from 9 current api/ files)
│
├── operations/
│   ├── DEPLOYMENT.md                  # Consolidated deployment guide
│   ├── MONITORING.md                  # Monitoring and troubleshooting
│   └── SERVICE_BUS_DEPLOYMENT.md      # Service Bus deployment specifics
│
├── product/
│   # Keep docs/product-audit/ structure as-is (comprehensive and current)
│   └── (No changes)
│
├── testing/
│   ├── TESTING_STRATEGY.md            # Test approach and coverage
│   └── PERFORMANCE_TESTING.md         # Performance test guide
│
├── calculations/
│   └── FORMULA_LOGIC.md               # (From product-audit/06_FORMULA_AND_CALCULATION_LOGIC.md)
│
└── archive/
    ├── historical-reports/            # All NIWI_*_REPORT.md files
    ├── upgrades/                      # Upgrade documentation
    └── legacy/                        # Existing archive/ contents
```

### 6.2 Files to Consolidate

**Root README.md Changes**:
- Keep current comprehensive documentation
- Add clear navigation to docs/ sections
- Remove redundant sections already in docs/product-audit/

**docs/API.md vs docs/api/ folder**:
- Consolidate `docs/API.md` into `docs/api/API_REFERENCE.md`
- Keep `docs/api/` as authoritative source

**Duplicate Technical Documentation**:
- `docs/NEUROMARK_TECHNICAL_DOCUMENTATION.md` (duplicate of archive version)
- Action: Remove, keep only archive version

---

## Execution Plan

### Phase 1: Safe Immediate Actions (No Risk)
1. Create documentation structure
2. Move historical reports to archive
3. Update .gitignore
4. Delete Vite timestamp files
5. Git commit: "docs: reorganize documentation structure"

### Phase 2: Verification and Assessment
1. Verify job_worker.py usage
2. Check deploy.sh references
3. Assess untracked files with user
4. Review frontend/components/archive/
5. Verify nginx.conf usage

### Phase 3: Verified Removals
1. Remove confirmed obsolete files
2. Archive superseded SQL scripts
3. Archive old performance reports
4. Git commit: "chore: remove obsolete files and archive superseded scripts"

### Phase 4: Documentation Consolidation
1. Consolidate API documentation
2. Create architecture documentation
3. Update root README
4. Create docs/README.md index
5. Git commit: "docs: consolidate and organize documentation"

### Phase 5: Validation
1. Run backend tests (pytest)
2. Run frontend build (npm run build)
3. Verify Docker build succeeds
4. Check CI/CD pipeline configuration
5. Compare before/after file counts

---

## Success Criteria

- [ ] All historical reports moved to organized archive
- [ ] Documentation reduced from 120+ files to ~40 authoritative files
- [ ] No production-critical files deleted
- [ ] All tests pass (93 backend tests)
- [ ] Frontend builds successfully
- [ ] Docker build succeeds
- [ ] Git repository is clean (no unnecessary artifacts)
- [ ] Clear documentation navigation established

---

## Rollback Plan

**Branch**: All changes on `maintenance/niwi-codebase-cleanup`  
**Original Commit**: `57a4e92e4ba0b52acbe18e6b428400c24707ba2f`

**To Rollback**:
```bash
git checkout main
git branch -D maintenance/niwi-codebase-cleanup
```

**To Cherry-pick specific cleanup commits**:
```bash
git cherry-pick <commit-hash>
```

---

## Next Actions

1. Present this plan to user for approval
2. Get user input on untracked files (SIWI scripts, performance test scripts)
3. Execute Phase 1 (safe immediate actions)
4. Create file inventory spreadsheet
5. Proceed with verified cleanup phases

---

**Estimated Cleanup Impact**:
- Documentation files: 120+ → ~40 (66% reduction)
- Performance reports: 100+ → ~12 (88% reduction)
- Obsolete code files: 3-5 removals
- Git hygiene: 5+ .gitignore additions
- Overall repository clarity: Significant improvement
