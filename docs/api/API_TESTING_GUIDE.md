# NIWI — API Testing & Verification Guide

This guide provides QA engineers, developers, and integration partners with a comprehensive playbook for testing the NIWI REST APIs across local development, staging, and production environments.

---

## 1. Safety Rules for Production Verification

> [!CAUTION] Production Testing Precaution
> When executing tests against `https://niwi.orchvate.in`:
> 1. **Email Isolation:** Always use emails ending in `@example.com` (RFC 2606 reserved). Azure Communication Services will not deliver external emails to `@example.com`.
> 2. **Never Invoke Emergency Purge:** Do NOT call `POST /api/settings/delete-all-records` in production.
> 3. **Non-Destructive Operations:** Avoid unlinking live client submissions or modifying active client organisation names.
> 4. **Idempotency Keys:** Always provide unique `idempotency_key` UUIDs to prevent unintentional duplicate test records.

---

## 2. Environment Configuration

| Target Environment | Base URL | How to Access |
| :--- | :--- | :--- |
| **Local Container** | `http://localhost:8080/api` | Full stack running via Docker on developer workstation. |
| **Local Backend Only** | `http://127.0.0.1:8000/api` | Direct Uvicorn server in isolated virtualenv. |
| **Production** | `https://niwi.orchvate.in/api` | Live Azure cloud environment. |

---

## 3. Postman Configuration & Environment Variables

Create a Postman Environment containing:

```json
{
  "base_url": "https://niwi.orchvate.in/api",
  "admin_token": "<insert_microsoft_entra_id_token>",
  "org_token": "<insert_org_member_jwt_token>",
  "test_email": "qa.tester@example.com",
  "test_org_id": "c7d5efb5-bd5a-4883-8bb4-6a8deab1c9b8"
}
```

### Pre-request Script for Admin Endpoints
In Postman collection settings, add the following Pre-request Script:
```javascript
pm.request.headers.add({
    key: 'Authorization',
    value: 'Bearer ' + pm.environment.get('admin_token')
});
```

---

## 4. Test Suites & Verification Playbooks

### Suite A: Public Questionnaire & Scoring Flow

#### TC-SUB-001: Valid Complete Assessment Submission (Happy Path)
* **Endpoint:** `POST {{base_url}}/submit`
* **Headers:** `Content-Type: application/json`
* **Payload:**
  ```json
  {
    "name": "QA Verification Bot",
    "email": "qa_run_{{$timestamp}}@example.com",
    "company_name": "QA Automated Systems",
    "consent_given": true,
    "idempotency_key": "{{$guid}}",
    "q5": "3", "q6": "3", "q7": "3", "q8": "3", "q9": "3", "q10": "3",
    "q11": "3", "q12": "3", "q13": "3", "q14": "3", "q15": "3", "q16": "3",
    "q17": "3", "q18": "3", "q19": "3", "q20": "3", "q21": "3", "q22": "3",
    "q23": "3", "q24": "3", "q25": "3", "q26": "3", "q27": "3", "q28": "3",
    "q29": "3", "q30": "3", "q31": "3", "q32": "3", "q33": "3", "q34": "3",
    "q35": "3", "q36": "3", "q37": "3", "q38": "3", "q39": "3", "q40": "3",
    "q41": "3", "q42": "3", "q43": "3", "q44": "3"
  }
  ```
* **Assertions (Postman Test Script):**
  ```javascript
  pm.test("Status is 201 Created", () => pm.response.to.have.status(201));
  pm.test("Returns submission_id UUID", () => {
      const data = pm.response.json();
      pm.expect(data.success).to.be.true;
      pm.expect(data.submission_id).to.match(/^[0-9a-fA-F-]{36}$/);
      pm.environment.set("last_submission_id", data.submission_id);
  });
  ```

#### TC-SUB-002: In-Flight Concurrency & Idempotency Check
* **Objective:** Ensure sending the exact same payload with the identical `idempotency_key` twice returns the identical `submission_id` without creating a duplicate record in PostgreSQL.
* **Execution:** Replay `TC-SUB-001` with the same `idempotency_key`.
* **Assertion:** Status is `201` or `200`, `data.submission_id == pm.environment.get("last_submission_id")`.

#### TC-SUB-003: Negative Test — Missing Required Consent
* **Payload:** Set `"consent_given": false` or omit the field.
* **Expected Status:** `422 Unprocessable Entity` or `400 Bad Request`.

#### TC-SUB-004: Negative Test — Missing Organisation Name
* **Payload:** Set `"company_name": ""` and omit `organization_id`.
* **Expected Status:** `400 Bad Request`.
* **Expected Detail:** `"Organisation name is required."`

---

### Suite B: Authentication & Authorization Security Tests

#### TC-SEC-001: Unauthenticated Admin Request Rejected
* **Endpoint:** `GET {{base_url}}/manage/orgs`
* **Headers:** No `Authorization` header.
* **Expected Status:** `401 Unauthorized`.
* **Expected Body:** `{"detail": "Missing or invalid Authorization header"}`.

#### TC-SEC-002: Standard Admin Super-Privilege Enforcement
* **Endpoint:** `GET {{base_url}}/manage/users`
* **Headers:** `Authorization: Bearer <standard_admin_token>` (user has `role = 'admin'`).
* **Expected Status:** `403 Forbidden`.
* **Expected Body:** `{"detail": "Super admin privileges required"}`.

#### TC-SEC-003: Expired Token Rejection
* **Endpoint:** `GET {{base_url}}/submissions`
* **Headers:** `Authorization: Bearer <expired_token>`.
* **Expected Status:** `401 Unauthorized`.
* **Expected Body:** `{"detail": "Token expired"}`.

---

### Suite C: Database Connection Pool Diagnostics

#### TC-DB-001: Pool Metrics Telemetry Sanity
* **Endpoint:** `GET {{base_url}}/health/pool-metrics`
* **Expected Status:** `200 OK`.
* **Assertions:**
  ```javascript
  pm.test("Pool metrics are well-formed", () => {
      const data = pm.response.json();
      pm.expect(data.checkout_pool_errors).to.eql(0);
      pm.expect(data.in_flight_delta).to.eql(0);
      pm.expect(data.maxconn).to.eql(10);
      pm.expect(data.minconn).to.eql(2);
  });
  ```

---

## 5. Automated k6 Concurrency Benchmark Script

To run non-destructive concurrency load verification against the submission pipeline, use Grafana k6:

```bash
k6 run \
  -e BASE_URL="https://niwi.orchvate.in" \
  -e VUS=10 \
  -e DURATION="30s" \
  -e CONFIRM_PROD=true \
  Audit/tests/performance/niwi-submission-load.js
```

### Metrics Acceptance Criteria
* **HTTP Error Rate:** `< 1.0%`
* **Valid Submission Success Rate:** `100%`
* **P95 Latency:** `< 3,000 ms`
* **Pool Errors Captured:** `0`

