# NIWI — API Request & Response Practical Examples

This document provides production-verified **cURL commands**, JSON request bodies, success responses, and expected error structures for the primary API workflows implemented across the NIWI platform.

---

## 1. Assessment & Submission Pipeline

### 1.1 Complete Self-Assessment Submission
Submits a complete respondent questionnaire with atomic idempotency and consent.

#### cURL
```bash
curl -X POST "https://niwi.orchvate.in/api/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alex Mercer",
    "email": "alex.mercer@innovatetech.com",
    "company_name": "Innovate Tech Ltd",
    "designation": "VP People & Culture",
    "contact_number": "+44 20 7946 0912",
    "has_physical_workspace": "Yes",
    "has_suppliers": "Yes",
    "consent_given": true,
    "idempotency_key": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "q5": "3", "q6": "2", "q7": "3", "q8": "2", "q9": "3", "q10": "1",
    "q11": "2", "q12": "2", "q13": "3", "q14": "1", "q15": "2", "q16": "2",
    "q17": "3", "q18": "2", "q19": "2", "q20": "3", "q21": "2", "q22": "1",
    "q23": "2", "q24": "2", "q25": "3", "q26": "2", "q27": "1", "q28": "2",
    "q29": "2", "q30": "3", "q31": "2", "q32": "1", "q33": "2", "q34": "2",
    "q35": "3", "q36": "2", "q37": "2", "q38": "1", "q39": "2", "q40": "3",
    "q41": "2", "q42": "2", "q43": "3", "q44": "2"
  }'
```

#### Success Response (`201 Created`)
```json
{
  "success": true,
  "submission_id": "c1f7b093-6c8a-4467-b5b6-7c93817f9382"
}
```

#### Duplicate Submission Within 5 Minutes (`429 Too Many Requests`)
```json
{
  "detail": "A submission from this email was received recently. Please wait a few minutes before submitting again."
}
```

---

### 1.2 Fetch Dynamic Form Sections & Questions
Retrieves the 8 assessment pillars and their configured questions from server memory.

#### cURL
```bash
curl -X GET "https://niwi.orchvate.in/api/form/sections" \
  -H "Accept: application/json"
```

#### Success Response (`200 OK`)
```json
[
  {
    "id": 1,
    "section_code": "LC",
    "title": "Leadership & Culture",
    "icon": "flag",
    "summary": "Assessing neuroinclusion commitment at executive levels.",
    "why_it_matters": "Leadership sets the tone and psychological safety of the entire workplace.",
    "tip": "Review published diversity charters and board minutes.",
    "gating_question": null,
    "gating_field": null,
    "order_index": 1,
    "questions": [
      {
        "id": 1,
        "section_id": 1,
        "field_name": "q5",
        "short_title": "Executive Commitment",
        "question_text": "Is there visible executive sponsorship for neuroinclusion initiatives?",
        "order_index": 1,
        "score_mapping": {
          "0": 0,
          "1": 5,
          "2": 10,
          "3": 20
        },
        "depends_on_field": null,
        "depends_on_value": null
      }
    ]
  }
]
```

---

### 1.3 Save Assessment In-Progress Draft
Saves partial survey progress and generates an email resume token.

#### cURL
```bash
curl -X POST "https://niwi.orchvate.in/api/drafts/save" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "sarah.connor@cyberdyne.com",
    "company_name": "Cyberdyne Systems",
    "current_step": 3,
    "answers": {
      "name": "Sarah Connor",
      "designation": "Director of Security",
      "q5": "3",
      "q6": "2",
      "q7": "3"
    }
  }'
```

#### Success Response (`200 OK`)
```json
{
  "success": true,
  "draft_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "message": "Draft saved. A resume link has been dispatched to your email."
}
```

---

### 1.4 Resume In-Progress Draft
Retrieves stored answers using the token received in email.

#### cURL
```bash
curl -X GET "https://niwi.orchvate.in/api/drafts/resume?token=dft_8f3a9e217c4b05d8" \
  -H "Accept: application/json"
```

#### Success Response (`200 OK`)
```json
{
  "success": true,
  "draft_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "company_name": "Cyberdyne Systems",
  "current_step": 3,
  "answers": {
    "name": "Sarah Connor",
    "designation": "Director of Security",
    "q5": "3",
    "q6": "2",
    "q7": "3"
  }
}
```

---

## 2. Admin Submission Review & Modification

### 2.1 Dynamic ServiceNow-Style Submissions Filter
Performs advanced multi-column filtering with sort order and pagination.

#### cURL
```bash
curl -X POST "https://niwi.orchvate.in/api/submissions/filter" \
  -H "Authorization: Bearer <microsoft_id_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "conditions": [
      {
        "field": "overall_level",
        "operator": "equals",
        "value": "Level 2 — Early Progress"
      },
      {
        "field": "company_name",
        "operator": "contains",
        "value": "Innovate"
      }
    ],
    "match_type": "AND",
    "sort_by": "submitted_at",
    "sort_order": "desc",
    "page": 1,
    "page_size": 10
  }'
```

#### Success Response (`200 OK`)
```json
{
  "items": [
    {
      "id": "c1f7b093-6c8a-4467-b5b6-7c93817f9382",
      "name": "Alex Mercer",
      "company_name": "Innovate Tech Ltd",
      "email": "alex.mercer@innovatetech.com",
      "submitted_at": "2026-11-03T20:15:30Z",
      "overall_avg": 13.75,
      "overall_level": "Level 2 — Early Progress",
      "status": "pending",
      "organization_name": "Innovate Tech Ltd"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

---

### 2.2 Override Assessment Pillar Scores
Updates score values and automatically recomputes the weighted overall level.

#### cURL
```bash
curl -X PATCH "https://niwi.orchvate.in/api/submissions/c1f7b093-6c8a-4467-b5b6-7c93817f9382/scores" \
  -H "Authorization: Bearer <microsoft_id_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "lc_score": 18.0,
    "ro_score": 15.0,
    "we_score": 16.5
  }'
```

#### Success Response (`200 OK`)
```json
{
  "success": true,
  "message": "Submission scores updated successfully",
  "scores": {
    "lc_score": 18.0,
    "lc_level": "Level 3 — Developing",
    "ro_score": 15.0,
    "ro_level": "Level 3 — Developing",
    "we_score": 16.5,
    "we_level": "Level 3 — Developing",
    "overall_avg": 16.5,
    "overall_level": "Level 3 — Developing"
  }
}
```

#### Validation Error (`400 Bad Request`)
```json
{
  "detail": "Score lc_score must be between 0 and 20"
}
```

---

### 2.3 Dispatch Assessment Report Email
Triggers the formal executive findings dispatch via Azure Communication Services.

#### cURL
```bash
curl -X POST "https://niwi.orchvate.in/api/submissions/c1f7b093-6c8a-4467-b5b6-7c93817f9382/send" \
  -H "Authorization: Bearer <microsoft_id_token>"
```

#### Success Response (`200 OK`)
```json
{
  "success": true,
  "message": "Email sent"
}
```

#### Conflict If Already Sent (`409 Conflict`)
```json
{
  "detail": "Already sent or sending"
}
```

---

## 3. Organisation Management & Link Weighting

### 3.1 Create Client Organisation
Provisions a new corporate client entity.

#### cURL
```bash
curl -X POST "https://niwi.orchvate.in/api/manage/orgs" \
  -H "Authorization: Bearer <microsoft_id_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Global Logistics Corp",
    "industry": "Transportation",
    "employee_count": 2500,
    "notes": "Contract signed Q4 2026. Target 50 assessments across depots."
  }'
```

#### Success Response (`201 Created`)
```json
{
  "id": "e2b3c4d5-e6f7-8901-abcd-ef2345678901",
  "name": "Global Logistics Corp",
  "industry": "Transportation",
  "employee_count": 2500,
  "is_active": true,
  "is_deleted": false,
  "approval_status": "approved",
  "created_at": "2026-11-04T02:00:00Z"
}
```

---

### 3.2 Create Audit Campaign Invitation Link
Generates an unguessable invitation token with submission cap and expiration.

#### cURL
```bash
curl -X POST "https://niwi.orchvate.in/api/manage/orgs/e2b3c4d5-e6f7-8901-abcd-ef2345678901/invitations" \
  -H "Authorization: Bearer <microsoft_id_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "label": "UK Warehouses Autumn Audit",
    "expires_at": "2026-12-15T23:59:59Z",
    "max_submissions": 50
  }'
```

#### Success Response (`201 Created`)
```json
{
  "id": "a9b8c7d6-e5f4-3210-fedc-ba9876543210",
  "organization_id": "e2b3c4d5-e6f7-8901-abcd-ef2345678901",
  "token": "inv_7d8e9f0a1b2c3d4e",
  "label": "UK Warehouses Autumn Audit",
  "invite_url": "https://niwi.orchvate.in/audit?token=inv_7d8e9f0a1b2c3d4e",
  "max_submissions": 50,
  "submission_count": 0,
  "is_active": true,
  "expires_at": "2026-12-15T23:59:59Z",
  "created_at": "2026-11-04T02:15:00Z"
}
```

---

### 3.3 Link Unbound Submission to Organisation with Weight
Associates an ad-hoc survey response with a formal client organisation with a custom weight.

#### cURL
```bash
curl -X POST "https://niwi.orchvate.in/api/manage/orgs/e2b3c4d5-e6f7-8901-abcd-ef2345678901/link" \
  -H "Authorization: Bearer <microsoft_id_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "submission_id": "c1f7b093-6c8a-4467-b5b6-7c93817f9382",
    "weight": 0.75
  }'
```

#### Success Response (`200 OK`)
```json
{
  "success": true,
  "message": "Submission linked successfully",
  "link": {
    "organization_id": "e2b3c4d5-e6f7-8901-abcd-ef2345678901",
    "submission_id": "c1f7b093-6c8a-4467-b5b6-7c93817f9382",
    "weight": 0.75
  }
}
```

---

## 4. User Provisioning (Super Admin Only)

### 4.1 Provision Administrator Access
Grants an internal user access to the admin dashboard.

#### cURL
```bash
curl -X POST "https://niwi.orchvate.in/api/manage/users" \
  -H "Authorization: Bearer <super_admin_id_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "lead.auditor@orchvate.com",
    "role": "admin"
  }'
```

#### Success Response (`201 Created`)
```json
{
  "id": 5,
  "email": "lead.auditor@orchvate.com",
  "role": "admin",
  "created_at": "2026-11-04T03:00:00Z"
}
```

#### Authorization Failure When Run as Regular Admin (`403 Forbidden`)
```json
{
  "detail": "Super admin privileges required"
}
```

---

## 5. System Health & Pool Diagnostics

### 5.1 Query Real-Time Database Connection Pool Metrics
Inspects connection checkouts, hold times, and leak invariants per Uvicorn worker.

#### cURL
```bash
curl -X GET "https://niwi.orchvate.in/api/health/pool-metrics" \
  -H "Accept: application/json"
```

#### Success Response (`200 OK`)
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

