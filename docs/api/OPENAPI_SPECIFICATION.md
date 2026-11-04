# NIWI — OpenAPI 3.1.0 Specification & Complete Endpoint Reference

This document provides the authoritative specification for the **NIWI** application programming interfaces, formatted according to the **OpenAPI 3.1.0** standard.

Every endpoint below is cross-referenced with its Python backend handler, Pydantic validation schema, database persistence models, and Vue 3 frontend consumers.

---

## 1. Specification Metadata

* **Specification Standard:** OpenAPI 3.1.0
* **API Title:** Orchvate Audit API (NIWI)
* **API Version:** 2.1.0 (Architecture Upgrade v3.1)
* **Host / Production Gateway:** `https://niwi.orchvate.in/api`
* **Local Development Gateway:** `http://localhost:8080/api`
* **Direct Backend Server:** `http://127.0.0.1:8000/api`
* **Transport Protocols:** HTTPS (TLS 1.3 enforced in production)

---

## 2. Global Security Schemes

| Scheme Name | Type | Format / Header | Description |
| :--- | :--- | :--- | :--- |
| **`OAuth2EntraID`** | OAuth2 / Bearer | `Authorization: Bearer <idToken>` | Microsoft Entra ID (Azure AD) ID token validated against Microsoft JWKS public key set. Required for all `/api/manage/*`, `/api/settings/*`, and form modifications. |
| **`OrgMemberJWT`** | HTTP Bearer | `Authorization: Bearer <token>` | RS/HS256 JWT issued upon magic-link verification (`/api/org/verify`). Required for `/api/org/dashboard`. |
| **`PublicRateLimited`** | None | Client IP | Unauthenticated; governed by SlowAPI in-memory rate limiting (100 req/hr, 1000 req/day per IP). |

---

## 3. Exhaustive Endpoint Reference

### 3.1 Assessment & Submission Pipeline

#### 1. POST `/api/submit`
* **Summary:** Primary Audit Submission
* **Description:** Ingests completed self-assessment answers, computes pure maturity scores in-memory, writes submission and score records atomically within a short database transaction (<25ms), links to an organisation or auto-creates one, and enqueues post-submit asynchronous background jobs for report email generation and optional HubSpot CRM synchronization.
* **Authentication:** Public (Protected by SlowAPI rate limiter: 100 req/hour, 1000 req/day per IP).
* **Permissions / Roles:** None.
* **Headers:** `Content-Type: application/json`, optional `Authorization: Bearer <org_token>` (for pre-authenticated organisation members).
* **Request Body (`AuditSubmission`):**
  * `name` (string, required): Full name of respondent.
  * `company_name` (string, required): Organisation or employer name.
  * `email` (string [email], required): Corporate email address.
  * `designation` / `role` (string, optional): Job title or designation.
  * `contact_number` (string, optional): Telephone contact.
  * `has_physical_workspace` (string [Yes/No/NA], optional): Physical workspace gating flag.
  * `has_suppliers` (string [Yes/No/NA], optional): External supplier engagement gating flag.
  * `q5` to `q44` (string / int, optional): Assessment response values (e.g. '0', '1', '2', '3', 'NA').
  * `consent_given` (boolean, required): Explicit consent flag for audit data processing.
  * `idempotency_key` (string [UUID], optional): Client-generated unique UUIDv4 ensuring atomic idempotency.
  * `draft_id` (string [UUID], optional): If resuming a draft, automatically marks draft as completed.
  * `invitation_token` (string, optional): Secure invitation campaign token.
  * `organization_id` (string [UUID], optional): Explicit organisation ID.
* **Response Schema (`201 Created`):**
  ```json
  {
    "success": true,
    "submission_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
  ```
* **Error Responses:**
  * `400 Bad Request`: `{"detail": "Organisation name is required."}` or invalid invitation link.
  * `422 Unprocessable Entity`: Validation failure on input schema or malformed email.
  * `429 Too Many Requests`: `{"detail": "A submission from this email was received recently. Please wait a few minutes before submitting again."}` (5-minute email deduplication window) or SlowAPI limit exceeded.
  * `500 Internal Server Error`: `{"detail": "Database error"}`.
* **Related Models / Tables:** `submissions`, `organizations`, `organization_invitations`, `post_submit_jobs`, `draft_submissions`.
* **Frontend Consumers:** `AuditForm.vue` via `submitAudit()` in `api.js`.

#### 2. GET `/api/form/sections`
* **Summary:** Fetch Form Structure & Question Metadata
* **Description:** Returns the active assessment questionnaire schema including 8 sections, gating questions, why-it-matters metadata, and 40 ordered questions. Cached in server memory for 5 minutes (`_SECTIONS_CACHE_TTL = 300s`) with automatic invalidation on admin edits.
* **Authentication:** Public.
* **Permissions / Roles:** None.
* **Query Parameters:** None.
* **Response Schema (`200 OK` - `List[SectionResponse]`):**
  ```json
  [
    {
      "id": 1,
      "section_code": "LC",
      "title": "Leadership & Culture",
      "icon": "flag",
      "summary": "Evaluation of executive commitment...",
      "why_it_matters": "Executive alignment drives...",
      "tip": "Review your leadership charter...",
      "gating_question": null,
      "gating_field": null,
      "order_index": 1,
      "questions": [
        {
          "id": 1,
          "section_id": 1,
          "field_name": "q5",
          "short_title": "Executive Commitment",
          "question_text": "Does leadership actively support neurodiversity?",
          "order_index": 1,
          "score_mapping": {"0": 0, "1": 5, "2": 10, "3": 20},
          "depends_on_field": null,
          "depends_on_value": null
        }
      ]
    }
  ]
  ```
* **Related Models / Tables:** `form_sections`, `form_questions`.
* **Frontend Consumers:** `AuditForm.vue`, `FormBuilder.vue`, `SubmissionDetail.vue`.

#### 3. POST `/api/public/organisations/validate`
* **Summary:** Validate Organisation Name
* **Description:** Pre-assessment check to verify if a typed company name matches an existing approved client organisation or requires auto-provisioning.
* **Authentication:** Public.
* **Request Body (`ValidateOrganisationRequest`):** `{"name": "Acme Corp"}`
* **Response (`200 OK`):**
  ```json
  {
    "exists": true,
    "id": "c7d5efb5-bd5a-4883-8bb4-6a8deab1c9b8",
    "name": "Acme Corp",
    "is_active": true
  }
  ```
* **Frontend Consumers:** `AuditForm.vue` via `validateOrgName()`.

#### 4. POST `/api/public/invitations/validate`
* **Summary:** Validate Invitation Campaign Link
* **Description:** Validates an invitation token hash, returning bound organisation UUID, name, and campaign validity.
* **Authentication:** Public.
* **Request Body (`ValidateInvitationRequest`):** `{"token": "inv_abcdef123456"}`
* **Response (`200 OK`):**
  ```json
  {
    "valid": true,
    "organization_id": "c7d5efb5-bd5a-4883-8bb4-6a8deab1c9b8",
    "organization_name": "Acme Corp",
    "expires_at": "2026-12-31T23:59:59Z",
    "remaining_uses": 15
  }
  ```
* **Frontend Consumers:** `AuditForm.vue` via `validateInvitation()`.

#### 5. POST `/api/drafts/save`
* **Summary:** Save Assessment Progress
* **Description:** Persists partially completed questionnaire responses and sends a secure resume link to the respondent's email.
* **Authentication:** Public.
* **Request Body (`SaveDraftPayload`):**
  * `email` (string, required): Corporate email.
  * `company_name` (string, required): Company name.
  * `answers` (object, required): Key-value dictionary of answered fields.
  * `current_step` (int, optional): Active stepper index.
* **Response (`200 OK`):** `{"success": true, "draft_id": "uuid", "message": "Draft saved. Check your email for resume link."}`
* **Frontend Consumers:** `composables/useDraftSaving.js`.

#### 6. GET `/api/drafts/resume`
* **Summary:** Resume Assessment Progress
* **Description:** Retrieves serialized in-progress answers using an unguessable draft resume token from email.
* **Authentication:** Public.
* **Query Parameters:** `token` (string, required).
* **Response (`200 OK`):** `{"success": true, "draft_id": "uuid", "company_name": "Acme Corp", "answers": {...}, "current_step": 3}`
* **Frontend Consumers:** `ResumeDraft.vue`.

#### 7. POST `/api/book-call`
* **Summary:** Schedule Consultation Call
* **Description:** Records an advisory call booking request and triggers email notification to Orchvate specialists.
* **Authentication:** Public.
* **Request Body:** `{"name": "Jane Doe", "email": "jane@acme.com", "phone": "+44123456", "company": "Acme Corp", "preferred_date": "2026-11-15", "notes": "Interested in Level 2 roadmap."}`
* **Response (`200 OK`):** `{"success": true, "message": "Call booked successfully"}`
* **Frontend Consumers:** `BookCall.vue`.

#### 8. POST `/api/support`
* **Summary:** Submit Support Ticket
* **Description:** Forwards user inquiries, bug reports, and accessibility questions to the support mailbox.
* **Authentication:** Public.
* **Request Body:** `{"name": "John Doe", "email": "john@acme.com", "subject": "Questionnaire clarification", "message": "Could you clarify Section BE gating?"}`
* **Response (`200 OK`):** `{"success": true, "message": "Support request submitted"}`
* **Frontend Consumers:** `Support.vue`.

#### 9. GET `/api/health`
* **Summary:** Service Health Probe
* **Description:** Real-time healthcheck validating PostgreSQL connection pool and Azure Communication Services availability.
* **Response (`200 OK` or `503 Service Unavailable`):** `{"version": "2.1", "database": "up", "acs": "up"}`

#### 10. GET `/api/health/pool-metrics`
* **Summary:** Database Pool Diagnostics
* **Description:** Returns process-local `ThreadedConnectionPool` metrics for the worker process handling the request.
* **Response (`200 OK`):**
  ```json
  {
    "pid": 12,
    "minconn": 2,
    "maxconn": 10,
    "checkout_attempts": 146,
    "checkout_successes": 146,
    "checkout_pool_errors": 0,
    "checkout_other_errors": 0,
    "returns_count": 146,
    "active_connections": 0,
    "peak_connections": 1,
    "max_hold_time_ms": 4883.97,
    "avg_hold_time_ms": 575.84,
    "long_hold_count": 1,
    "in_flight_delta": 0
  }
  ```

---

### 3.2 Authentication & Identity

#### 11. GET `/api/auth/config`
* **Summary:** Fetch MSAL Configuration
* **Description:** Delivers public Azure Entra ID Client ID and Tenant ID to the frontend SPA to initialize `@azure/msal-browser`.
* **Authentication:** Public.
* **Response (`200 OK`):** `{"clientId": "2f900af5-c166-4fdb-90f1-1eaee09eeff2", "tenantId": "ea77fe37-fd2c-4294-87c3-8746bce6625a"}`
* **Frontend Consumers:** `authConfig.js`.

#### 12. POST `/api/auth/verify`
* **Summary:** Verify Administrative User Email
* **Description:** Checks if an authenticated Microsoft user email is enrolled in `admin_users` table and returns their RBAC role.
* **Authentication:** Public.
* **Request Body:** `{"email": "admin@orchvate.com"}`
* **Response (`200 OK`):** `{"authorized": true, "role": "super", "name": "Admin User"}`
* **Frontend Consumers:** `AdminLogin.vue`, `authConfig.js`.

---

### 3.3 Client Organisation Portal

#### 13. POST `/api/org/register`
* **Summary:** Request Organisation Magic Link
* **Description:** Verifies that the supplied email belongs to an existing client organisation and sends an unguessable passwordless login link.
* **Authentication:** Public.
* **Request Body (`RegisterPayload`):** `{"email": "employee@clientcompany.com"}`
* **Response (`200 OK`):** `{"success": true, "message": "Magic link sent to your corporate email."}`
* **Frontend Consumers:** `OrgLogin.vue`.

#### 14. GET `/api/org/verify`
* **Summary:** Verify Magic Link Token
* **Description:** Validates magic link cryptographic hash, exchanges it for an RS/HS256 JWT with `role: "org_member"` and `org_id`, and sets a secure cookie.
* **Authentication:** Public (Token via Query Parameter `?token=...`).
* **Response (`200 OK`):** `{"success": true, "token": "jwt_token_here", "org_id": "uuid", "org_name": "Acme Corp"}`
* **Frontend Consumers:** `OrgVerify.vue`.

#### 15. GET `/api/org/dashboard`
* **Summary:** Organisation Maturity Dashboard
* **Description:** Returns historical audit assessment records, progression trajectory, overall averages, and maturity pillar levels for the authenticated organisation.
* **Authentication:** Bearer `OrgMemberJWT`.
* **Headers:** `Authorization: Bearer <token>`
* **Response (`200 OK`):** `{"organization": {"id": "uuid", "name": "Acme Corp"}, "submissions": [...]}`
* **Frontend Consumers:** `OrgDashboard.vue`.

---

### 3.4 Admin Submission Review & Modification

#### 16. GET `/api/submissions`
* **Summary:** List Recent Submissions
* **Authentication:** Bearer `OAuth2EntraID` (`admin` or `super`).
* **Response (`200 OK`):** Array of submission records with summary scores, respondent names, and company names.
* **Frontend Consumers:** `Dashboard.vue`, `Overview.vue`, `Analytics.vue`.

#### 17. GET `/api/submissions/{submission_id}`
* **Summary:** Full Submission Detail
* **Authentication:** Bearer `OAuth2EntraID` (`admin` or `super`).
* **Path Parameters:** `submission_id` (UUID).
* **Response (`200 OK`):** Complete submission object with 40 questions, dimension scores, status, and rendered email body.
* **Frontend Consumers:** `SubmissionDetail.vue`.

#### 18. POST `/api/submissions/filter`
* **Summary:** Dynamic Multi-Column Filter Query
* **Authentication:** Bearer `OAuth2EntraID`.
* **Request Body:** `{"conditions": [...], "match_type": "AND", "page": 1, "page_size": 20}`
* **Response (`200 OK`):** `{"items": [...], "total": 45, "page": 1, "page_size": 20}`
* **Frontend Consumers:** `Submissions.vue` via `filterSubmissions()`.

#### 19. GET `/api/submissions/saved-filters`
* **Summary:** List Filter Presets
* **Authentication:** Bearer `OAuth2EntraID`.
* **Response (`200 OK`):** Array of saved filter objects.

#### 20. POST `/api/submissions/saved-filters`
* **Summary:** Save New Filter Preset
* **Authentication:** Bearer `OAuth2EntraID`.
* **Request Body:** `{"name": "Preset Name", "conditions": [...], "match_type": "AND"}`
* **Response (`201 Created`):** Saved filter object.

#### 21. DELETE `/api/submissions/saved-filters/{filter_id}`
* **Summary:** Delete Filter Preset
* **Authentication:** Bearer `OAuth2EntraID`.
* **Path Parameters:** `filter_id` (string).
* **Response (`200 OK`):** `{"success": true, "message": "Saved filter deleted"}`

#### 22. PUT `/api/submissions/{submission_id}/email`
* **Summary:** Update Stored Email Body
* **Authentication:** Bearer `OAuth2EntraID`.
* **Request Body:** `{"email_body": "Updated HTML string"}`
* **Response (`200 OK`):** `{"success": true, "message": "Email updated"}`

#### 23. POST `/api/submissions/{submission_id}/send`
* **Summary:** Dispatch Audit Results Email
* **Authentication:** Bearer `OAuth2EntraID`.
* **Response (`200 OK`):** `{"success": true, "message": "Email sent"}`

#### 24. POST `/api/submissions/{submission_id}/regenerate-email`
* **Summary:** Re-render Email Template
* **Authentication:** Bearer `OAuth2EntraID`.
* **Response (`200 OK`):** `{"success": true, "email_body": "<html>...</html>"}`

#### 25. PATCH `/api/submissions/{submission_id}/respondent`
* **Summary:** Update Respondent Contact Attributes
* **Authentication:** Bearer `OAuth2EntraID`.
* **Request Body:** `{"name": "...", "email": "...", "role": "..."}`
* **Response (`200 OK`):** `{"success": true, "message": "Respondent details updated"}`

#### 26. PATCH `/api/submissions/{submission_id}/scores`
* **Summary:** Override Assessment Pillar Scores
* **Authentication:** Bearer `OAuth2EntraID`.
* **Request Body:** `{"lc_score": 15.0, "ro_score": 12.0}`
* **Response (`200 OK`):** `{"success": true, "scores": {...}}`

#### 27. PATCH `/api/submissions/{submission_id}/organisation`
* **Summary:** Reassign Submission Organisation
* **Authentication:** Bearer `OAuth2EntraID`.
* **Request Body:** `{"organization_id": "c7d5efb5-bd5a-4883-8bb4-6a8deab1c9b8"}`
* **Response (`200 OK`):** `{"success": true, "message": "Organisation reassigned"}`

---

### 3.5 Admin Organisation Management

#### 28. GET `/api/manage/orgs`
* **Summary:** List Organisations
* **Authentication:** Bearer `OAuth2EntraID`.
* **Query Parameters:** `include_deleted` (bool).
* **Response (`200 OK`):** List of client organisations.

#### 29. POST `/api/manage/orgs` (and legacy `/api/manage/orgs/create`)
* **Summary:** Create Organisation
* **Authentication:** Bearer `OAuth2EntraID`.
* **Request Body (`CreateOrgRequest`):** `{"name": "New Org", "industry": "Finance"}`
* **Response (`201 Created`):** `{"id": "uuid", "name": "New Org", "is_active": true}`

#### 30. GET `/api/manage/orgs/unlinked`
* **Summary:** List Unlinked Submissions
* **Authentication:** Bearer `OAuth2EntraID`.
* **Response (`200 OK`):** Array of submissions with no organisation mapping.

#### 31. GET `/api/manage/orgs/{org_id}`
* **Summary:** Get Organisation Details
* **Authentication:** Bearer `OAuth2EntraID`.
* **Response (`200 OK`):** Organisation profile and linked submission statistics.

#### 32. PUT `/api/manage/orgs/{org_id}`
* **Summary:** Update Organisation Profile
* **Authentication:** Bearer `OAuth2EntraID`.
* **Request Body (`UpdateOrgRequest`):** Updated organisation fields.
* **Response (`200 OK`):** `{"success": true, "organisation": {...}}`

#### 33. DELETE `/api/manage/orgs/{org_id}`
* **Summary:** Soft-Delete Organisation
* **Authentication:** Bearer `OAuth2EntraID`.
* **Response (`200 OK`):** `{"success": true, "message": "Organisation soft-deleted"}`

#### 34. POST `/api/manage/orgs/{org_id}/restore`
* **Summary:** Restore Soft-Deleted Organisation
* **Authentication:** Bearer `OAuth2EntraID`.
* **Response (`200 OK`):** `{"success": true, "message": "Organisation restored"}`

#### 35. PATCH `/api/manage/orgs/{org_id}/status`
* **Summary:** Toggle Organisation Active Status
* **Authentication:** Bearer `OAuth2EntraID`.
* **Request Body (`OrgStatusRequest`):** `{"is_active": false}`
* **Response (`200 OK`):** `{"success": true, "is_active": false}`

#### 36. GET `/api/manage/orgs/{org_id}/report-preview`
* **Summary:** Organisation Maturity Report Rollup
* **Authentication:** Bearer `OAuth2EntraID`.
* **Response (`200 OK`):** Aggregate weighted scores across all member assessments.

#### 37. POST `/api/manage/orgs/{org_id}/message`
* **Summary:** Broadcast Message to Organisation Respondents
* **Authentication:** Bearer `OAuth2EntraID`.
* **Request Body:** `{"subject": "Notice", "body": "Message content"}`
* **Response (`200 OK`):** `{"success": true, "sent_count": 5}`

#### 38. POST `/api/manage/orgs/{org_id}/link`
* **Summary:** Bind Unlinked Submission to Organisation
* **Authentication:** Bearer `OAuth2EntraID`.
* **Request Body:** `{"submission_id": "uuid", "weight": 1.0}`
* **Response (`200 OK`):** `{"success": true, "message": "Submission linked"}`

#### 39. PUT `/api/manage/orgs/{org_id}/links/{submission_id}`
* **Summary:** Update Submission Weight
* **Authentication:** Bearer `OAuth2EntraID`.
* **Request Body:** `{"weight": 0.5}`
* **Response (`200 OK`):** `{"success": true, "weight": 0.5}`

#### 40. POST `/api/manage/orgs/{org_id}/invitations`
* **Summary:** Create Invitation Link Campaign
* **Authentication:** Bearer `OAuth2EntraID`.
* **Request Body (`CreateInvitationRequest`):** `{"label": "Q4 Staff", "expires_at": "...", "max_submissions": 50}`
* **Response (`201 Created`):** `{"id": "uuid", "token": "inv_xyz", "invite_url": "..."}`

#### 41. GET `/api/manage/orgs/{org_id}/invitations`
* **Summary:** List Organisation Invitations
* **Authentication:** Bearer `OAuth2EntraID`.
* **Response (`200 OK`):** List of invitation tokens and statistics.

#### 42. PATCH `/api/manage/orgs/invitations/{invitation_id}`
* **Summary:** Update Invitation Constraints
* **Authentication:** Bearer `OAuth2EntraID`.
* **Request Body (`UpdateInvitationRequest`):** `{"is_active": false, "max_submissions": 100}`
* **Response (`200 OK`):** `{"success": true, "invitation": {...}}`

#### 43. POST `/api/manage/orgs/invitations/{invitation_id}/revoke`
* **Summary:** Revoke Invitation Link
* **Authentication:** Bearer `OAuth2EntraID`.
* **Response (`200 OK`):** `{"success": true, "message": "Invitation revoked"}`

#### 44. POST `/api/manage/orgs/invitations/{invitation_id}/regenerate`
* **Summary:** Regenerate Invitation Token
* **Authentication:** Bearer `OAuth2EntraID`.
* **Response (`200 OK`):** `{"success": true, "token": "inv_newtoken", "invite_url": "..."}`

---

### 3.6 Admin Users & Audit Logs

#### 45. GET `/api/manage/users`
* **Summary:** List Administrative Users
* **Authentication:** Bearer `OAuth2EntraID` (`super` only).
* **Response (`200 OK`):** `[{"id": 1, "email": "admin@orchvate.com", "role": "super", "created_at": "..."}]`

#### 46. POST `/api/manage/users`
* **Summary:** Provision Admin User
* **Authentication:** Bearer `OAuth2EntraID` (`super` only).
* **Request Body:** `{"email": "newadmin@orchvate.com", "role": "admin"}`
* **Response (`201 Created`):** `{"id": 2, "email": "newadmin@orchvate.com", "role": "admin"}`

#### 47. DELETE `/api/manage/users/{email}`
* **Summary:** Deprovision Admin User
* **Authentication:** Bearer `OAuth2EntraID` (`super` only).
* **Path Parameters:** `email` (string).
* **Response (`200 OK`):** `{"success": true, "message": "User removed"}`

#### 48. GET `/api/manage/audit-logs`
* **Summary:** Query System Audit Logs
* **Authentication:** Bearer `OAuth2EntraID`.
* **Query Parameters:** `limit` (int, default: 100), `offset` (int, default: 0).
* **Response (`200 OK`):** List of immutable audit trail records.

---

### 3.7 Platform Settings

#### 49. GET `/api/settings`
* **Summary:** Fetch System Settings
* **Authentication:** Bearer `OAuth2EntraID`.
* **Response (`200 OK`):** System configuration object.

#### 50. PUT `/api/settings`
* **Summary:** Save System Settings
* **Authentication:** Bearer `OAuth2EntraID`.
* **Request Body:** Updated settings JSON.
* **Response (`200 OK`):** `{"success": true, "settings": {...}}`

#### 51. POST `/api/settings/notifications/toggle`
* **Summary:** Quick-Toggle Email Notifications
* **Authentication:** Bearer `OAuth2EntraID`.
* **Request Body:** `{"enabled": true}`
* **Response (`200 OK`):** `{"success": true, "enabled": true}`

#### 52. POST `/api/settings/delete-all-records`
* **Summary:** Emergency Data Purge
* **Authentication:** Bearer `OAuth2EntraID` (`super` only).
* **Request Body:** `{"password": "<master_secret_password>"}`
* **Response (`200 OK`):** `{"success": true, "message": "All assessment records purged"}`

---

### 3.8 Questionnaire Form Builder

#### 53. POST `/api/form/sections`
* **Summary:** Add Section
* **Authentication:** Bearer `OAuth2EntraID`.
* **Request Body (`SectionCreate`):** Section metadata.
* **Response (`201 Created`):** Created section record.

#### 54. PUT `/api/form/sections/{section_id}`
* **Summary:** Update Section
* **Authentication:** Bearer `OAuth2EntraID`.
* **Response (`200 OK`):** Updated section record.

#### 55. DELETE `/api/form/sections/{section_id}`
* **Summary:** Delete Section
* **Authentication:** Bearer `OAuth2EntraID`.
* **Response (`200 OK`):** `{"success": true, "deleted": true}`

#### 56. POST `/api/form/sections/{section_id}/questions`
* **Summary:** Add Question to Section
* **Authentication:** Bearer `OAuth2EntraID`.
* **Request Body (`QuestionCreate`):** Question definition and score mapping.
* **Response (`201 Created`):** Created question record.

#### 57. PUT `/api/form/questions/{question_id}`
* **Summary:** Update Question
* **Authentication:** Bearer `OAuth2EntraID`.
* **Response (`200 OK`):** Updated question record.

#### 58. DELETE `/api/form/questions/{question_id}`
* **Summary:** Delete Question
* **Authentication:** Bearer `OAuth2EntraID`.
* **Response (`200 OK`):** `{"success": true, "deleted": true}`

---

## 4. Complete Embedded OpenAPI 3.1.0 YAML Specification

```yaml
openapi: 3.1.0
info:
  title: Orchvate Audit API
  version: 0.1.0
paths:
  /api/drafts/save:
    post:
      tags:
      - Drafts
      summary: Save Draft
      operationId: save_draft_api_drafts_save_post
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SaveDraftPayload'
        required: true
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/drafts/resume:
    get:
      tags:
      - Drafts
      summary: Resume Draft
      operationId: resume_draft_api_drafts_resume_get
      parameters:
      - name: token
        in: query
        required: true
        schema:
          type: string
          title: Token
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/org/register:
    post:
      tags:
      - Organizations
      summary: Register Or Login Org
      operationId: register_or_login_org_api_org_register_post
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/RegisterPayload'
        required: true
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/org/verify:
    get:
      tags:
      - Organizations
      summary: Verify Magic Link
      operationId: verify_magic_link_api_org_verify_get
      parameters:
      - name: token
        in: query
        required: true
        schema:
          type: string
          title: Token
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/org/dashboard:
    get:
      tags:
      - Organizations
      summary: Get Org Dashboard
      operationId: get_org_dashboard_api_org_dashboard_get
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
  /api/manage/orgs:
    get:
      tags:
      - Org Scoring & Management
      summary: List Orgs
      operationId: list_orgs_api_manage_orgs_get
      parameters:
      - name: include_deleted
        in: query
        required: false
        schema:
          type: boolean
          default: false
          title: Include Deleted
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
    post:
      tags:
      - Org Scoring & Management
      summary: Create Org
      operationId: create_org_api_manage_orgs_post
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateOrgRequest'
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/manage/orgs/create:
    post:
      tags:
      - Org Scoring & Management
      summary: Create Org Legacy
      operationId: create_org_legacy_api_manage_orgs_create_post
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
  /api/manage/orgs/unlinked:
    get:
      tags:
      - Org Scoring & Management
      summary: List Unlinked
      operationId: list_unlinked_api_manage_orgs_unlinked_get
      parameters:
      - name: company_name
        in: query
        required: false
        schema:
          type: string
          title: Company Name
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/manage/orgs/{org_id}:
    get:
      tags:
      - Org Scoring & Management
      summary: Get Org
      operationId: get_org_api_manage_orgs__org_id__get
      parameters:
      - name: org_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
          title: Org Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
    put:
      tags:
      - Org Scoring & Management
      summary: Update Org
      operationId: update_org_api_manage_orgs__org_id__put
      parameters:
      - name: org_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
          title: Org Id
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateOrgRequest'
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
    delete:
      tags:
      - Org Scoring & Management
      summary: Delete Org
      operationId: delete_org_api_manage_orgs__org_id__delete
      parameters:
      - name: org_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
          title: Org Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/manage/orgs/{org_id}/status:
    patch:
      tags:
      - Org Scoring & Management
      summary: Toggle Org Status
      operationId: toggle_org_status_api_manage_orgs__org_id__status_patch
      parameters:
      - name: org_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
          title: Org Id
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/OrgStatusRequest'
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/manage/orgs/{org_id}/restore:
    post:
      tags:
      - Org Scoring & Management
      summary: Restore Org
      operationId: restore_org_api_manage_orgs__org_id__restore_post
      parameters:
      - name: org_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
          title: Org Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/manage/orgs/{org_id}/invitations:
    post:
      tags:
      - Org Scoring & Management
      summary: Create Invitation
      description: 'Generate a reusable invitation link with a cryptographically secure
        token (32+ bytes).

        Store only the SHA-256 hash. Return raw token only once.'
      operationId: create_invitation_api_manage_orgs__org_id__invitations_post
      parameters:
      - name: org_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
          title: Org Id
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateInvitationRequest'
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
    get:
      tags:
      - Org Scoring & Management
      summary: List Invitations
      description: List all invitations for an organisation.
      operationId: list_invitations_api_manage_orgs__org_id__invitations_get
      parameters:
      - name: org_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
          title: Org Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/manage/orgs/invitations/{invitation_id}:
    patch:
      tags:
      - Org Scoring & Management
      summary: Update Invitation
      description: Update invitation label, expiration, or maximum submissions limit.
      operationId: update_invitation_api_manage_orgs_invitations__invitation_id__patch
      parameters:
      - name: invitation_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
          title: Invitation Id
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UpdateInvitationRequest'
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/manage/orgs/invitations/{invitation_id}/revoke:
    post:
      tags:
      - Org Scoring & Management
      summary: Revoke Invitation
      description: Revoke an active invitation link immediately.
      operationId: revoke_invitation_api_manage_orgs_invitations__invitation_id__revoke_post
      parameters:
      - name: invitation_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
          title: Invitation Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/manage/orgs/invitations/{invitation_id}/regenerate:
    post:
      tags:
      - Org Scoring & Management
      summary: Regenerate Invitation
      description: 'Revoke the existing invitation and generate a fresh token with
        identical settings.

        Returns the new raw token and link.'
      operationId: regenerate_invitation_api_manage_orgs_invitations__invitation_id__regenerate_post
      parameters:
      - name: invitation_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
          title: Invitation Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/manage/orgs/{org_id}/links/{submission_id}:
    put:
      tags:
      - Org Scoring & Management
      summary: Update Link Weight
      operationId: update_link_weight_api_manage_orgs__org_id__links__submission_id__put
      parameters:
      - name: org_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
          title: Org Id
      - name: submission_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
          title: Submission Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/manage/orgs/{org_id}/link:
    post:
      tags:
      - Org Scoring & Management
      summary: Link Submission
      operationId: link_submission_api_manage_orgs__org_id__link_post
      parameters:
      - name: org_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
          title: Org Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/manage/orgs/{org_id}/report-preview:
    get:
      tags:
      - Org Scoring & Management
      summary: Org Report Preview
      operationId: org_report_preview_api_manage_orgs__org_id__report_preview_get
      parameters:
      - name: org_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
          title: Org Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/manage/orgs/{org_id}/message:
    post:
      tags:
      - Org Scoring & Management
      summary: Send Org Message
      operationId: send_org_message_api_manage_orgs__org_id__message_post
      parameters:
      - name: org_id
        in: path
        required: true
        schema:
          type: string
          format: uuid
          title: Org Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/public/organisations/validate:
    post:
      tags:
      - Public Assessment
      summary: Validate Organisation By Name
      description: 'Validates a manually entered organisation name against existing
        records.

        Returns minimal information without exposing organisation directory.

        Uses case-insensitive, whitespace-normalized matching.'
      operationId: validate_organisation_by_name_api_public_organisations_validate_post
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ValidateOrganisationRequest'
        required: true
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/public/invitations/validate:
    post:
      tags:
      - Public Assessment
      summary: Validate Invitation
      description: 'Validates an invitation token without leaking sensitive org internals.

        Derives whether the token is valid, active, non-expired, and within limits.'
      operationId: validate_invitation_api_public_invitations_validate_post
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ValidateInvitationRequest'
        required: true
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/submit:
    post:
      summary: Submit
      operationId: submit_api_submit_post
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AuditSubmission'
        required: true
      responses:
        '201':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/submissions:
    get:
      summary: Get Submissions
      operationId: get_submissions_api_submissions_get
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
  /api/submissions/filter:
    post:
      summary: Filter Submissions
      operationId: filter_submissions_api_submissions_filter_post
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
  /api/submissions/saved-filters:
    get:
      summary: List Saved Filters
      operationId: list_saved_filters_api_submissions_saved_filters_get
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
    post:
      summary: Create Saved Filter
      operationId: create_saved_filter_api_submissions_saved_filters_post
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
  /api/submissions/saved-filters/{filter_id}:
    delete:
      summary: Delete Saved Filter
      operationId: delete_saved_filter_api_submissions_saved_filters__filter_id__delete
      parameters:
      - name: filter_id
        in: path
        required: true
        schema:
          type: string
          title: Filter Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/submissions/{submission_id}:
    get:
      summary: Get Submission
      operationId: get_submission_api_submissions__submission_id__get
      parameters:
      - name: submission_id
        in: path
        required: true
        schema:
          type: string
          title: Submission Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/submissions/{submission_id}/respondent:
    patch:
      summary: Update Respondent
      operationId: update_respondent_api_submissions__submission_id__respondent_patch
      parameters:
      - name: submission_id
        in: path
        required: true
        schema:
          type: string
          title: Submission Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/submissions/{submission_id}/scores:
    patch:
      summary: Update Submission Scores
      operationId: update_submission_scores_api_submissions__submission_id__scores_patch
      parameters:
      - name: submission_id
        in: path
        required: true
        schema:
          type: string
          title: Submission Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/submissions/{submission_id}/organisation:
    patch:
      summary: Reassign Submission Organisation
      description: 'Reassign a submission to a different organisation.

        Updates both submissions.organization_id AND submissions.company_name.

        Updates org_submission_links table.

        Creates audit trail in submission_reassignments table.

        Both Normal Admin and Super Admin have global access to reassign between any
        organisations.'
      operationId: reassign_submission_organisation_api_submissions__submission_id__organisation_patch
      parameters:
      - name: submission_id
        in: path
        required: true
        schema:
          type: string
          title: Submission Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/submissions/{submission_id}/email:
    put:
      summary: Update Email
      operationId: update_email_api_submissions__submission_id__email_put
      parameters:
      - name: submission_id
        in: path
        required: true
        schema:
          type: string
          title: Submission Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/submissions/{submission_id}/regenerate-email:
    post:
      summary: Regenerate Email
      operationId: regenerate_email_api_submissions__submission_id__regenerate_email_post
      parameters:
      - name: submission_id
        in: path
        required: true
        schema:
          type: string
          title: Submission Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/submissions/{submission_id}/send:
    post:
      summary: Send Email Route
      operationId: send_email_route_api_submissions__submission_id__send_post
      parameters:
      - name: submission_id
        in: path
        required: true
        schema:
          type: string
          title: Submission Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/settings:
    get:
      summary: Get Settings Route
      operationId: get_settings_route_api_settings_get
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
    put:
      summary: Save Settings Route
      operationId: save_settings_route_api_settings_put
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
  /api/settings/notifications/toggle:
    post:
      summary: Toggle Notifications
      operationId: toggle_notifications_api_settings_notifications_toggle_post
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
  /api/book-call:
    post:
      summary: Book Call
      operationId: book_call_api_book_call_post
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
  /api/support:
    post:
      summary: Support Request
      operationId: support_request_api_support_post
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
  /api/auth/config:
    get:
      summary: Auth Config
      operationId: auth_config_api_auth_config_get
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
  /api/auth/verify:
    post:
      summary: Auth Verify
      operationId: auth_verify_api_auth_verify_post
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
  /api/manage/users:
    get:
      summary: Admin Users List
      operationId: admin_users_list_api_manage_users_get
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
    post:
      summary: Admin User Add
      operationId: admin_user_add_api_manage_users_post
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
  /api/manage/users/{email}:
    delete:
      summary: Admin User Remove
      operationId: admin_user_remove_api_manage_users__email__delete
      parameters:
      - name: email
        in: path
        required: true
        schema:
          type: string
          title: Email
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/settings/delete-all-records:
    post:
      summary: Delete All Records
      description: 'Deletes all submissions from the database.

        Strictly Super Admin only. Requires explicit confirmation text ''DELETE ALL
        SUBMISSIONS''.

        Normal Admin receives HTTP 403 Forbidden.

        Unauthenticated caller receives HTTP 401 Unauthorized.'
      operationId: delete_all_records_api_settings_delete_all_records_post
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
  /api/manage/audit-logs:
    get:
      summary: Get Audit Logs
      operationId: get_audit_logs_api_manage_audit_logs_get
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
  /api/form/sections:
    get:
      summary: Get All Sections
      operationId: get_all_sections_api_form_sections_get
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                items:
                  $ref: '#/components/schemas/SectionResponse'
                type: array
                title: Response Get All Sections Api Form Sections Get
    post:
      summary: Create Section
      operationId: create_section_api_form_sections_post
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SectionCreate'
        required: true
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SectionResponse'
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/form/sections/{section_id}:
    put:
      summary: Update Section
      operationId: update_section_api_form_sections__section_id__put
      parameters:
      - name: section_id
        in: path
        required: true
        schema:
          type: integer
          title: Section Id
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SectionCreate'
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SectionResponse'
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
    delete:
      summary: Delete Section
      operationId: delete_section_api_form_sections__section_id__delete
      parameters:
      - name: section_id
        in: path
        required: true
        schema:
          type: integer
          title: Section Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/form/sections/{section_id}/questions:
    post:
      summary: Create Question
      operationId: create_question_api_form_sections__section_id__questions_post
      parameters:
      - name: section_id
        in: path
        required: true
        schema:
          type: integer
          title: Section Id
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/QuestionCreate'
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/QuestionResponse'
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/form/questions/{question_id}:
    put:
      summary: Update Question
      operationId: update_question_api_form_questions__question_id__put
      parameters:
      - name: question_id
        in: path
        required: true
        schema:
          type: integer
          title: Question Id
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/QuestionCreate'
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/QuestionResponse'
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
    delete:
      summary: Delete Question
      operationId: delete_question_api_form_questions__question_id__delete
      parameters:
      - name: question_id
        in: path
        required: true
        schema:
          type: integer
          title: Question Id
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
        '422':
          description: Validation Error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HTTPValidationError'
  /api/health:
    get:
      summary: Health
      description: ACA health probe endpoint.
      operationId: health_api_health_get
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
  /api/health/pool-metrics:
    get:
      summary: Health Pool Metrics
      description: Diagnostic endpoint to inspect worker-local connection pool metrics.
      operationId: health_pool_metrics_api_health_pool_metrics_get
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema: {}
components:
  schemas:
    AuditSubmission:
      properties:
        name:
          anyOf:
          - type: string
            maxLength: 255
          - type: 'null'
          title: Name
        designation:
          anyOf:
          - type: string
            maxLength: 255
          - type: 'null'
          title: Designation
        company_name:
          anyOf:
          - type: string
            maxLength: 255
          - type: 'null'
          title: Company Name
        organization_id:
          anyOf:
          - type: string
          - type: 'null'
          title: Organization Id
        invitation_token:
          anyOf:
          - type: string
          - type: 'null'
          title: Invitation Token
        email:
          type: string
          format: email
          title: Email
        contact_number:
          anyOf:
          - type: string
            maxLength: 50
          - type: 'null'
          title: Contact Number
        consent_given:
          anyOf:
          - type: boolean
          - type: 'null'
          title: Consent Given
          default: false
        draft_id:
          anyOf:
          - type: string
          - type: 'null'
          title: Draft Id
        idempotency_key:
          anyOf:
          - type: string
            maxLength: 64
          - type: 'null'
          title: Idempotency Key
        function:
          anyOf:
          - type: string
          - type: 'null'
          title: Function
        function_other:
          anyOf:
          - type: string
          - type: 'null'
          title: Function Other
        role:
          anyOf:
          - type: string
          - type: 'null'
          title: Role
        country:
          anyOf:
          - type: string
          - type: 'null'
          title: Country
        state_ut:
          anyOf:
          - type: string
          - type: 'null'
          title: State Ut
        gender:
          anyOf:
          - type: string
          - type: 'null'
          title: Gender
        gender_other:
          anyOf:
          - type: string
          - type: 'null'
          title: Gender Other
        is_pwd:
          anyOf:
          - type: string
          - type: 'null'
          title: Is Pwd
        is_neurodivergent:
          anyOf:
          - type: string
          - type: 'null'
          title: Is Neurodivergent
        is_marginalized:
          anyOf:
          - type: string
          - type: 'null'
          title: Is Marginalized
        has_physical_workspace:
          anyOf:
          - type: string
            pattern: ^(Yes|No|)$
          - type: 'null'
          title: Has Physical Workspace
        has_suppliers:
          anyOf:
          - type: string
            pattern: ^(Yes|No|)$
          - type: 'null'
          title: Has Suppliers
      additionalProperties: true
      type: object
      required:
      - email
      title: AuditSubmission
    CreateInvitationRequest:
      properties:
        invitation_name:
          anyOf:
          - type: string
            maxLength: 255
          - type: 'null'
          title: Invitation Name
        expires_at:
          anyOf:
          - type: string
            format: date-time
          - type: 'null'
          title: Expires At
        max_submissions:
          anyOf:
          - type: integer
            minimum: 1.0
          - type: 'null'
          title: Max Submissions
      type: object
      title: CreateInvitationRequest
    CreateOrgRequest:
      properties:
        name:
          type: string
          maxLength: 255
          minLength: 1
          title: Name
      type: object
      required:
      - name
      title: CreateOrgRequest
    HTTPValidationError:
      properties:
        detail:
          items:
            $ref: '#/components/schemas/ValidationError'
          type: array
          title: Detail
      type: object
      title: HTTPValidationError
    OrgStatusRequest:
      properties:
        is_active:
          type: boolean
          title: Is Active
      type: object
      required:
      - is_active
      title: OrgStatusRequest
    QuestionCreate:
      properties:
        field_name:
          type: string
          title: Field Name
        short_title:
          type: string
          title: Short Title
        question_text:
          type: string
          title: Question Text
        order_index:
          type: integer
          title: Order Index
          default: 0
        depends_on_field:
          anyOf:
          - type: string
          - type: 'null'
          title: Depends On Field
        depends_on_value:
          anyOf:
          - type: string
          - type: 'null'
          title: Depends On Value
        score_mapping:
          additionalProperties:
            type: integer
          type: object
          title: Score Mapping
      type: object
      required:
      - field_name
      - short_title
      - question_text
      title: QuestionCreate
    QuestionResponse:
      properties:
        field_name:
          type: string
          title: Field Name
        short_title:
          type: string
          title: Short Title
        question_text:
          type: string
          title: Question Text
        order_index:
          type: integer
          title: Order Index
          default: 0
        depends_on_field:
          anyOf:
          - type: string
          - type: 'null'
          title: Depends On Field
        depends_on_value:
          anyOf:
          - type: string
          - type: 'null'
          title: Depends On Value
        score_mapping:
          additionalProperties:
            type: integer
          type: object
          title: Score Mapping
        id:
          type: integer
          title: Id
        section_id:
          type: integer
          title: Section Id
      type: object
      required:
      - field_name
      - short_title
      - question_text
      - id
      - section_id
      title: QuestionResponse
    RegisterPayload:
      properties:
        email:
          type: string
          format: email
          title: Email
        company_name:
          type: string
          title: Company Name
      type: object
      required:
      - email
      - company_name
      title: RegisterPayload
    SaveDraftPayload:
      properties:
        draft_id:
          anyOf:
          - type: string
            format: uuid
          - type: 'null'
          title: Draft Id
        email:
          type: string
          format: email
          title: Email
        company_name:
          type: string
          title: Company Name
        form_state:
          additionalProperties: true
          type: object
          title: Form State
        current_step:
          type: integer
          title: Current Step
      type: object
      required:
      - email
      - company_name
      - form_state
      - current_step
      title: SaveDraftPayload
    SectionCreate:
      properties:
        section_code:
          type: string
          title: Section Code
        title:
          type: string
          title: Title
        icon:
          anyOf:
          - type: string
          - type: 'null'
          title: Icon
        summary:
          anyOf:
          - type: string
          - type: 'null'
          title: Summary
        why_it_matters:
          anyOf:
          - type: string
          - type: 'null'
          title: Why It Matters
        tip:
          anyOf:
          - type: string
          - type: 'null'
          title: Tip
        gating_question:
          anyOf:
          - type: string
          - type: 'null'
          title: Gating Question
        gating_field:
          anyOf:
          - type: string
          - type: 'null'
          title: Gating Field
        order_index:
          type: integer
          title: Order Index
          default: 0
      type: object
      required:
      - section_code
      - title
      title: SectionCreate
    SectionResponse:
      properties:
        section_code:
          type: string
          title: Section Code
        title:
          type: string
          title: Title
        icon:
          anyOf:
          - type: string
          - type: 'null'
          title: Icon
        summary:
          anyOf:
          - type: string
          - type: 'null'
          title: Summary
        why_it_matters:
          anyOf:
          - type: string
          - type: 'null'
          title: Why It Matters
        tip:
          anyOf:
          - type: string
          - type: 'null'
          title: Tip
        gating_question:
          anyOf:
          - type: string
          - type: 'null'
          title: Gating Question
        gating_field:
          anyOf:
          - type: string
          - type: 'null'
          title: Gating Field
        order_index:
          type: integer
          title: Order Index
          default: 0
        id:
          type: integer
          title: Id
        questions:
          items:
            $ref: '#/components/schemas/QuestionResponse'
          type: array
          title: Questions
          default: []
      type: object
      required:
      - section_code
      - title
      - id
      title: SectionResponse
    UpdateInvitationRequest:
      properties:
        invitation_name:
          anyOf:
          - type: string
            maxLength: 255
          - type: 'null'
          title: Invitation Name
        expires_at:
          anyOf:
          - type: string
            format: date-time
          - type: 'null'
          title: Expires At
        max_submissions:
          anyOf:
          - type: integer
            minimum: 1.0
          - type: 'null'
          title: Max Submissions
      type: object
      title: UpdateInvitationRequest
    UpdateOrgRequest:
      properties:
        name:
          type: string
          maxLength: 255
          minLength: 1
          title: Name
      type: object
      required:
      - name
      title: UpdateOrgRequest
    ValidateInvitationRequest:
      properties:
        token:
          type: string
          minLength: 1
          title: Token
      type: object
      required:
      - token
      title: ValidateInvitationRequest
    ValidateOrganisationRequest:
      properties:
        name:
          type: string
          maxLength: 255
          minLength: 1
          title: Name
      type: object
      required:
      - name
      title: ValidateOrganisationRequest
    ValidationError:
      properties:
        loc:
          items:
            anyOf:
            - type: string
            - type: integer
          type: array
          title: Location
        msg:
          type: string
          title: Message
        type:
          type: string
          title: Error Type
      type: object
      required:
      - loc
      - msg
      - type
      title: ValidationError
  securitySchemes:
    OAuth2EntraID:
      type: oauth2
      description: Microsoft Entra ID (Azure AD) OAuth 2.0 Bearer Token with dynamic
        JWKS validation.
      flows:
        implicit:
          authorizationUrl: https://login.microsoftonline.com/common/oauth2/v2.0/authorize
          scopes:
            openid: OpenID identity token
            profile: User profile information
            email: User email address
    OrgMemberJWT:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: Organisation member token issued upon magic-link verification (/api/org/verify).

```
