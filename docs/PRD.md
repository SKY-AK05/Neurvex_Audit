# Product Requirements Document (PRD) — NIWI Platform

> **In plain words:**  
> This document explains what the Neuro-Inclusive Workplace Index (NIWI) platform is, why it was created, who uses it, and how it measures inclusion in the workplace. It serves business executives, HR leaders, and engineers by defining exactly what the product does and how each feature is built.
>
> **Last updated:** November 5, 2026  
> **Document Status:** Active Canonical Specification  
> **Target System:** NIWI (commercially branded as NeuroMark) | **Operator:** Orchvate  

---

## Table of Contents
1. [In Plain Words](#in-plain-words)
2. [The Problem](#the-problem)
3. [The Solution](#the-solution)
4. [Why It Exists (Vision & Purpose)](#why-it-exists-vision--purpose)
5. [Target Users and Personas](#target-users-and-personas)
6. [User Stories](#user-stories)
7. [Features & System Capabilities](#features--system-capabilities)
8. [How a Typical Session Works](#how-a-typical-session-works)
9. [Scope: Goals and Non-Goals](#scope-goals-and-non-goals)
10. [Success Metrics](#success-metrics)
11. [Assumptions, Constraints and Known Limitations](#assumptions-constraints-and-known-limitations)
12. [Risks and Mitigations](#risks-and-mitigations)
13. [Roadmap & Planned Evolutions](#roadmap--planned-evolutions)
14. [Glossary](#glossary)

---

## 1. In Plain Words

Imagine trying to improve your health without a thermometer, blood test, or scale; you might try random diets and guess whether they help. For years, companies have done the exact same thing with neurodiversity (supporting people with ADHD, Autism, Dyslexia, and other neurological differences). They held workshops and published blog posts, but had no objective way to measure whether their hiring, office environments, or management practices actually welcomed neurodivergent employees.

NIWI is the digital "medical checkup" for company inclusion. It gives organizations a clear, confidential 40-question survey across 8 vital workplace areas, mathematically calculates their inclusion health score out of 20 points, benchmarks them against other companies, and provides exact steps to fix systemic barriers.

*Why it exists:* Without objective, repeatable numbers, workplace inclusion remains wishful thinking. NIWI replaces guesswork with verified data.

---

## 2. The Problem

### The Real-World Pain: A Tale of Two Perspectives
Consider **Sarah**, a senior software engineer who has ADHD and sensory sensitivities. At her job interview, the company claimed to be "inclusive." But once hired, Sarah was assigned a desk beneath buzzing fluorescent lights in a noisy open bullpen. When she requested noise-dampening panels and written task summaries instead of verbal interruptions, HR took five months to process the request, categorizing it as a "special medical disability accommodation." Exhausted and disengaged, Sarah resigned after nine months.

Meanwhile, **David**, the Chief People Officer at Sarah's company, genuinely believes his organization is a leader in diversity. On paper, his team hosted webinars and celebrated Neurodiversity Awareness Month. When Sarah left, David had no idea her resignation was caused by physical sensory overload and slow accommodation bureaucracy.

### What Companies Do Today Without NIWI
Without a specialized diagnostic tool, organizations rely on:
1. **Generic Engagement Surveys:** Annual surveys ask broad questions ("Do you feel valued at work?") that completely miss sensory barriers, interview biases, and accommodation delays.
2. **Expensive Manual Consultants:** Hiring human diversity consultants costs $30,000 to $100,000 per audit and takes 3 to 6 months to produce a static PDF slide deck that quickly becomes outdated.
3. **Unchecked Leadership Biases:** Company executives frequently rate their culture at an 8 out of 10, while frontline neurodivergent employees experience that same culture at a 3 out of 10.

**The Real Cost:** Companies lose top-tier technical and creative talent to avoidable turnover, pay thousands in redundant recruiting costs, and miss out on the competitive innovations neurodivergent professionals bring.

---

## 3. The Solution

NIWI provides an automated, end-to-end diagnostic and benchmarking platform (accessible publicly at `https://niwi.orchvate.in`):

1. **A Guided 40-Question Assessment:** Employees and leaders complete an accessible digital questionnaire covering 8 foundational pillars of employment.
2. **Intelligent Question Gating:** If a respondent works at a fully remote company with no physical office, physical workspace questions are skipped automatically without penalizing the organization's final score.
3. **Save & Resume Technology:** Busy employees can save their progress at any time and resume via a secure, tokenized email link (`/resume`).
4. **Deterministic Multi-Pillar Scoring:** In milliseconds, the backend scores responses across 8 dimensions on an empirical 0–20 scale, categorizing the organization into maturity bands (Level 1 Foundational, Level 2 Early Progress, Level 3 Developing, Level 4 Proficient, or Level 5 Leading).
5. **Perception Gap Analysis:** In the administrative dashboard, leadership scores are compared directly against frontline staff scores, instantly highlighting blind spots (e.g., "Leadership rates Workplace Culture at 16.5/20, but Neurodivergent employees rate it at 11.2/20 — a 5.3 variance gap").
6. **Consolidated Executive Reports:** Organizations receive automated diagnostic breakdowns and interactive radar charts comparing their score to industry peers.

---

## 4. Why It Exists (Vision & Purpose)

The vision of Orchvate is to build a corporate world where neurodivergent professionals are recognized as competitive assets rather than accommodation burdens. 

NIWI exists to establish the global operational benchmark for neuro-inclusion. By transforming subjective workplace culture into concrete, comparable metrics, NIWI allows companies to:
- Establish a factual baseline before spending money on diversity programs.
- Track progress year-over-year to verify return on investment.
- Compare inclusion across departments, seniority levels, and neurotypes.

---

## 5. Target Users and Personas

| Persona | Role | Primary Goal | Biggest Frustration | How NIWI Helps |
|---|---|---|---|---|
| **P1: Sarah (Neurodivergent Employee)** | Software Engineer / Individual Contributor | Share candid feedback on workplace friction without fear of retaliation. | Surveys force irrelevant questions and reveal personal identities. | 100% anonymous, accessible survey with dynamic gating and save/resume drafts. |
| **P2: David (Chief People Officer)** | Enterprise HR Executive | Understand company-wide inclusion health and justify DEI budget to the CEO. | Expensive consulting reports take months and give vague, high-level advice. | Real-time multi-respondent weighted dashboard, radar charts, and PDF executive reports. |
| **P3: Maya (Platform Operations Admin)** | Orchvate Super Admin | Monitor platform ingestion, manage tenant organizations, and reprocess failed messages. | Database crashes under high survey traffic; inability to see pipeline health. | Real-time Operations Command dashboard with sub-second telemetry, DLQ inspector, and one-click replay. |

---

## 6. User Stories

### Public & Employee Stories
- **US-01:** *As an employee*, I want to take the 40-question assessment on my laptop or phone without sensory distractions, so that I can provide candid workplace feedback.
- **US-02:** *As a busy respondent*, I want to save my draft and receive a secure resume link in my email, so that I can finish the survey later without losing my answers (see `app/api/drafts.py`).
- **US-03:** *As an employee at a 100% remote company*, I want questions about physical buildings to be automatically skipped, so that my company is not penalized for having no physical office (see `frontend/src/views/AuditForm.vue`).

### Employer & HR Admin Stories
- **US-04:** *As an HR Director*, I want to invite all 200 members of my engineering division using a single trackable link, so that their responses automatically group into our company profile (see `app/api/orgs.py`).
- **US-05:** *As a People Executive*, I want to compare how Leadership answered versus frontline Neurodivergent staff, so that I can identify perception gaps across our hierarchy (see `frontend/src/views/Organisations.vue`).
- **US-06:** *As an HR Analyst*, I want to export all employee submission data as a CSV spreadsheet, so that I can perform custom statistical modeling in Excel (see `frontend/src/views/Organisations.vue`).

### System Administrator Stories
- **US-07:** *As an Orchvate Super Admin*, I want to log in using Microsoft Entra ID (Azure AD) Single Sign-On, so that administrative access is secured by corporate identity governance (see `app/core/security.py`).
- **US-08:** *As a Systems Engineer*, I want an automated Operations Command dashboard showing queue depth, worker concurrency, and average latency, so that I can verify backend performance under load (see `frontend/src/views/SuperDashboard.vue`).
- **US-09:** *As an SRE*, I want to inspect and replay any dead-lettered submission with one click, so that no audit is ever permanently lost (see `app/api/routes.py`).

---

## 7. Features & System Capabilities

| Feature Name | Plain Words Description | Primary User | Source Code Location | Status |
|---|---|---|---|---|
| **40-Question Assessment** | Clean multi-step questionnaire evaluating 8 dimensions. | Public / Employees | `frontend/src/views/AuditForm.vue` | Active |
| **Dynamic Gating** | Skips physical workspace and supplier questions if not applicable. | Public / Employees | `frontend/src/views/AuditForm.vue`, `app/services/scoring_service.py` | Active |
| **Draft Save & Magic Resume** | Saves partial survey answers to PostgreSQL and emails a magic link. | Public / Employees | `app/api/drafts.py`, `frontend/src/views/ResumeDraft.vue` | Active |
| **Deterministic Scoring Engine** | Calculates 8 pillar scores (0–20 pts) and overall maturity band in < 1ms. | System / Backend | `app/services/scoring_service.py` | Active |
| **Outbox & Worker Fleet** | Decoupled background workers score audits and queue notifications without blocking web requests. | System / Backend | `app/services/outbox_service.py`, `app/tasks/service_bus_worker.py` | Active |
| **5-Minute Email Digest** | Groups audit notifications by organization into a consolidated 5-minute summary email. | Admins | `app/services/settings_service.py` | Active |
| **Operations Command (Super Admin)** | Real-time queue telemetry, latency tracking, and DLQ replay controls. | Super Admins | `frontend/src/views/SuperDashboard.vue`, `app/services/dashboard_service.py` | Active |
| **Multi-Respondent Org Portal** | Aggregates individual survey scores with customizable weights and demographic cuts. | HR Admins / Admins | `frontend/src/views/Organisations.vue`, `app/services/org_scoring_service.py` | Active |
| **Demographic Perception Gaps** | Real-time calculation of score variances (e.g. Leadership vs Neurodivergent). | HR Admins / Admins | `frontend/src/views/Organisations.vue` (lines 4565–4720) | Active |
| **ServiceNow-Style Query Builder** | Multi-attribute visual SQL query builder for searching and filtering submissions. | Admins | `frontend/src/components/ServiceNowFilterBuilder.vue`, `app/services/filter_service.py` | Active |
| **PDF Executive Report Dispatch** | Sends full diagnostic report with pillar scorecards directly to leadership. | Admins | `app/api/orgs.py`, `app/services/scoring_service.py` | Active |
| **AI Executive Summary Narrative** | LLM-synthesized narrative commentary for board-level reports. | HR Admins | `app/services/ai_service.py` | *Planned (Stub in code)* |

---

## 8. How a Typical Session Works

### Step 1: Accessing the Survey
An employee clicks a link provided by HR (either a direct company link `https://niwi.orchvate.in/audit?org=ACME` or an invitation token link `https://niwi.orchvate.in/audit?t=TOKEN`). The assessment page loads instantly in their browser.

### Step 2: Demographics and Gating
The respondent enters their role, department, seniority level, and whether they identify as neurodivergent. They are asked two gating questions:
1. "Does your organisation maintain a physical workplace?" (Yes/No)
2. "Does your organisation contract third-party vendors or suppliers?" (Yes/No)
If they select "No", the corresponding question sections are automatically omitted from their survey.

### Step 3: Completing Assessment Sections
The user answers Likert-scale questions (1 = Strongly Disagree to 5 = Strongly Agree) across the active dimensions:
- Leadership Commitment (LC)
- Recruitment & Onboarding (RO)
- Workplace Environment & Adjustments (WE)
- Benefits, Mental Health & Well-being (BE)
- Training & Awareness (TM)
- Culture, Advocacy & Community (CA)
- Performance & Career Progression (PC)
- Suppliers & Procurement (SP)

### Step 4: Submission & Instant Confirmation
Upon clicking "Submit Assessment":
1. The frontend validates that all required questions have answers.
2. An HTTP `POST /api/submit` request sends the answers to the backend.
3. The backend saves the raw submission and immediately acknowledges receipt (`HTTP 201 Created` with a `submission_id`).
4. The user sees an instant thank-you screen; they do not wait for email sending or background analytics.

### Step 5: Asynchronous Background Scoring
In the background:
1. The NIWI worker fleet claims the pending submission.
2. The deterministic scoring algorithm computes all 8 pillar scores and the overall index (e.g., 14.5 / 20).
3. The submission is linked to the employer's official account in `org_submission_links`.
4. A notification is queued for the 5-minute administrator digest.

### Step 6: HR Executive Review
The company's HR Director logs into the portal. Under the **Organisations** view, they see their updated aggregated score, explore the **Segments** tab to see perception differences, and click **Export CSV** or **Send Executive Report** to brief senior leadership.

---

## 9. Scope: Goals and Non-Goals

### Goals (What NIWI Must Do)
- Deliver an accessible, WCAG-compliant audit survey interface.
- Provide 100% deterministic, mathematically verifiable scoring without hallucination.
- Handle high-concurrency survey bursts (hundreds of simultaneous submissions) without dropping records.
- Preserve complete anonymity for individual employees while allowing organizations to aggregate team insights.
- Provide enterprise-grade administrative governance with Microsoft Entra ID Single Sign-On and Role-Based Access Control.

### Non-Goals (What NIWI Explicitly Does Not Do)
- **Not a medical diagnostic tool:** NIWI evaluates company culture and workplace practices; it does not diagnose individuals with ADHD, Autism, or other clinical conditions.
- **Not a public review board:** Unlike Glassdoor or Indeed, survey responses are private to the contracting organization and Orchvate; individual answers are never published publicly.
- **Not a general-purpose survey monkey:** NIWI is strictly focused on neurodiversity and cognitive inclusion; it is not designed to run arbitrary customer satisfaction surveys.

---

## 10. Success Metrics

| Metric | Target SLA | Measured Capability in Code / Tests | Evidence |
|---|---|---|---|
| **Submission Ingestion Latency** | P95 < 1,500 ms | **580 ms** average under 100 concurrent users | `tests/performance/reports/` |
| **Worker Scoring Duration** | < 100 ms per audit | **0.10 ms – 1.2 ms** pure scoring duration | `app/services/scoring_service.py` |
| **Data Integrity / Zero Loss** | 0 lost submissions | **100% (640 / 640 completed)** under load tests | PostgreSQL `raw_submissions` table |
| **Concurrent Idempotency** | 100% resolution | 10 concurrent requests with identical key return 1 record | `tests/test_complete_submission_flow.py` |
| **Test Suite Coverage** | 100% test pass rate | **6 / 6 Super Admin tests pass**, **131 total suite pass** | `pytest tests/` |

---

## 11. Assumptions, Constraints and Known Limitations

1. **Email Service Dependency:** Automated email delivery relies on Azure Communication Services (ACS). If the external ACS service experiences an Azure outage, emails cannot leave the server immediately. *Mitigation:* The system queues notifications in `service_bus_outbox` and marks jobs for retry.
2. **Current AI Feature Status:** *Needs confirmation:* The codebase contains an empty stub in `app/services/ai_service.py`. While the product roadmap envisions LLM-generated report commentary, the live platform currently generates 100% deterministic, rules-based scorecard narratives.
3. **Hardware-Adaptive Worker Bounds:** The worker pool automatically scales to `Cores - 1`. On very small 1-core VMs, the background worker and web server share a single core; production deployments should run on a minimum of 2 vCPUs.

---

## 12. Risks and Mitigations

| Risk | Impact | Likelihood | Mitigation in Code |
|---|---|---|---|
| **Survey Spam / Denial of Service** | High | Medium | IP-based sliding window rate limits (`SlowAPI` in `app/core/database.py`, `app/api/public.py`). |
| **Database Connection Exhaustion** | High | Low | Thread-safe connection pooling (`ThreadedConnectionPool`, statement timeout = 15s) and advisory locks. |
| **Stale Worker Processing** | Medium | Low | Stuck task recovery loop (`SELECT ... FOR UPDATE SKIP LOCKED` reclaimed after 3 minutes in `service_bus_worker.py`). |
| **Accidental Data Destruction** | Critical | Low | Bulk deletion restricted strictly to Super Admins with mandatory `DELETE ALL SUBMISSIONS` text challenge. |

---

## 13. Roadmap & Planned Evolutions

1. **AI-Powered Executive Commentary:** Implement `app/services/ai_service.py` using Azure OpenAI to synthesize customized paragraph commentary based on an organization's lowest-scoring pillars.
2. **Automated Benchmark Slicing:** Add dynamic industry sector benchmarks (e.g., Tech vs Finance vs Healthcare) directly within the Analytics view.
3. **Multi-Language Accessibility:** Localize survey questions into Spanish, French, German, and Japanese.
4. **Automated HRIS Integration:** Direct connectors (Workday, BambooHR) to automatically sync employee cohorts and department hierarchies.

---

## 14. Glossary

- **ADHD:** Attention Deficit Hyperactivity Disorder; a common neurodevelopmental difference impacting executive function and focus.
- **Autism:** A neurodivergent condition characterized by distinct patterns of sensory processing, communication, and information processing.
- **Neurodivergent (ND):** Having a brain that processes information differently from the neurological majority.
- **Neurotypical (NT):** Having brain function and processing that aligns with conventional societal expectations.
- **Likert Scale:** A 5-point rating scale from 1 (Strongly Disagree) to 5 (Strongly Agree).
- **Advisory Lock:** A PostgreSQL concurrency primitive that prevents two processes from creating duplicate records at the same millisecond.
- **DLQ (Dead-Letter Queue):** A storage area for messages that failed processing after multiple attempts, allowing engineers to inspect and fix errors safely.

