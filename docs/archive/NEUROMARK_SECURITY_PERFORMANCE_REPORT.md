# NeuroMark (Orchvate audit) — Comprehensive security, reliability, and performance assessment

> **Title:** NeuroMark Security, Reliability, and Performance Assessment  
> **Version:** 1.0  
> **Last Updated:** May 2026  
> **Author:** Senior Security & Performance Architecture Team  
> **Status:** Final Review  

---

## Table of contents

1. [Security vulnerabilities](#1-security-vulnerabilities)
   - 1.1. [Frontend and input vulnerabilities](#11-frontend-and-input-vulnerabilities)
   - 1.2. [Backend and database vulnerabilities](#12-backend-and-database-vulnerabilities)
   - 1.3. [Authentication and authorization gaps](#13-authentication-and-authorization-gaps)
   - 1.4. [Infrastructure and dependency risks](#14-infrastructure-and-dependency-risks)
2. [Bugs and logic errors](#2-bugs-and-logic-errors)
   - 2.1. [Application logic and edge cases](#21-application-logic-and-edge-cases)
   - 2.2. [Concurrency and state management](#22-concurrency-and-state-management)
   - 2.3. [User interface and dashboard defects](#23-user-interface-and-dashboard-defects)
3. [Performance bottlenecks](#3-performance-bottlenecks)
   - 3.1. [Compute and scaling bottlenecks](#31-compute-and-scaling-bottlenecks)
   - 3.2. [Database and data access bottlenecks](#32-database-and-data-access-bottlenecks)
   - 3.3. [Frontend and rendering bottlenecks](#33-frontend-and-rendering-bottlenecks)
4. [Reliability and resilience issues](#4-reliability-and-resilience-issues)
   - 4.1. [Fault tolerance and recovery](#41-fault-tolerance-and-recovery)
   - 4.2. [Monitoring and visibility](#42-monitoring-and-visibility)
5. [Compliance and privacy risks](#5-compliance-and-privacy-risks)
   - 5.1. [Data governance and privacy](#51-data-governance-and-privacy)
   - 5.2. [Auditing and access control](#52-auditing-and-access-control)
6. [Next steps and conclusion](#6-next-steps-and-conclusion)
7. [Appendix: Glossary](#7-appendix-glossary)
8. [Revision history](#8-revision-history)

---

## 1. Security vulnerabilities

The NeuroMark application processes sensitive organizational metrics, rendering it a high-value target for malicious actors. This section evaluates systemic security flaws spanning the Vue 3 frontend, the FastAPI backend, and the Azure infrastructure. Addressing these vulnerabilities is critical to preventing unauthorized data access, privilege escalation, and service disruption.

### 1.1. Frontend and input vulnerabilities

Client-side vulnerabilities occur when the application implicitly trusts user input or fails to secure local execution environments. These flaws provide entry points for deeper systemic attacks.

#### Input validation and sanitization issues on the audit form

**Description:** The Vue 3 frontend form lacks strict type-checking, and the Python backend accepts payloads without rigorous schema validation. Malicious actors can send excessively large payloads, unexpected data types, or malformed JSON objects to the `/api/submit` endpoint. 

**Why it matters:** Relying solely on client-side validation allows attackers to bypass the user interface using tools like Postman or curl. Processing unvalidated payloads on the server leads to memory exhaustion (Denial of Service), application crashes, or database truncation errors if input strings exceed column limits.

**Severity:** High  
**Impact:** Application downtime, potential database corruption, and service disruption.  

**Recommended fix:** Enforce strict dual-layer validation. Implement schema validation on the frontend using libraries like `Vuelidate`, and mandate strict structural validation on the backend utilizing FastAPI's `Pydantic` models.

```python
from pydantic import BaseModel, EmailStr, constr

class AuditSubmission(BaseModel):
    name: constr(max_length=255, strip_whitespace=True)
    company_name: constr(max_length=255, strip_whitespace=True)
    email: EmailStr
    q5: constr(regex='^(Yes|Partially|No|Not Sure)$')
    # All 40 questions must enforce exact allowable string literals
```

#### Cross-site scripting (XSS) risks in the Vue frontend

**Description:** The administrative dashboard displays user-submitted text strings, such as the company name. If the application renders these strings using the `v-html` directive instead of standard interpolation, executable script tags injected by the respondent will execute within the administrator's browser context.

**Why it matters:** XSS vulnerabilities allow attackers to hijack authenticated administrative sessions. An injected script can silently harvest authentication tokens or execute unauthorized administrative API calls on behalf of the victim.

**Severity:** High  
**Impact:** Complete administrative account takeover and subsequent data breaches.  

**Recommended fix:** Strictly avoid utilizing the `v-html` directive for rendering user-supplied content. Vue's default double mustache syntax `{{ }}` automatically HTML-encodes output, neutralizing executable scripts.

```html
<!-- VULNERABLE IMPLEMENTATION -->
<div v-html="submission.company_name"></div>

<!-- SECURE IMPLEMENTATION -->
<div>{{ submission.company_name }}</div>
```

### 1.2. Backend and database vulnerabilities

Backend vulnerabilities expose the core logic and data storage mechanisms of the application. Exploitation at this layer typically results in catastrophic data loss or systemic compromise.

#### SQL injection risks in PostgreSQL queries

**Description:** Dynamic string concatenation used to construct SQL queries permits attackers to embed malicious SQL commands within form input fields. 

**Why it matters:** Relational databases execute concatenated strings as literal commands. Without proper sanitization, an attacker can terminate the intended query and append destructive commands, bypassing all application logic.

**Severity:** Critical  
**Impact:** Absolute database compromise, facilitating data exfiltration, modification, or deletion (e.g., dropping the `admin_users` table).  

**Recommended fix:** Eliminate dynamic string formatting in database queries. Utilize parameterized queries provided by `psycopg2` or implement an object-relational mapper (ORM) like `SQLAlchemy`.

```python
# VULNERABLE IMPLEMENTATION
# Allows input like: "'; DROP TABLE submissions; --"
cursor.execute(f"INSERT INTO submissions (name) VALUES ('{payload.name}')")

# SECURE IMPLEMENTATION
# The database driver safely escapes the input parameter
cursor.execute("INSERT INTO submissions (name) VALUES (%s)", (payload.name,))
```

#### Insecure direct object references (IDOR)

**Description:** The application utilizes sequential integer IDs for accessing submission details via the `/api/submissions/{id}` endpoint.

**Why it matters:** Predictable resource identifiers allow authenticated users, or unauthenticated actors if authorization is bypassed, to enumerate and access resources belonging to other organizations simply by incrementing the ID parameter in the URL.

**Severity:** High  
**Impact:** Horizontal privilege escalation leading to unauthorized disclosure of sensitive audit data belonging to external organizations.  

**Recommended fix:** Enforce strict authorization checks confirming the requester owns the requested resource. Transition from sequential integers to universally unique identifiers (UUIDv4) to eliminate predictability.

```sql
-- Database schema update for UUID primary keys
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
ALTER TABLE submissions ADD COLUMN uuid_id UUID DEFAULT uuid_generate_v4();
```

#### Data at rest and in transit encryption gaps

**Description:** Sensitive organizational metrics and administrator credentials transit over unencrypted HTTP connections and reside unencrypted on physical storage volumes.

**Why it matters:** Unencrypted transit enables man-in-the-middle (MITM) attacks, allowing network eavesdroppers to intercept payloads. Unencrypted storage exposes the database to theft if underlying infrastructure or backups are compromised.

**Severity:** High  
**Impact:** Total exposure of transmitted credentials and stored organizational data.  

**Recommended fix:** Enforce HTTP Strict Transport Security (HSTS) headers across all environments. Require SSL connections for the PostgreSQL database via the `sslmode=require` connection parameter. Enable Transparent Data Encryption (TDE) on the Azure PostgreSQL instance.

### 1.3. Authentication and authorization gaps

Flaws in the authentication mechanisms allow unauthorized entities to bypass identity verification, granting access to restricted administrative functionalities.

#### API authentication enforcement failures

**Description:** Administrative endpoints lack strict enforcement of Microsoft Entra ID token validation. Missing, expired, or forged tokens might bypass authorization checks if the middleware fails open.

**Why it matters:** Identity verification is the primary defense against unauthorized access. If an endpoint assumes a request is legitimate without cryptographically verifying the token, any user can execute administrative commands.

**Severity:** Critical  
**Impact:** Unauthorized actors can view all audit data, modify system configurations, and trigger arbitrary email dispatches.  

**Recommended fix:** Implement robust FastAPI dependencies that intercept all requests to `/api/admin/*`, verifying the JWT signature against Microsoft's public JSON Web Key Set (JWKS), checking the `aud` (audience), `iss` (issuer), and `exp` (expiration) claims.

#### Cross-site request forgery (CSRF) protection gaps

**Description:** If the application relies on cookie-based session management without explicit `SameSite` attributes, external malicious websites can force an authenticated administrator's browser to execute state-changing requests against the NeuroMark API.

**Why it matters:** Browsers automatically attach cookies to cross-origin requests unless explicitly instructed otherwise. This allows an attacker to manipulate the application state without requiring the victim's credentials.

**Severity:** Medium  
**Impact:** Unauthorized configuration modifications or data deletion executed silently via an authenticated administrator's browser.  

**Recommended fix:** Ensure all session and authentication cookies enforce `SameSite=Lax` or `Strict` attributes.

#### JWT token storage vulnerabilities

**Description:** Storing Entra ID JSON Web Tokens (JWT) in the browser's `localStorage` exposes them to client-side scripts. 

**Why it matters:** Any successful XSS attack will immediately extract tokens from `localStorage`, allowing the attacker to impersonate the administrator indefinitely across different devices.

**Severity:** High  
**Impact:** Administrative account takeover and persistent unauthorized access.  

**Recommended fix:** Transition token storage from `localStorage` to `HttpOnly`, `Secure` cookies. This configuration prevents client-side JavaScript from accessing the token material.

### 1.4. Infrastructure and dependency risks

Vulnerabilities inherent in the deployment environment and third-party libraries compromise the foundational security of the application.

#### Secrets and environment variable exposure

**Description:** Hardcoding sensitive configuration values, such as the `DATABASE_URL` or `ACS_CONNECTION_STRING`, directly in the source code or exposing `.env` files in production environments.

**Why it matters:** Exposed credentials provide attackers with direct, unfettered access to external services and databases, bypassing all application-layer security controls.

**Severity:** Critical  
**Impact:** Complete infrastructure compromise, data exfiltration, and financial exploitation of Azure resources.  

**Recommended fix:** Exclusively utilize Azure Key Vault for managing and injecting secrets at runtime. Ensure `.env` files are strictly excluded via `.gitignore`. 

#### Email injection attacks via Azure Communication Services

**Description:** The application constructs outgoing email reports by directly concatenating user-supplied strings, such as the company name, into the HTML email body.

**Why it matters:** Attackers can inject malicious HTML, links, or entirely forged content into the email body. Because the email originates from the legitimate NeuroMark domain, it circumvents standard spam filters, making it a highly effective phishing vector.

**Severity:** High  
**Impact:** Reputational damage and facilitation of secondary phishing campaigns using the trusted organizational domain.  

**Recommended fix:** Utilize a secure templating engine, such as `Jinja2`, configured with automatic context-aware escaping. Never manually concatenate user strings into email HTML structures.

> [!NOTE]
> **Section 1 Summary**
> - **Input validation:** Strictly enforce data schemas at both the frontend and backend boundaries.
> - **Query parameterization:** Eradicate string concatenation in SQL queries to prevent injection attacks.
> - **Authentication verification:** Cryptographically validate all Entra ID tokens on every administrative request.
> - **Secure storage:** Transition from `localStorage` to `HttpOnly` cookies and utilize Azure Key Vault for all infrastructure secrets.

---

## 2. Bugs and logic errors

Software defects and flawed business logic disrupt user workflows, corrupt data integrity, and diminish the overall reliability of the assessment platform.

### 2.1. Application logic and edge cases

Flaws in the core processing algorithms lead to unexpected application states and calculation failures.

#### Scoring engine calculation failures

**Description:** The weighting algorithm expects a specific set of string responses. If the frontend permits skipping a question, or if an unexpected value bypasses validation, the backend dictionary mapping will raise a `KeyError`.

**Why it matters:** Unhandled exceptions during the scoring calculation abort the entire transaction. The user receives a generic 500 Internal Server Error, and the audit submission is lost.

**Severity:** Medium  
**Impact:** Disrupted user experience and lost assessment data.  

**Recommended fix:** Mandate all 40 questions as strictly required on the frontend. Implement default fallback values in the backend dictionary mapping to prevent fatal errors during calculation.

```python
# VULNERABLE
score = mapping_dict[payload.q5]

# SECURE
score = mapping_dict.get(payload.q5, 0) # Fallback to 0 if unexpected input occurs
```

#### Radar chart generation boundary errors

**Description:** The application relies on the QuickChart API for visual rendering. If an organization scores exactly `0` across an entire dimension, or if the resulting URI string exceeds maximum URL length limitations, the chart image fails to render.

**Why it matters:** Broken visual assets within the finalized email report severely undermine the professional credibility of the platform.

**Severity:** Low  
**Impact:** Degraded visual presentation in client-facing deliverables.  

**Recommended fix:** Implement fallback logic to handle zero-value dimensions gracefully. Transition from `GET` requests with massive URL parameters to parameterized `POST` requests when interacting with the QuickChart API.

### 2.2. Concurrency and state management

Issues arising from simultaneous operations and temporary state persistence degrade data integrity and user experience.

#### Race conditions in concurrent submissions

**Description:** Simultaneous submissions processed by the backend may encounter race conditions if the route handlers utilize shared global state or unsynchronized variables for score calculation.

**Why it matters:** Shared state in a concurrent environment leads to cross-contamination. One organization's score might be incorrectly applied to another organization's submission, invalidating the entire assessment.

**Severity:** Medium  
**Impact:** Corrupted diagnostic data and inaccurate client reporting.  

**Recommended fix:** Guarantee that all FastAPI route handlers remain strictly stateless. Isolate all score calculation variables within the local function scope to ensure thread safety.

#### Form state loss in the Vue application

**Description:** The assessment spans 45 questions. If a respondent inadvertently clicks the browser's back button or refreshes the page, the Vue component unmounts, resulting in the immediate loss of all inputted data.

**Why it matters:** The assessment requires significant time and cognitive effort to complete. Data loss frustrates users, leading to high abandonment rates and incomplete assessments.

**Severity:** Medium  
**Impact:** Reduced completion rates and severe user frustration.  

**Recommended fix:** Persist the form state to the browser's `localStorage` incrementally using Vue's `watch` mechanism. Clear the local storage cache exclusively upon a confirmed successful submission.

#### Duplicate submission handling

**Description:** The application lacks a mechanism to prevent multiple submissions if a user rapidly double-clicks the submission button before the network request resolves.

**Why it matters:** Duplicate requests create redundant database entries, artificially inflating analytic metrics and triggering duplicate email dispatches.

**Severity:** Low  
**Impact:** Minor data bloat and redundant processing overhead.  

**Recommended fix:** Disable the submit button and display a loading indicator immediately upon the initial click event. Implement idempotency keys on the backend to reject duplicate payloads.

### 2.3. User interface and dashboard defects

Errors in the administrative interface hinder operational efficiency and data management.

#### Pagination and filtering oversights

**Description:** The administrative dashboard attempts to retrieve and render the entire `submissions` table in a single request. 

**Why it matters:** As the database grows to thousands of records, transferring and rendering the entire dataset will exhaust browser memory, freeze the user interface, and place unnecessary load on the backend database.

**Severity:** Medium  
**Impact:** The administrative dashboard becomes inoperable at scale.  

**Recommended fix:** Implement server-side pagination utilizing SQL `LIMIT` and `OFFSET` clauses. Shift search filtering logic from client-side array manipulation to optimized database queries.

#### Timezone handling discrepancies

**Description:** The system stamps submissions using the database's local `NOW()` function. If the server operates in UTC but the dashboard parses the timestamp blindly as local time, display values will misalign with reality.

**Why it matters:** Inaccurate timestamp rendering causes operational confusion, particularly when tracking submission SLAs or investigating technical issues.

**Severity:** Low  
**Impact:** Administrative confusion regarding event chronologies.  

**Recommended fix:** Standardize all database timestamps to UTC using `TIMESTAMP WITH TIME ZONE`. Utilize JavaScript libraries like `date-fns` to format dates into the administrator's local timezone at the presentation layer.

> [!NOTE]
> **Section 2 Summary**
> - **Calculation safety:** Implement fallback values for all scoring dictionaries to prevent fatal application crashes.
> - **State persistence:** Utilize `localStorage` to save form progress incrementally, preventing data loss on accidental navigation.
> - **Data scaling:** Implement server-side pagination to ensure the administrative dashboard remains performant as the dataset expands.
> - **Stateless processing:** Ensure backend calculations avoid global variables to prevent cross-contamination during concurrent requests.

---

## 3. Performance bottlenecks

Architectural inefficiencies restrict the application's ability to handle high traffic volumes and deliver responsive user experiences. Identifying and resolving these constraints is vital for system scalability.

### 3.1. Compute and scaling bottlenecks

Constraints associated with the serverless hosting environment and payload processing.

#### Azure Functions cold start latency

**Description:** Serverless architectures, such as Azure Container Apps scaling to zero, terminate instances during idle periods. The initial request triggering a new instance incurs a significant "cold start" delay.

**Why it matters:** The boot sequence requires initializing the container, loading the Python runtime, and establishing database connections. This process introduces 5 to 10 seconds of latency, causing users to perceive the application as unresponsive or broken.

**Severity:** High  
**Impact:** Severe degradation of the user experience during initial interactions, leading to form abandonment.  

**Recommended fix:** Configure the Azure Container App environment with a minimum replica count of `1`. Alternatively, deploy a lightweight synthetic ping mechanism executed via a CRON job every 4 minutes to prevent instance termination.

#### Synchronous versus asynchronous I/O operations

**Description:** The FastAPI backend utilizes the synchronous `psycopg2` driver within asynchronous (`async def`) route handlers.

**Why it matters:** Executing synchronous blocking operations inside an asynchronous event loop halts all concurrent processing. The application can only handle one database query at a time, severely restricting throughput.

**Severity:** High  
**Impact:** Systemic performance degradation and potential request timeouts under moderate concurrent load.  

**Recommended fix:** Transition the database layer to an asynchronous driver such as `asyncpg`, or explicitly offload synchronous database calls to a separate thread pool using FastAPI's `run_in_threadpool`.

### 3.2. Database and data access bottlenecks

Inefficiencies in how the application queries and retrieves data from the persistent storage layer.

#### Database connection pooling exhaustion

**Description:** Under heavy traffic, the serverless environment rapidly spins up multiple concurrent instances. Each instance establishes its own direct connection to the PostgreSQL database.

**Why it matters:** PostgreSQL possesses strict limits on concurrent connections. Rapid scaling exhausts the connection limit, resulting in `FATAL: sorry, too many clients already` errors and cascading application failure.

**Severity:** High  
**Impact:** Complete application outage during traffic spikes.  

**Recommended fix:** Implement a centralized connection pooler such as `PgBouncer`. Azure Database for PostgreSQL provides built-in PgBouncer functionality which must be explicitly enabled to multiplex connections efficiently.

#### Suboptimal query execution on large datasets

**Description:** The administrative dashboard search functionality utilizes basic `ILIKE '%query%'` wildcard matching across text columns.

**Why it matters:** Leading wildcards in SQL queries bypass standard B-Tree indexes, forcing the database engine to execute a sequential full table scan. Performance degrades linearly as the table grows.

**Severity:** Medium  
**Impact:** Sluggish search functionality and unnecessary CPU consumption on the database server.  

**Recommended fix:** Implement trigram indexes (`pg_trgm`) specifically designed to optimize arbitrary text search queries within PostgreSQL.

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_company_name_trgm ON submissions USING gin (company_name gin_trgm_ops);
```

### 3.3. Frontend and rendering bottlenecks

Constraints affecting the client-side delivery and rendering of the application interface.

#### Vue 3 bundle size and initial load delays

**Description:** Importing entire component frameworks and icon libraries without tree-shaking yields a monolithic JavaScript payload exceeding optimal sizes.

**Why it matters:** Large payloads extend download times and block the main execution thread during parsing. This disproportionately affects users on constrained mobile networks, delaying the Time to Interactive (TTI) metric.

**Severity:** Medium  
**Impact:** Slower page load speeds and decreased accessibility for users on mobile devices.  

**Recommended fix:** Utilize Vite's bundle analyzer to identify bloated dependencies. Implement route-level code splitting to defer loading administrative components until strictly necessary.

```typescript
// SECURE LAZY LOADING IMPLEMENTATION
const AdminDashboard = () => import('./views/AdminDashboard.vue');
```

#### DOM rendering performance on data grids

**Description:** The dashboard attempts to render thousands of distinct Document Object Model (DOM) nodes simultaneously when viewing large datasets.

**Why it matters:** The browser must calculate layout and paint operations for every rendered node. Rendering extensive non-virtualized lists monopolizes the UI thread, resulting in janky scrolling and interface unresponsiveness.

**Severity:** Medium  
**Impact:** Frustrating user experience for administrators navigating large datasets.  

**Recommended fix:** Implement virtual scrolling using a library such as `vue-virtual-scroller`. This technique selectively renders only the DOM nodes currently visible within the user's viewport, drastically reducing layout computation costs.

> [!NOTE]
> **Section 3 Summary**
> - **Eliminate cold starts:** Maintain a minimum instance count of one to bypass severe serverless boot latencies.
> - **Asynchronous processing:** Transition to asynchronous database drivers to unblock the FastAPI event loop.
> - **Connection multiplexing:** Enable PgBouncer to prevent database connection exhaustion during scale-out events.
> - **Code splitting:** Implement lazy loading in the Vue router to minimize the initial payload size for end users.

---

## 4. Reliability and resilience issues

Resilience mechanisms ensure the system recovers gracefully from internal faults and external service disruptions. The current architecture lacks critical fallback procedures.

### 4.1. Fault tolerance and recovery

Mechanisms required to handle transient failures and prevent data loss.

#### Lack of retry logic on email dispatch

**Description:** The application relies on Azure Communication Services (ACS) to dispatch reports. The implementation executes a single synchronous network request without retry mechanisms.

**Why it matters:** External APIs experience transient network instability or temporary service degradation (e.g., HTTP 503 errors). A single failed attempt means the respondent never receives their finalized audit report.

**Severity:** Medium  
**Impact:** Failed deliverability and a degraded user experience.  

**Recommended fix:** Implement exponential backoff and retry logic using robust libraries like `Tenacity`. Decouple the email dispatch from the synchronous web request using asynchronous background tasks.

```python
from tenacity import retry, wait_exponential, stop_after_attempt

@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
def dispatch_email_report(payload):
    # Execute ACS API call
    pass
```

#### Absence of a dead letter queue (DLQ)

**Description:** Background tasks, such as generating the radar chart or dispatching notifications, execute silently. If a task crashes due to an unhandled exception, it fails without alerting the development team.

**Why it matters:** Silent failures complicate debugging efforts and obscure systemic issues. Data drops out of the pipeline without leaving an audit trail.

**Severity:** High  
**Impact:** Unnoticed task failures and lost administrative notifications.  

**Recommended fix:** Implement a dedicated task queue system, such as Celery or Azure Service Bus. Configure failed tasks to route automatically to a Dead Letter Queue for manual inspection and eventual replay.

#### Database backup and recovery omissions

**Description:** The architectural documentation does not define a formal backup strategy, point-in-time recovery (PITR) configuration, or disaster recovery plan for the PostgreSQL instance.

**Why it matters:** Accidental data truncation, malicious data destruction, or catastrophic regional infrastructure failures will result in the permanent loss of all organizational audit data.

**Severity:** Critical  
**Impact:** Total and irreversible data loss.  

**Recommended fix:** Enable automated daily backups within the Azure portal. Configure Geo-Redundant storage for backups to survive regional outages, and verify Point-in-Time Restore capabilities.

### 4.2. Monitoring and visibility

Systems required to track application health and trigger automated remediation.

#### Missing health check telemetry

**Description:** The FastAPI application does not expose a dedicated `/health` endpoint to verify the operational status of internal components, such as the database connection or external API availability.

**Why it matters:** The Azure Container Apps orchestrator relies on liveness and readiness probes to manage container lifecycles. Without an endpoint, the orchestrator cannot detect application deadlocks or automatically restart hanging containers.

**Severity:** Low  
**Impact:** Prolonged downtime during silent application crashes.  

**Recommended fix:** Expose a lightweight `/health` endpoint that quickly verifies database connectivity. Configure Azure to poll this endpoint and restart the container if it returns a non-200 status code.

> [!NOTE]
> **Section 4 Summary**
> - **Implement retries:** Use exponential backoff to handle transient failures when interacting with external APIs like ACS.
> - **Establish task queues:** Route failed background tasks to a Dead Letter Queue to prevent silent data loss.
> - **Automate backups:** Configure Geo-Redundant backups and verify Point-in-Time Restore functionality for the PostgreSQL database.
> - **Enable telemetry:** Create a `/health` endpoint to allow Azure orchestrators to automatically recover deadlocked containers.

---

## 5. Compliance and privacy risks

Handling organizational demographics and qualitative performance data requires adherence to strict privacy regulations and data governance principles.

### 5.1. Data governance and privacy

Policies defining how data is collected, stored, and eventually destroyed.

#### GDPR and CCPA consent deficiencies

**Description:** The application collects personally identifiable information (PII), including names, email addresses, and phone numbers, without requiring explicit user consent via a dedicated checkbox.

**Why it matters:** Processing PII without explicit, documented consent violates major international privacy frameworks, including the General Data Protection Regulation (GDPR) and the California Consumer Privacy Act (CCPA).

**Severity:** High  
**Impact:** Significant regulatory fines and organizational legal liability.  

**Recommended fix:** Implement a mandatory consent checkbox on the demographic collection screen ("I consent to the processing of my data in accordance with the Privacy Policy"). Record the exact timestamp of this consent alongside the submission record in the database.

#### Indefinite data retention practices

**Description:** The system lacks an automated mechanism to purge or anonymize historical audit records, resulting in indefinite data storage.

**Why it matters:** Storing sensitive qualitative data in perpetuity violates the core privacy principle of data minimization. It unnecessarily inflates the impact radius of any potential future data breach.

**Severity:** Medium  
**Impact:** Increased legal liability and non-compliance with data retention regulations.  

**Recommended fix:** Establish a formal data retention policy. Implement a scheduled CRON job to automatically anonymize or hard-delete submission records exceeding a three-year retention threshold.

### 5.2. Auditing and access control

Mechanisms tracking internal administrative behavior and restricting internal data access.

#### Unrestricted internal data visibility

**Description:** The Role-Based Access Control (RBAC) model grants all authorized Orchvate administrators global visibility into every submitted organizational audit.

**Why it matters:** Providing global read access violates the principle of least privilege. An auditor assigned to Client A possesses unnecessary access to the highly sensitive performance metrics of Client B, potentially violating Non-Disclosure Agreements (NDAs).

**Severity:** Medium  
**Impact:** Internal privacy breaches and violation of client confidentiality agreements.  

**Recommended fix:** Implement Row-Level Security (RLS) within the PostgreSQL database or adjust the application logic to associate specific submissions directly with assigned account manager IDs, restricting visibility accordingly.

#### Absence of administrative audit logs

**Description:** Super Administrators possess the ability to alter global platform settings, and Administrators can modify generated email reports. However, the system does not log the identity of the user executing these modifications or the timestamp of the event.

**Why it matters:** Without an immutable audit trail, tracking down accidental misconfigurations, identifying compromised internal accounts, or investigating malicious internal activity is impossible.

**Severity:** Medium  
**Impact:** Lack of accountability and inability to perform forensic investigations post-incident.  

**Recommended fix:** Construct a dedicated `audit_logs` table. Instrument the application layer to record the `admin_id`, `action_type`, `target_resource_id`, and `timestamp` for every state-changing administrative operation.

> [!NOTE]
> **Section 5 Summary**
> - **Enforce explicit consent:** Require and log explicit user consent before processing any personally identifiable information.
> - **Implement data minimization:** Deploy automated routines to purge historical audit records exceeding the defined retention period.
> - **Restrict internal visibility:** Transition from global administrative access to siloed, assignment-based data visibility.
> - **Track administrative actions:** Implement comprehensive audit logging for all state-changing actions performed within the administrative dashboard.

---

## 6. Next steps and conclusion

This assessment reveals that while the NeuroMark application possesses a modern architectural foundation, significant vulnerabilities exist across its security posture, performance characteristics, and compliance frameworks. 

**Immediate Priorities:**
1.  **Remediate SQL Injection:** Immediately transition all database interactions to parameterized queries.
2.  **Enforce API Authentication:** Deploy robust JWT validation middleware across all administrative endpoints.
3.  **Implement Connection Pooling:** Enable PgBouncer to prevent database exhaustion under load.

Addressing these high-severity findings is mandatory before the application clears the final production readiness review. Subsequent iterations should focus on the medium-severity resilience and scalability recommendations detailed within this document.

---

## 7. Appendix: Glossary

*   **ACS:** Azure Communication Services. Microsoft's cloud-based email and communication delivery platform.
*   **CSRF:** Cross-Site Request Forgery. An attack forcing an end user to execute unwanted actions on a web application in which they are currently authenticated.
*   **Dead Letter Queue (DLQ):** A secondary queue utilized to isolate messages or tasks that failed processing for manual inspection.
*   **Entra ID:** Microsoft's cloud-based identity and access management service (formerly Azure Active Directory).
*   **IDOR:** Insecure Direct Object Reference. An access control vulnerability where an application provides direct access to objects based on user-supplied input.
*   **JWKS:** JSON Web Key Set. A set of keys containing the public keys used to verify any JSON Web Token (JWT) issued by the authorization server.
*   **MITM:** Man-in-the-Middle. An attack where the perpetrator positions themselves in a conversation between a user and an application to eavesdrop or impersonate one of the parties.
*   **ORM:** Object-Relational Mapping. A programming technique for converting data between incompatible type systems using object-oriented programming languages.
*   **PgBouncer:** A lightweight connection pooler for PostgreSQL designed to reduce the overhead of opening and closing database connections.
*   **TTI:** Time to Interactive. A performance metric measuring how long it takes a page to become fully interactive.
*   **UUIDv4:** Universally Unique Identifier version 4. A 128-bit number generated randomly, minimizing the probability of duplication or predictability.
*   **XSS:** Cross-Site Scripting. A vulnerability allowing attackers to inject malicious client-side scripts into web pages viewed by other users.

---

## 8. Revision history

| Version | Date | Author | Description of Changes |
| :--- | :--- | :--- | :--- |
| **0.9** | May 2026 | Architecture Team | Initial draft and discovery phase |
| **1.0** | May 2026 | Architecture Team | Formalized publication with comprehensive vulnerability enumeration and remediation code snippets |

---
*Report generated and finalized by the Advanced Performance and Security Architecture Team.*
