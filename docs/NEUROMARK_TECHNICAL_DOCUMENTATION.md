# NeuroMark (NeuroMark / Orchvate Audit) — Comprehensive Technical Reference Documentation
**Version:** 2.1 (Enterprise Production Edition)  
**Last Updated:** May 2026  
**Target System:** Single-Container Azure Container Apps & Azure Database for PostgreSQL  
**Author:** Senior Technical Writing & Architecture Team  

---

## Table of Contents
1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Product Overview](#3-product-overview)
4. [User Roles and Permissions (RBAC)](#4-user-roles-and-permissions-rbac)
5. [End-to-End Application Flow](#5-end-to-end-application-flow)
6. [Audit Structure and Question Analysis](#6-audit-structure-and-question-analysis)
7. [Scoring Engine and Maturity Model](#7-scoring-engine-and-maturity-model)
8. [Dynamic Email Report Generation](#8-dynamic-email-report-generation)
9. [Administrative Dashboard and Portal](#9-administrative-dashboard-and-portal)
10. [Tech Stack Deep Dive](#10-tech-stack-deep-dive)
11. [Deployment Architecture](#11-deployment-architecture)
12. [System Data Flow Diagrams](#12-system-data-flow-diagrams)
13. [API Reference (REST Specifications)](#13-api-reference-rest-specifications)
14. [Database Schema Specification](#14-database-schema-specification)
15. [Security Architecture](#15-security-architecture)
16. [Accessibility (a11y) and UX Design System](#16-accessibility-a11y-and-ux-design-system)

---

## 1. Executive Summary

### 1.1 Product Vision & Goals
**NeuroMark** (commercially branded as **NeuroMark** and powered by **Orchvate**) is a state-of-the-art SaaS self-assessment and auditing platform designed to measure and accelerate Neuro-Diversity (ND) inclusion maturity within corporate environments. The product is engineered to empower organizations to audit their operations across eight critical organizational dimensions: Leadership & Culture, Recruitment & Onboarding, Work Environment & Adjustments, Built Environment & Sensory, Talent Management & Development, Communication & Accessibility, Products & Customer Experience, and Suppliers & Procurement.

The primary objective of NeuroMark is to transition organizations from superficial compliance and checkbox diversity initiatives to meaningful, systemic neuroinclusion. By offering a multi-stage audit questionnaire, the platform automatically evaluates organizational practices, computes section-specific and cumulative scores, drafts comprehensive, tailored email reports featuring dynamic visualizations, and provides administrators with a centralized control center to review, modify, and dispatch feedback to respondents.

### 1.2 Target Audience & Stakeholders
*   **Organizational Representatives (Audit Takers):** HR directors, Diversity, Equity & Inclusion (DEI) leads, Operations executives, and facility managers who self-assess their organization's policies, environments, and practices.
*   **Orchvate Administrators:** Certified neuroinclusion consultants and auditors who review submissions, edit automatically generated reports to add custom consultant feedback, track compliance trends, and manage organization settings.
*   **Super Administrators:** High-level platform owners who manage RBAC, grant administrative permissions, edit settings, and configure integrations.
*   **Neurodivergent Employees:** The ultimate beneficiaries of the platform whose workplace experiences, physical spaces, and career progression are improved as a result of organizational audits.

### 1.3 Strategic Purpose
In the modern landscape of human resource management, traditional diversity frameworks often overlook cognitive differences. NeuroMark fills this critical void by providing a scientific, structured, and auditable self-assessment system. The platform replaces manual processes—such as Microsoft Forms, local Excel macros, and manual copy-pasting—with a unified, cloud-hosted, scalable web application. It integrates robust security, enterprise Single Sign-On (SSO) through Microsoft Entra ID, Azure Database for PostgreSQL, and Azure Communication Services (ACS) into a seamless, high-performance solution.

---

## 2. Problem Statement

### 2.1 The Invisible Workforce: Neurodiversity in Corporate Environments
Neurodiversity refers to the natural variation in human brain function and behavior, encompassing conditions such as Autism Spectrum Condition (ASC), Attention Deficit Hyperactivity Disorder (ADHD), Dyslexia, Dyspraxia (Developmental Coordination Disorder), Dyscalculia, and Tourette Syndrome. Research indicates that neurodivergent individuals constitute approximately 15% to 20% of the global population. 

Despite this significant representation, corporate workplaces are predominantly designed for neurotypical cognitive profiles. This mismatch leads to systemic biases in recruitment, communication barriers, sensory overload in physical environments, and rigid performance evaluation frameworks.

### 2.2 Why Neuro-Inclusion is Ignored
1.  **Lack of Quantifiable Data:** Organizations cannot manage what they do not measure. Without a structured auditing framework, leadership teams lack visibility into how their environments exclude neurodivergent staff.
2.  **Checkbox Diversity (DEI) Fatigue:** Conventional DEI efforts focus heavily on visible demographics (race, gender, physical disability) while cognitive accessibility remains neglected.
3.  **Complex Accommodation Processes:** Requesting workplace adjustments is frequently stigmatized or burdened by bureaucratic barriers, forcing neurodivergent employees to remain undisclosed.
4.  **Recruitment Funnel Bottlenecks:** Traditional hiring practices rely heavily on unstructured interviews, behavioral metrics, and social signaling, which systematically filter out candidates with divergent communication styles.

### 2.3 The Limitations of Existing HR Tools
Conventional employee engagement surveys (e.g., Glint, Culture Amp) or physical compliance checkers (e.g., ADA guidelines) fail to evaluate cognitive inclusion. They do not address:
*   Sensory stressors (e.g., lighting glare, noise levels in open-plan offices).
*   Cognitive load in communications (e.g., abstract language, lack of pre-meeting agendas).
*   Biases in talent development (e.g., career progression plans that mandate public speaking or specific social styles).

### 2.4 The Human and Economic Cost of Exclusion
*   **Masking and Burnout:** Neurodivergent employees expend significant cognitive effort "masking"—mimicking neurotypical social behaviors—leading to high rates of anxiety, depression, and occupational burnout.
*   **High Attrition Rates:** Due to unaccommodating spaces and unsupportive management, talented neurodivergent employees leave organizations prematurely.
*   **Lost Innovation:** Companies miss out on the distinct problem-solving capacities, hyper-focus, creativity, and analytical skills that neurodivergent individuals bring to teams.
*   **Litigation and Compliance Risks:** Failure to provide reasonable accommodations under regional statutes (e.g., Americans with Disabilities Act, UK Equality Act 2010) exposes corporations to legal liabilities.

---

## 3. Product Overview

NeuroMark is built as a highly responsive, secure, and visually appealing web application. It transitions the old Orchvate auditing workflow into a modern, automated pipeline:

| Dimension | Legacy Workflow | NeuroMark Workflow |
| :--- | :--- | :--- |
| **User Interface** | Microsoft Forms (generic, unbranded) | Vue 3 Single Page Application (highly branded, interactive) |
| **Data Collection** | Manual Excel exports | Real-time writes to Azure Database for PostgreSQL |
| **Scoring Engine** | Local, offline Python scripts | Real-time calculation in FastAPI/Azure Functions |
| **Report Generation** | Copy-pasting text, manually editing docs | Automatic HTML generation, custom radar charts |
| **Quality Control** | No intermediate review step | Interactive Admin Dashboard for editing drafts |
| **Email Delivery** | Outlook client manual sends | Azure Communication Services API |
| **Audit Trail** | Disjointed spreadsheets | Relational database status tracking (`pending`, `sent`) |

---

## 4. User Roles and Permissions (RBAC)

NeuroMark enforces a strict Role-Based Access Control (RBAC) model. Access to resources is checked on both the frontend (Vue Router guards and session state) and the backend (API endpoint authorization layers).

### 4.1 Organizational Representative (Audit Taker)
*   **Access:** Anonymous public access to the landing page and the 45-field Audit Form.
*   **Permissions:** Can fill and submit the audit form. Cannot view other organizations' data, access the dashboard, or modify configuration settings.

### 4.2 Orchvate Administrator
*   **Access:** Authenticated access via Microsoft Entra ID (SSO).
*   **Permissions:**
    *   View all audit submissions in a paginated, filterable table.
    *   Inspect detailed submission scores and question-by-question responses.
    *   Edit the automatically generated HTML report body using a rich-text editor.
    *   Trigger report delivery to respondents via Azure Communication Services.
    *   Toggle system alerts (bell notifications) in the dashboard header.
    *   Access and test settings (e.g., update sender names or support email inboxes).

### 4.3 Super Administrator
*   **Access:** Authenticated access via Microsoft Entra ID (SSO) with `super` role flag.
*   **Permissions:**
    *   Inherits all Orchvate Administrator permissions.
    *   Access the **User Management** portal (`/admin/users`).
    *   Add new administrators, assign roles (`admin`, `super`), or revoke access.
    *   Update underlying global settings (e.g., SMTP configurations, API connection strings).

---

## 5. End-to-End Application Flow

```
+------------------+       Submit       +-------------------------+       Trigger       +--------------------+
|  Vue 3 Frontend  | -----------------> | Python Backend API      | ------------------> | PostgreSQL DB      |
|  (Audit Form)    |  (POST /submit)    | (Scores & Drafts Email) |  (Inserts Record)   | (status='pending') |
+------------------+                    +-------------------------+                     +--------------------+
                                                     |                                             |
                                                     | Notify                                      |
                                                     v                                             v
                                        +-------------------------+                     +--------------------+
                                        | Admin (Email Alert)     |                     | Admin Dashboard    |
                                        +-------------------------+                     | (Fetches list)     |
                                                                                        +--------------------+
                                                                                                   |
                                                                                                   | Review & Edit
                                                                                                   v
+------------------+       Mark Sent    +-------------------------+       Send API      +--------------------+
| Respondent Email | <----------------- | Azure Comm Services     | <------------------ | Admin Clicks Send  |
| (HTML Report)    |  (status='sent')   | (ACS Delivery Engine)   | (POST /{id}/send)   | (Dashboard UI)     |
+------------------+                    +-------------------------+                     +--------------------+
```

### 5.1 Step-by-Step Walkthrough

#### Step 1: Landing and Demographics Collection
The user lands on the application. The sidebar displays a step-by-step progress tracking wizard, while the right-hand side displays a contextual information card explaining the purpose of the audit. The user enters their name, designation, organization name, work email address, and optional contact number.
*   *Validation:* The platform enforces corporate domain validation. Free email providers (e.g., Gmail, Yahoo, Hotmail) are blocked.

#### Step 2: Answering the Audit Sections
The user advances through 8 sections, answering 5 questions per section. Each question is rated using button options: **Yes**, **Partially**, **No**, and **Not Sure**. The sidebar updates a mini progress bar for the current section and a vertical progress track for the entire questionnaire. Contextual sidebars display tips and explanations for each topic.

#### Step 3: Form Submission and Processing
Upon clicking "Submit Audit", the frontend sends a `POST` request containing all answers and demographics to `/api/submit`. 
*   The scoring engine evaluates the inputs, maps them against pre-written interpretations, generates a high-fidelity HTML email report containing a dynamically rendered radar chart, and commits the record to the PostgreSQL database with the status set to `pending`.
*   If enabled, a background thread sends an email notification to Orchvate administrators informing them of a new submission.

#### Step 4: Administrator Review
An administrator authenticates via Microsoft Entra ID and logs into the Admin Dashboard. They view the submission in the list, see the overall score (e.g., `12.50 / 20`), and click the row to open the details.
*   The detail view displays the score breakdown per section, the overall average maturity, and a rich-text editor containing the pre-rendered HTML report.

#### Step 5: Customization and Dispatch
The administrator can edit the report draft directly in the editor to insert qualitative advice, observations, or scheduling links. After reviewing, they click "Send Email".
*   The backend receives a `POST` request to `/api/submissions/{id}/send`, converts basic HTML elements to plain text (for multi-part email delivery), routes the dispatch through Azure Communication Services, and updates the database record status to `sent` along with the timestamp.

---

## 6. Audit Structure and Question Analysis

The NeuroMark questionnaire comprises 45 fields: 5 demographic questions (Q1–Q4, including designation) and 40 thematic questions (Q5–Q44) divided into 8 sections.

| Section Code | Section Name | Question Range | Focus Areas |
| :--- | :--- | :--- | :--- |
| **LC** | Leadership & Culture | Q5 – Q9 | Senior sponsorship, values integration, leadership training, public branding, representation |
| **RO** | Recruitment & Onboarding | Q10 – Q14 | Job design, interview adaptations, adjustment availability, clear onboarding formats, bias training |
| **WE** | Work Environment & Adjustments | Q15 – Q19 | Request pathways, flexible work, manager capability, assistive tools, psychological safety |
| **BE** | Built Environment & Sensory | Q20 – Q24 | Quiet spaces, acoustic/lighting design, wayfinding signage, workstation control, sensory audits |
| **TM** | Talent Management & Development | Q25 – Q29 | Appraisals review, development access, strengths-based metrics, mentoring networks, retention data |
| **CA** | Communication & Accessibility | Q30 – Q34 | Plain language, multi-format comms, pre-meeting preparation, tool testing, preference options |
| **PC** | Products & Customer Experience | Q35 – Q39 | Inclusive product design, user testing, customer support training, digital standards, adjustments |
| **SP** | Suppliers & Procurement | Q40 – Q44 | Supplier diversity, contract standards, inclusive procurement, SRM integration, ecosystem sharing |

---

### 6.1 Leadership & Culture (Q5 – Q9)
Leadership sets the tone for an organization's values. Without executive sponsorship and training, neuroinclusion initiatives remain isolated programs rather than core culture.

*   **Q5: Named executive sponsor responsible for neurodiversity inclusion.**
    *   *Rationale:* Establishes strategic accountability. Without a senior champion, initiatives lack funding and influence.
*   **Q6: Inclusion explicitly referenced in strategy/DEI policies.**
    *   *Rationale:* Formalizes commitment in official governance, protecting programs during leadership changes.
*   **Q7: Senior leaders trained on neurodiversity in the past 12 months.**
    *   *Rationale:* Counteracts cognitive bias at decision-making levels, reducing institutional resistance.
*   **Q8: Public communication of commitment to neurodiversity.**
    *   *Rationale:* Builds brand trust, attracting neurodivergent talent and establishing market leadership.
*   **Q9: Representation of neurodivergent employees in leadership roles.**
    *   *Rationale:* Ensures diverse cognitive styles contribute to strategy.

---

### 6.2 Recruitment & Onboarding (Q10 – Q14)
Standard hiring processes rely on social cues that can disadvantage neurodivergent candidates, filtering out high-performing talent.

*   **Q10: Job descriptions reviewed to remove restrictive requirements.**
    *   *Rationale:* Eliminates unnecessary criteria (e.g., "excellent communication skills" for a programming role) that deter qualified applicants.
*   **Q11: Alternative interview formats offered proactively.**
    *   *Rationale:* Allows candidates to demonstrate skills in practical formats (e.g., work trials or portfolio reviews) rather than relying solely on verbal interviews.
*   **Q12: Reasonable adjustments discussed proactively during recruitment.**
    *   *Rationale:* Normalizes accommodation requests, removing the burden of disclosure from candidates.
*   **Q13: Onboarding structured, clear, and provided in multiple formats.**
    *   *Rationale:* Minimizes anxiety during transition by outlining expectations and schedules clearly.
*   **Q14: Hiring managers trained to conduct inclusive, bias-aware interviews.**
    *   *Rationale:* Prevents bias during selection.

---

### 6.3 Work Environment & Adjustments (Q15 – Q19)
Day-to-day practices dictate employee productivity and wellbeing. Accessible adjustments allow staff to work effectively without masking.

*   **Q15: Clear, accessible process to request reasonable adjustments.**
    *   *Rationale:* A transparent request process encourages employees to seek support early.
*   **Q16: Flexible working arrangements available and supported.**
    *   *Rationale:* Allows employees to manage energy and focus by adjusting their hours and work locations.
*   **Q17: Managers trained to implement adjustments.**
    *   *Rationale:* Equips managers to handle requests constructively, avoiding friction.
*   **Q18: Assistive technologies and tools available.**
    *   *Rationale:* Provides resources (e.g., screen readers, noise-canceling headphones, writing aids) that help employees work more efficiently.
*   **Q19: Adjustment requests handled promptly and without stigma.**
    *   *Rationale:* Prompt, stigma-free responses build organizational trust and prevent burnout.

---

### 6.4 Built Environment & Sensory (Q20 – Q24)
Physical workspaces often present sensory challenges. Sensory-friendly offices help reduce distraction, fatigue, and overload.

*   **Q20: Quiet or low-stimulation spaces available.**
    *   *Rationale:* Quiet zones offer a space to reset, helping to prevent sensory overload.
*   **Q21: Lighting, acoustics, and sensory factors considered in design.**
    *   *Rationale:* Lighting and acoustic planning reduce sensory fatigue caused by office noise and bright lights.
*   **Q22: Clear, consistent wayfinding and signage.**
    *   *Rationale:* Easy navigation reduces cognitive load and anxiety in physical environments.
*   **Q23: Employees able to personalize their workstations.**
    *   *Rationale:* Gives staff control over their immediate space (e.g., lighting, furniture) to suit their needs.
*   **Q24: Sensory/environmental audit conducted in past 2 years.**
    *   *Rationale:* Systematic reviews identify environmental challenges that might otherwise go unnoticed.

---

### 6.5 Talent Management & Development (Q25 – Q29)
Standard career progression and evaluation metrics can favor a single style of working, which can limit development opportunities for neurodivergent staff.

*   **Q25: Appraisal processes reviewed to prevent disadvantage.**
    *   *Rationale:* Reviews ensure performance metrics focus on actual output rather than subjective social qualities.
*   **Q26: Equal access to learning and development.**
    *   *Rationale:* Development programs should accommodate different learning styles.
*   **Q27: Strengths-based approaches used in talent management.**
    *   *Rationale:* Focuses roles around individual strengths rather than forcing compliance with a standard template.
*   **Q28: Mentoring or coaching programs available.**
    *   *Rationale:* Provides career guidance and support tailored to individual needs.
*   **Q29: Retention data monitored to track turnover.**
    *   *Rationale:* Analysis of retention patterns helps identify areas where neurodivergent staff may need more support.

---

### 6.6 Communication & Accessibility (Q30 – Q34)
Information flow affects employee performance and participation. Clear, accessible communication improves collaboration across teams.

*   **Q30: Internal communications written in plain language.**
    *   *Rationale:* Plain language makes information easier to process and reduces ambiguity.
*   **Q31: Information provided in multiple formats.**
    *   *Rationale:* Multi-format communication (e.g., video, audio, text) supports diverse learning and processing styles.
*   **Q32: Meeting agendas shared in advance.**
    *   *Rationale:* Pre-shared agendas allow participants to prepare, leading to more productive discussions.
*   **Q33: Digital tools tested for accessibility.**
    *   *Rationale:* Testing digital platforms prevents system barriers from hindering day-to-day work.
*   **Q34: Employees able to request communication adjustments.**
    *   *Rationale:* Communication options (e.g., written follow-ups, camera-optional policies) help accommodate different needs.

---

### 6.7 Products & Customer Experience (Q35 – Q39)
Cognitive accessibility extends to an organization's products and services, ensuring all customers can access them.

*   **Q35: Customer-facing products designed with neurodivergent users in mind.**
    *   *Rationale:* Design consideration ensures products are accessible and easy for all clients to use.
*   **Q36: Neurodivergent customers involved in testing.**
    *   *Rationale:* Direct user feedback helps identify and address accessibility issues during design.
*   **Q37: Customer service staff trained to support neurodivergent clients.**
    *   *Rationale:* Training helps support teams assist clients with different communication needs more effectively.
*   **Q38: Digital products meet recognized accessibility standards.**
    *   *Rationale:* Conforming with guidelines (e.g., WCAG) ensures basic digital accessibility.
*   **Q39: Clear process for customers to request adjustments/formats.**
    *   *Rationale:* Providing accessible options (e.g., phone, chat, plain-text documents) improves the client experience.

---

### 6.8 Suppliers & Procurement (Q40 – Q44)
Extending inclusion practices to the supply chain helps build a more supportive ecosystem and encourages partners to adopt similar policies.

*   **Q40: Procurement process includes supplier inclusion practices.**
    *   *Rationale:* Inclusion checks encourage suppliers to evaluate their own neurodiversity policies.
*   **Q41: Suppliers expected to meet inclusion standards in contracts.**
    *   *Rationale:* Clear contract standards establish inclusion as a shared business priority.
*   **Q42: Actively seek to work with neurodiversity-friendly suppliers.**
    *   *Rationale:* Supporting inclusive businesses helps promote neurodiversity initiatives in the wider market.
*   **Q43: Inclusion reviewed in supplier relationship management.**
    *   *Rationale:* Regular reviews keep partners focused on maintaining and improving their policies.
*   **Q44: Organization shares inclusion best practices with the supply chain.**
    *   *Rationale:* Sharing resources helps suppliers implement effective neurodiversity adjustments.

---

## 7. Scoring Engine and Maturity Model

The NeuroMark scoring engine translates questionnaire responses into quantifiable metrics.

### 7.1 Quantitative Weighting Algorithm
For each of the 40 questions ($q_5$ to $q_{44}$), points are assigned based on a predefined dictionary mapping:
$$\text{Score}(q_i) = \begin{cases} 
4 & \text{if answer is "Yes"} \\ 
2 & \text{if answer is "Partially"} \\ 
0 & \text{if answer is "No"} \\ 
0 & \text{if answer is "Not Sure"} 
\end{cases}$$

### 7.2 Section Score Derivation
A section score is calculated as the sum of points for its 5 mapped questions. With a maximum of 4 points per question, each section has a score range of 0 to 20:
$$\text{Score}_{\text{Section}} = \sum_{j \in \text{Questions}} \text{Score}(q_j)$$

### 7.3 Overall Score Calculation
The overall score is calculated as the arithmetic average of all 8 section scores:
$$\text{Score}_{\text{Overall}} = \frac{1}{8} \sum_{k=1}^{8} \text{Score}_{\text{Section}_k}$$

The system rounds this score to two decimal places ($Score_{Overall} \in [0.00, 20.00]$).

---

### 7.4 Maturity Level Classification
Maturity is assessed at both the section and overall level. The platform uses a nested level representation.

#### Underlying Database & Rules Engine Scale
The database and rules engine use a 3-tier classification to map sections to pre-written interpretation texts:

| Score Range | Maturity Label | Index | Strategic Implications |
| :--- | :--- | :--- | :--- |
| **0 – 6** | Level 1 — Foundational | 0 | The organization is starting its neurodiversity inclusion journey. Awareness is limited, and policies do not address cognitive needs. Primary focus should be leadership education. |
| **7 – 14** | Level 2 — Early Progress | 1 | Early inclusion efforts are in place but remain inconsistent. Pockets of good practice exist, but formalizing commitments and training managers is key to progress. |
| **15 – 20** | Level 3 — Developing | 2 | The organization has a solid inclusion framework. Key policies are integrated, but continued focus on impact measurement and scaling is needed. |

#### High-Fidelity Front-Facing Presentation Scale
The report and dashboard translate the overall average score into a 5-tier maturity scale to provide a more detailed progression path:

```
[0.00 - 6.00] ──> Level 1: Starting out (Foundational)
[6.01 - 10.00] ─> Level 2: Early Progress
[10.01 - 14.00] ─> Level 3: Developing
[14.01 - 18.00] ─> Level 4: Advanced
[18.01 - 20.00] ─> Level 5: Leading
```

#### Detailed Breakdown of the 5 Maturity Levels:
1.  **Level 1 — Starting out (Score: 0.00 – 6.00):** Neurodiversity is not yet part of corporate planning. The workplace has sensory and communication barriers, and accommodations are handled on an ad-hoc basis.
2.  **Level 2 — Early Progress (Score: 6.01 – 10.00):** Leadership has begun training, and some accommodation options are available. However, policies are not yet formally documented or consistently implemented.
3.  **Level 3 — Developing (Score: 10.01 – 14.00):** Clear adjustment pathways are in place, recruitment reviews are underway, and digital accessibility is monitored. Managers are generally supportive but still need structured guidance.
4.  **Level 4 — Advanced (Score: 14.01 – 18.00):** Inclusion is integrated into recruitment, workspace design, and talent management. Mentorship networks are active, and physical spaces feature dedicated quiet zones.
5.  **Level 5 — Leading (Score: 18.01 – 20.00):** Neurodiversity is a key part of organizational strategy. Best practices are shared with suppliers, customers are offered communication options, and inclusion metrics are regularly audited.

---

## 8. Dynamic Email Report Generation

NeuroMark generates high-fidelity HTML email reports designed for compatibility across modern and legacy email clients (including Microsoft Outlook, Gmail, Apple Mail).

### 8.1 Visual Components

#### Radial Metric Score Arc
At the top right, a vector circular gauge displays the organization's average score. The SVG arc is calculated dynamically using a dash-array stroke representation:
$$\text{dashOffset} = \text{round}\left( \frac{\text{Score}_{\text{Overall}}}{20.0} \times 226.2, 1 \right)$$
```xml
<svg width="84" height="84" viewBox="0 0 84 84">
  <circle cx="42" cy="42" r="36" fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="6"/>
  <circle cx="42" cy="42" r="36" fill="none" stroke="#7F77DD" stroke-width="6"
          stroke-dasharray="{dash} 226.2" stroke-dashoffset="0"
          stroke-linecap="round" transform="rotate(-90 42 42)"/>
  <text x="42" y="38" text-anchor="middle" font-size="18" fill="#FFFFFF">{overall_avg_display}</text>
  <text x="42" y="52" text-anchor="middle" font-size="10" fill="#AFA9EC">of 20</text>
</svg>
```

#### Dynamic Segment Progress Bars
Within each segment card, a horizontal progress bar displays the section score out of 20:
```html
<table width="100%">
  <tr>
    <td width="{fill_w}%" height="4" style="background:#7F77DD;border-radius:3px 0 0 3px;"></td>
    <td width="{empty_w}%" height="4" style="background:#E0DDD8;border-radius:0 3px 3px 0;"></td>
  </tr>
</table>
```

#### Interactive Maturity Scale Indicator
A 5-column scale is rendered in the footer of the email, highlighting the organization's current level:
```html
<td width="20%" align="center">
  <table width="100%">
    <tr><td height="6" style="background:#7F77DD;border-radius:3px;"></td></tr>
    <tr><td style="color:#534AB7;font-weight:600;">Level 3 ← You<br>Developing</td></tr>
  </table>
</td>
```

### 8.2 Radar Chart Generator
Rather than running heavy rendering libraries on the backend, NeuroMark uses the **QuickChart API** to generate the radar chart. The scoring engine builds a JSON configuration, URL-encodes it, and embeds it as an image source:
```
https://quickchart.io/chart?w=500&h=340&v=2&c=%7B%22type%22%3A%22radar%22...
```

*   **Labels:** Leadership & Culture, Recruitment & Onboarding, Work Environment, Built Environment, Talent Management, Communication, Products & CX, Suppliers & Procurement.
*   **Colors:** Accent fill of `rgba(127, 119, 221, 0.15)` with borders and grid markers in Orchvate purple (`#7F77DD`).
*   **Scale:** Set to a maximum of 20 with step sizes of 5 to align with section score ranges.

### 8.3 Azure Communication Services Integration
The platform uses the `azure-communication-email` SDK to send reports. The email dispatcher supports:
1.  **Multi-Part Deliverability:** Dispatches both rich HTML and plain-text alternatives (using regex stripping to support legacy clients).
2.  **Thread Pool Execution:** Admin alerts are sent in a separate background thread, preventing email latency from blocking database transactions or API responses.
3.  **Configurable Sender Info:** The sender name and verified domain address are managed through the database and loaded dynamically at dispatch time.

---

## 9. Administrative Dashboard and Portal

The administrative dashboard provides a management interface for Orchvate auditors.

### 9.1 Overview & Analytics View
*   **Submissions Overview:** Lists submissions with metadata, overall scores, and status tags (`pending` or `sent`).
*   **Dynamic Search:** Filters records by name, email, company, or status.
*   **Analytics Panel:** Displays trend charts, Average Score distribution, and section performance benchmarks.

### 9.2 Submission Details & Live Email Editor
*   **Score Card Breakdown:** Lists the score and maturity classification for all 8 sections.
*   **Audit Answer View:** Displays the organization's answer to each individual question.
*   **Live Email Editor:** A rich-text editor preloaded with the generated report HTML.
    *   *Save:* Saves changes back to the database.
    *   *Regenerate:* Restores the draft back to the default scoring logic recommendations.
    *   *Send:* Dispatches the email via ACS and updates the status to `sent`.

### 9.3 Settings Panel & User Management
*   **System Settings:** Allows administrators to configure the sender name, sender email, support email, and notifications email.
*   **Alert Configuration:** Turn on email notifications for new submissions.
*   **User Management Portal:** Super administrators can add new team members by email, assign roles (`admin` or `super`), and revoke access.

---

## 10. Tech Stack Deep Dive

```
+-----------------------------------------------------------------------------------+
|                           FRONTEND (Vue 3 Single Page App)                        |
|   +------------------+   +-------------------+   +----------------------------+   |
|   |  Vue Router 4    |   |  Vite Build Tool  |   |  Microsoft MSAL SSO        |   |
|   +------------------+   +-------------------+   +----------------------------+   |
+-----------------------------------------------------------------------------------+
                                         |
                                         | HTTP / HTTPS Requests
                                         v
+-----------------------------------------------------------------------------------+
|                         BACKEND API (FastAPI / Python Web App)                    |
|   +------------------+   +-------------------+   +----------------------------+   |
|   |  Uvicorn Server  |   |  Psycopg2 DB Driver|  |  Azure SDK (ACS Email)     |   |
|   +------------------+   +-------------------+   +----------------------------+   |
+-----------------------------------------------------------------------------------+
                                         |
                                         | SQL Queries (TCP 5432)
                                         v
+-----------------------------------------------------------------------------------+
|                     DATABASE (Azure PostgreSQL Flexible Server)                   |
+-----------------------------------------------------------------------------------+
```

### 10.1 Frontend Architecture (Vue 3)
*   **Build Tool:** Vite, configured for fast development reloading and optimized production builds.
*   **Routing:** Vue Router 4, configured with navigation guards that verify session credentials (`nd_auth`) before loading admin pages.
*   **Design Tokens:** Managed through vanilla CSS variables in `frontend/src/style.css`.
*   **State Management:** Session storage caches authentication state (`nd_auth`, `nd_role`) to minimize login latency.

### 10.2 Backend Architecture (FastAPI & Azure Functions)
The platform is designed with a dual-backend architecture:
1.  **FastAPI Application:** Used for containerized hosting. The server runs on Uvicorn, exposing structured endpoints under the `/api` prefix.
2.  **Azure Functions Host:** Supported for serverless environments. The same scoring and routing logic is mirrored in `function_app.py`.

### 10.3 Database Layer (PostgreSQL)
*   **Driver:** `psycopg2-binary` for connection pooling.
*   **Connection Security:** Enforces `sslmode=require` for all database interactions.
*   **Transaction Management:** Uses context managers to ensure transactions rollback in the event of an execution error.

### 10.4 Authentication Layer (Microsoft Entra ID)
*   **Integration:** Authenticates administrators using `@azure/msal-browser` for Single Sign-On (SSO).
*   **Validation:**
    *   Admin logs in through Microsoft's authorization portal.
    *   The frontend receives the login response and verifies the email against the `admin_users` table in the database.
    *   If authorized, the backend returns the user's role (`admin` or `super`), which is stored in session storage.

---

## 11. Deployment Architecture

NeuroMark is deployed on **Azure Container Apps (ACA)** in a single-container architecture.

### 11.1 The Single-Container Design
Rather than running separate frontend and backend containers, NeuroMark bundles both into a single Docker image:
*   **Port 80 Ingress:** Nginx listens on port 80. It serves the Vue SPA static files directly from `/app/dist` and forwards API requests (`/api/*`) to Uvicorn on port 8000.
*   **Uvicorn Application:** Runs locally (`127.0.0.1:8000`) within the container, handling API requests.
*   **Supervisor Daemon:** Manages both processes, restarting them if a failure occurs.

### 11.2 Nginx Configuration
```nginx
server {
    listen 80;
    server_name localhost;

    location / {
        root /app/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 11.3 Deployment Configuration
*   **Scale-to-Zero:** Min replicas is set to 0. The platform spins down during inactive hours to minimize hosting costs.
*   **Secrets Management:** Sensitive variables (e.g., PostgreSQL credentials, ACS connection strings) are stored as container secrets.

---

## 12. System Data Flow Diagrams

### 12.1 Audit Submission Flow
1.  **Form Completion:** Respondent answers questions and clicks submit.
2.  **API Request:** Frontend validates fields and sends a `POST /api/submit` request.
3.  **Scoring Engine:** The backend calculates section scores, overall averages, and maturity levels.
4.  **HTML Render:** The backend generates the HTML email report, embedding the radar chart image link.
5.  **Database Commit:** The record is saved to the `submissions` table with `status = 'pending'`.
6.  **Admin Alert:** If enabled, the system starts a background thread to notify administrators of a new submission.
7.  **Client Response:** The API returns `{ success: true, submission_id: X }`.

### 12.2 Report Customization & Delivery Flow
1.  **Admin Login:** Administrator authenticates and retrieves the submissions list.
2.  **Inspect Draft:** Administrator reviews scores and opens the HTML report editor.
3.  **Save Changes:** Editing the report sends a `PUT /api/submissions/{id}/email` request to save changes.
4.  **Send Trigger:** Admin clicks "Send Email" (`POST /api/submissions/{id}/send`).
5.  **Dispatch Engine:**
    *   Backend loads sender details from settings.
    *   ACS API constructs the message payload and sends the email.
    *   Database updates the submission status to `sent` along with the timestamp.
6.  **Confirmation:** The dashboard disables the edit/send controls for the sent record.

---

## 13. API Reference (REST Specifications)

### 13.1 POST `/api/submit`
*   **Description:** Submits a completed audit form.
*   **Payload (JSON):**
    ```json
    {
      "name": "Jane Doe",
      "designation": "HR Director",
      "company_name": "Initech Corp",
      "email": "jane@initech.com",
      "contact_number": "+1 555-0199",
      "q5": "Yes", "q6": "Partially", "q7": "No", "q8": "Not Sure", "q9": "Yes",
      "q10": "Yes", "q11": "Yes", "q12": "Partially", "q13": "No", "q14": "Yes",
      "q15": "Yes", "q16": "Yes", "q17": "Yes", "q18": "Yes", "q19": "Yes",
      "q20": "Partially", "q21": "Partially", "q22": "Yes", "q23": "Yes", "q24": "No",
      "q25": "Yes", "q26": "Yes", "q27": "Yes", "q28": "Partially", "q29": "No",
      "q30": "Yes", "q31": "Yes", "q32": "Yes", "q33": "Yes", "q34": "Yes",
      "q35": "Partially", "q36": "No", "q37": "No", "q38": "Yes", "q39": "Partially",
      "q40": "No", "q41": "No", "q42": "Not Sure", "q43": "No", "q44": "No"
    }
    ```
*   **Response (201 Created):**
    ```json
    {
      "success": true,
      "submission_id": 412
    }
    ```

### 13.2 GET `/api/submissions`
*   **Description:** Retrieves all submissions for the dashboard list view.
*   **Response (200 OK):**
    ```json
    [
      {
        "id": 412,
        "name": "Jane Doe",
        "designation": "HR Director",
        "company_name": "Initech Corp",
        "email": "jane@initech.com",
        "submitted_at": "2026-05-24T01:10:00Z",
        "overall_avg": 12.50,
        "overall_level": "Level 2 — Early Progress",
        "status": "pending"
      }
    ]
    ```

### 13.3 GET `/api/submissions/{id}`
*   **Description:** Retrieves the complete detail record for a specific submission.
*   **Response (200 OK):**
    ```json
    {
      "id": 412,
      "submitted_at": "2026-05-24T01:10:00Z",
      "name": "Jane Doe",
      "company_name": "Initech Corp",
      "email": "jane@initech.com",
      "contact_number": "+1 555-0199",
      "designation": "HR Director",
      "q5": "Yes", "q6": "Partially", "q7": "No",
      "lc_score": 10, "lc_level": "Level 2 — Early Progress",
      "ro_score": 14, "ro_level": "Level 2 — Early Progress",
      "we_score": 20, "we_level": "Level 3 — Developing",
      "be_score": 12, "be_level": "Level 2 — Early Progress",
      "tm_score": 14, "tm_level": "Level 2 — Early Progress",
      "ca_score": 20, "ca_level": "Level 3 — Developing",
      "pc_score": 6,  "pc_level": "Level 1 — Foundational",
      "sp_score": 4,  "sp_level": "Level 1 — Foundational",
      "overall_avg": 12.50,
      "overall_level": "Level 2 — Early Progress",
      "email_body": "<!DOCTYPE html><html>...",
      "status": "pending",
      "sent_at": null
    }
    ```

### 13.4 PUT `/api/submissions/{id}/email`
*   **Description:** Updates the email report draft.
*   **Payload (JSON):**
    ```json
    {
      "email_body": "<!DOCTYPE html><html><body>...edited consultant notes...</body></html>"
    }
    ```
*   **Response (200 OK):**
    ```json
    {
      "success": true
    }
    ```

### 13.5 POST `/api/submissions/{id}/send`
*   **Description:** Sends the email report and marks the record as sent.
*   **Response (200 OK):**
    ```json
    {
      "success": true,
      "sent_at": "2026-05-24T01:25:00Z"
    }
    ```

### 13.6 POST `/api/submissions/{id}/regenerate-email`
*   **Description:** Restores the report draft to the default scoring template.
*   **Response (200 OK):**
    ```json
    {
      "success": true,
      "email_body": "<!DOCTYPE html><html>..."
    }
    ```

### 13.7 GET & PUT `/api/settings`
*   **Description:** Retrieves or updates platform settings.
*   **Payload (JSON):**
    ```json
    {
      "sender_name": "Orchvate Auditing Team",
      "sender_address": "audits@orchvate.in",
      "notification_email": "admin@orchvate.com",
      "notification_cc_email": "backup@orchvate.com",
      "notifications_enabled": true,
      "support_email": "support@orchvate.com"
    }
    ```
*   **Response (200 OK):** Current configuration status.

### 13.8 POST `/api/settings/notifications/toggle`
*   **Description:** Toggles email alerts for new submissions.
*   **Response (200 OK):** Updated settings object.

### 13.9 POST `/api/support`
*   **Description:** Sends a support request email from the admin page.
*   **Payload (JSON):**
    ```json
    {
      "name": "Alex Admin",
      "email": "alex@orchvate.com",
      "subject": "PostgreSQL Connection Timeouts",
      "message": "Encountering transient connection dropouts during peak loads."
    }
    ```
*   **Response (200 OK):** `{ "success": true }`

### 13.10 POST `/api/auth/verify`
*   **Description:** Verifies user authorization during Entra ID SSO.
*   **Payload (JSON):**
    ```json
    {
      "email": "aakash.padyachi@orchvate.com"
    }
    ```
*   **Response (200 OK):**
    ```json
    {
      "authorized": true,
      "role": "super"
    }
    ```

### 13.11 GET & POST `/api/manage/users`
*   **Description:** Manages administrator accounts.
*   **Payload (POST JSON):**
    ```json
    {
      "email": "new.admin@orchvate.com",
      "role": "admin"
    }
    ```
*   **Response (200 OK):** List of users or details of the newly created account.

---

## 14. Database Schema Specification

NeuroMark uses a relational database schema designed for PostgreSQL.

### 14.1 Table: `submissions`
Stores demographic information, raw question responses, calculations, and report details.

```sql
CREATE TABLE submissions (
    id                SERIAL PRIMARY KEY,
    submitted_at      TIMESTAMP DEFAULT NOW(),
    name              VARCHAR(255) NOT NULL,
    company_name      VARCHAR(255) NOT NULL,
    email             VARCHAR(255) NOT NULL,
    contact_number    VARCHAR(50),
    designation       VARCHAR(255),

    -- Raw answers Q5–Q44
    q5  VARCHAR(20), q6  VARCHAR(20), q7  VARCHAR(20), q8  VARCHAR(20), q9  VARCHAR(20),
    q10 VARCHAR(20), q11 VARCHAR(20), q12 VARCHAR(20), q13 VARCHAR(20), q14 VARCHAR(20),
    q15 VARCHAR(20), q16 VARCHAR(20), q17 VARCHAR(20), q18 VARCHAR(20), q19 VARCHAR(20),
    q20 VARCHAR(20), q21 VARCHAR(20), q22 VARCHAR(20), q23 VARCHAR(20), q24 VARCHAR(20),
    q25 VARCHAR(20), q26 VARCHAR(20), q27 VARCHAR(20), q28 VARCHAR(20), q29 VARCHAR(20),
    q30 VARCHAR(20), q31 VARCHAR(20), q32 VARCHAR(20), q33 VARCHAR(20), q34 VARCHAR(20),
    q35 VARCHAR(20), q36 VARCHAR(20), q37 VARCHAR(20), q38 VARCHAR(20), q39 VARCHAR(20),
    q40 VARCHAR(20), q41 VARCHAR(20), q42 VARCHAR(20), q43 VARCHAR(20), q44 VARCHAR(20),

    -- Section scores and levels
    lc_score INT,         lc_level VARCHAR(50),
    ro_score INT,         ro_level VARCHAR(50),
    we_score INT,         we_level VARCHAR(50),
    be_score INT,         be_level VARCHAR(50),
    tm_score INT,         tm_level VARCHAR(50),
    ca_score INT,         ca_level VARCHAR(50),
    pc_score INT,         pc_level VARCHAR(50),
    sp_score INT,         sp_level VARCHAR(50),

    -- Overall Metrics
    overall_avg   DECIMAL(4,2),
    overall_level VARCHAR(50),

    -- Email and status
    email_body    TEXT,
    status        VARCHAR(20) DEFAULT 'pending',
    sent_at       TIMESTAMP
);
```

### 14.2 Table: `app_settings`
A single-row configuration table containing app-wide settings.

```sql
CREATE TABLE app_settings (
    id                      INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    sender_name             VARCHAR(255) NOT NULL DEFAULT 'Orchvate',
    sender_address          VARCHAR(255) NOT NULL DEFAULT '',
    notification_email      TEXT NOT NULL DEFAULT '',
    notification_cc_email   TEXT NOT NULL DEFAULT '',
    notifications_enabled   BOOLEAN NOT NULL DEFAULT FALSE,
    support_email           VARCHAR(255) NOT NULL DEFAULT 'aakash.padyachi@rochvate.com',
    updated_at              TIMESTAMP DEFAULT NOW()
);
```

### 14.3 Table: `admin_users`
Stores authorized administrator accounts.

```sql
CREATE TABLE admin_users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    role          VARCHAR(50) NOT NULL DEFAULT 'admin',
    name          VARCHAR(255),
    password_hash VARCHAR(255),
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT NOW(),
    last_login    TIMESTAMP
);
```

### 14.4 Indexing Strategy
To optimize query performance as the database grows, the following indexes are configured:
```sql
CREATE INDEX idx_submissions_status ON submissions(status);
CREATE INDEX idx_submissions_email ON submissions(email);
CREATE INDEX idx_submissions_submitted_at ON submissions(submitted_at DESC);
CREATE INDEX idx_admin_users_email ON admin_users(email);
```

---

## 15. Security Architecture

NeuroMark implements a multi-layered security model to protect organizational data.

### 15.1 Authentication & MSAL Validation Flow
*   **OAuth2 Authorization:** Admin authentication is delegated to Microsoft Entra ID. No passwords are saved or verified locally by the application.
*   **Email Verification:** Once MSAL returns a valid profile, the backend verifies the returned email address against the database to confirm admin permissions.

### 15.2 Database and API Protection
*   **SQL Injection Prevention:** Database queries use parameterized inputs to prevent injection attacks.
*   **SSL Enforcements:** Database connections require SSL, encrypting all data in transit.
*   **CORS Policies:** CORS configurations restrict API access to trusted frontend origins during development, and enforce same-origin policies in production.

---

## 16. Accessibility (a11y) and UX Design System

Given that NeuroMark evaluates neurodiversity inclusion, its user interface is built to be accessible, clear, and easy to use.

### 16.1 Design Aesthetics
*   **Harmonious Color Palettes:** The interface uses high-contrast, soft color palettes (Orchvate Purples, Slate Greys, and Lime Green accents) that are visually distinct without being overwhelming.
*   **Typography:** The platform uses clean, modern fonts (**DM Sans** and **Playfair Display**) to ensure readability.
*   **Clean Layouts:** Grid alignments, generous spacing, and clear visual hierarchies help minimize cognitive load.

### 16.2 UI & UX Features
*   **Progress Tracking:** Step indicators and progress bars clarify the user's position in the assessment, reducing uncertainty.
*   **Visual Validation:** Clean, non-intrusive error highlights identify missing responses without creating user stress.
*   **Keyboard Navigation:** All button groups and inputs are accessible via keyboard controls.
*   **Screen Reader Support:** Standard semantic HTML tags and descriptive labels ensure compatibility with assistive technologies.
*   **Contextual Panels:** Sidebar tips explain why each section matters, helping users understand the purpose of the audit as they complete it.

---
*Document prepared for Orchvate internal reference and development use.*
