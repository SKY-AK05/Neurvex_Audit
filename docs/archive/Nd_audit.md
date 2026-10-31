# NeuroMark Audit Tool — Full Project Document

**Product:** Neurodiversity NeuroMark Audit Tool  
**Built for:** Orchvate  
**Version:** 2.0 (Web-based, Azure-backed)  
**Last Updated:** May 2026

---

## 1. What Are We Building

A web-based audit tool that allows organisations to self-assess their neurodiversity inclusion maturity. The user fills an HTML form with 40 questions across 8 segments. On submission, scores are calculated automatically, saved to a database, and a personalised email report is generated. An admin dashboard lets Orchvate review the scores and the draft email, make edits if needed, and then send the email to the respondent via Azure Communication Services.

This replaces the previous manual flow (Microsoft Forms → Excel download → Python script → manual email) with a fully automated, reviewer-controlled pipeline.

---

## 2. The Problem with the Old Flow

| Step | Old Way | Problem |
|---|---|---|
| Form | Microsoft Forms | No control over styling, no direct DB connection |
| Data | Downloaded as Excel manually | Manual, error-prone, not real-time |
| Scoring | Run Python script locally | Had to be done manually each time |
| Email | Copied and pasted from output file | No review step, no edit capability |
| Sending | Manual email | No tracking, no audit trail |

---

## 3. The New Flow (End to End)

```
[User fills HTML Form]
        ↓
[Submits form → POST to Azure Function]
        ↓
[Azure Function: scores all 8 sections instantly]
        ↓
[Saves everything to Azure PostgreSQL]
  - Respondent details
  - All 40 answers
  - 8 section scores + maturity levels
  - Overall average score + maturity level
  - Generated email body (editable draft)
  - Status: "pending"
        ↓
[Admin opens Dashboard (HTML)]
        ↓
[Dashboard fetches all submissions from Azure Function → PostgreSQL]
        ↓
[Admin clicks on a respondent → sees scores + email draft]
        ↓
[Admin edits email if needed → clicks Save]
        ↓
[Admin clicks "Send Email"]
        ↓
[Azure Function → Azure Communication Services (ACS)]
        ↓
[Email delivered to respondent]
        ↓
[Status updated to "sent" in DB]
```

---

## 4. Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Form (frontend) | HTML + CSS + Vanilla JS | Simple, no framework needed, works across org |
| Dashboard (frontend) | HTML + CSS + Vanilla JS | Same stack, easy to maintain |
| Backend / API | Azure Functions (Python) | Scoring logic already in Python, serverless = no server to manage |
| Database | Azure Database for PostgreSQL Flexible Server | Already provisioned, relational = easy to query and report on |
| Email delivery | Azure Communication Services (ACS) | Already in Azure ecosystem, reliable, trackable |
| Hosting (form + dashboard) | Azure Static Web Apps or Azure Blob Storage (static) | Simple HTML files, no server needed |

---

## 5. The Questionnaire Structure

The form has 44 fields total:

- **Q1–Q4:** Respondent details (Name, Company Name, Email, Contact Number)
- **Q5–Q44:** 40 audit questions across 8 sections, 5 questions each

### Sections and Question Mapping

| Section | Questions | Max Score |
|---|---|---|
| Leadership & Culture | Q5 – Q9 | 20 |
| Recruitment & Onboarding | Q10 – Q14 | 20 |
| Work Environment & Adjustments | Q15 – Q19 | 20 |
| Built Environment & Sensory | Q20 – Q24 | 20 |
| Talent Management & Development | Q25 – Q29 | 20 |
| Communication & Accessibility | Q30 – Q34 | 20 |
| Products & Customer Experience | Q35 – Q39 | 20 |
| Suppliers & Procurement | Q40 – Q44 | 20 |

Each question has 4 answer options: **Yes / Partially / No / Not Sure**

---

## 6. Scoring Logic

### Per-Answer Scoring

| Answer | Points |
|---|---|
| Yes | 4 |
| Partially | 2 |
| No | 0 |
| Not Sure | 0 |

### Per-Section Maturity Levels

Each section scores out of 20 (5 questions × 4 points max):

| Score Range | Maturity Level |
|---|---|
| 0 – 6 | Level 1 — Foundational |
| 7 – 14 | Level 2 — Early Progress |
| 15 – 20 | Level 3 — Developing |

### Overall Score

- Average of all 8 section scores
- Same 3-level maturity scale applied to the average
- A synopsis paragraph is selected based on the overall level

### Pre-written Interpretations

Each section has 3 pre-written interpretation texts (one per maturity level). The correct one is selected automatically based on the score and appended to the email. These are defined in the backend scoring function — same content as the existing `scoring_2.py`.

---

## 7. Database Schema

**Database name:** `nd_audit` (new database on existing PostgreSQL Flexible Server)

### Table: `submissions`

| Column | Type | Description |
|---|---|---|
| `id` | SERIAL PRIMARY KEY | Auto-increment unique ID |
| `submitted_at` | TIMESTAMP | When the form was submitted |
| `name` | VARCHAR(255) | Respondent name |
| `company_name` | VARCHAR(255) | Organisation name |
| `email` | VARCHAR(255) | Respondent email |
| `contact_number` | VARCHAR(50) | Optional phone number |
| `q5` – `q44` | VARCHAR(20) each | Raw answers for all 40 questions |
| `lc_score` | INT | Leadership & Culture score (0–20) |
| `lc_level` | VARCHAR(50) | Maturity level label |
| `ro_score` | INT | Recruitment & Onboarding score |
| `ro_level` | VARCHAR(50) | Maturity level label |
| `we_score` | INT | Work Environment & Adjustments score |
| `we_level` | VARCHAR(50) | Maturity level label |
| `be_score` | INT | Built Environment & Sensory score |
| `be_level` | VARCHAR(50) | Maturity level label |
| `tm_score` | INT | Talent Management & Development score |
| `tm_level` | VARCHAR(50) | Maturity level label |
| `ca_score` | INT | Communication & Accessibility score |
| `ca_level` | VARCHAR(50) | Maturity level label |
| `pc_score` | INT | Products & Customer Experience score |
| `pc_level` | VARCHAR(50) | Maturity level label |
| `sp_score` | INT | Suppliers & Procurement score |
| `sp_level` | VARCHAR(50) | Maturity level label |
| `overall_avg` | DECIMAL(4,2) | Average across all 8 sections |
| `overall_level` | VARCHAR(50) | Overall maturity level |
| `email_body` | TEXT | Full generated email (editable by admin) |
| `status` | VARCHAR(20) | `pending` or `sent` |
| `sent_at` | TIMESTAMP | When email was sent (null until sent) |

---

## 8. Azure Functions (Backend API)

Four functions, all in Python:

### `POST /api/submit`
- Receives form data (all 44 fields as JSON)
- Runs scoring logic (ported from `scoring_2.py`)
- Generates email body from pre-written interpretations
- Saves full record to `submissions` table with `status = pending`
- Returns: `{ success: true, submission_id: 123 }`

### `GET /api/submissions`
- Returns list of all submissions for the dashboard
- Fields returned: id, name, company_name, email, submitted_at, overall_avg, overall_level, status
- Dashboard uses this to populate the submissions table

### `PUT /api/submissions/{id}/email`
- Receives updated email body from admin
- Updates `email_body` in the DB for that submission
- Returns: `{ success: true }`

### `POST /api/submissions/{id}/send`
- Fetches the submission from DB
- Calls Azure Communication Services Email API
- Sends email to the respondent's email address
- Updates `status = sent` and `sent_at = now()` in DB
- Returns: `{ success: true, sent_at: "..." }`

---

## 9. HTML Form

**File:** `form.html`

### Fields
- Name (text, required)
- Company Name (text, required)
- Email (email, required)
- Contact Number (text, optional)
- Q5 to Q44: Radio button groups (Yes / Partially / No / Not Sure), all required

### Behaviour
- On submit: collects all field values, sends POST request to `/api/submit`
- Shows loading state while submitting
- On success: shows a thank-you message ("Your audit has been submitted. You will receive your results by email shortly.")
- On error: shows an error message with option to retry

---

## 10. Admin Dashboard

**File:** `dashboard.html`  
**Access:** Password-protected (simple JS-based gate or Azure Static Web Apps auth)

### Submissions List View
- Table showing all respondents: Name, Company, Email, Submitted date, Overall Score, Maturity Level, Status (Pending / Sent)
- Clicking a row opens the Detail View

### Detail View (per respondent)
- Respondent info at the top (name, company, email, contact)
- Score breakdown table: all 8 sections with score and maturity level
- Overall average score and maturity level
- Editable email body (textarea pre-filled with the generated draft)
- **Save Changes** button — saves edited email back to DB
- **Send Email** button — triggers ACS to send, updates status to Sent, disables the button

### Status Indicators
- `Pending` — email generated, not yet sent (yellow badge)
- `Sent` — email delivered (green badge), shows sent timestamp

---

## 11. Email Output Format

The generated email follows this structure (matching `Email.docx` sample):

```
Subject: NeuroMark Audit Results — [Company Name]

Dear [Name],

Thank you for completing the NeuroMark Audit for [Company Name]. 
Below is your breakdown and interpretation across the 8 key segments:

● Leadership & Culture: [Level] ([Score]/20)
   [Interpretation text]

● Recruitment & Onboarding: [Level] ([Score]/20)
   [Interpretation text]

... (all 8 sections) ...

========================================
OVERALL AUDIT SUMMARY
Average Score: [X.X]/20
Current Maturity: [Overall Level]

SYNOPSIS:
[Overall synopsis paragraph]
========================================

Best regards,
The Orchvate Team
```

---

## 12. Build Order (Recommended)

| Phase | What to Build | Why |
|---|---|---|
| 1 | PostgreSQL database + `submissions` table | Everything else depends on this |
| 2 | Azure Function: `submit` + scoring logic | Core of the product |
| 3 | HTML Form | Test end-to-end submission and scoring |
| 4 | Azure Function: `get_submissions` + `update_email` | Needed for dashboard |
| 5 | Admin Dashboard | Review and edit flow |
| 6 | ACS integration + `send` function | Final step, email delivery |
| 7 | Auth on dashboard | Security before go-live |

---

## 13. Key Decisions and Notes

- **Scoring is automatic on submission** — no manual trigger needed. By the time admin opens the dashboard, scores and email draft are already there.
- **Email is editable before sending** — the generated draft is a starting point. Admin can tweak wording per respondent before clicking Send.
- **Status tracking** — once sent, the Send button is disabled and the record is locked. Prevents accidental double-sends.
- **No auto-send** — email never fires without admin clicking the button. This is intentional and by design.
- **Named question fields** — the form uses `name="q5"` through `name="q44"` (not column indices like the old Excel approach). The backend maps by field name, not position.
- **Single database, new schema** — a new database `nd_audit` is created on the existing PostgreSQL Flexible Server. No changes to other databases on the same server.
- **ACS sender address** — needs to be a verified domain/address in your ACS resource before sending works.

---

## 14. Files to Be Created

| File | Type | Purpose |
|---|---|---|
| `form.html` | HTML | User-facing audit questionnaire |
| `dashboard.html` | HTML | Admin review and send interface |
| `function_app.py` | Python | All 4 Azure Functions |
| `scoring.py` | Python | Scoring logic (imported by function_app) |
| `requirements.txt` | Text | Python dependencies for Azure Functions |
| `host.json` | JSON | Azure Functions configuration |
| `create_table.sql` | SQL | PostgreSQL table creation script |

---

*Document prepared for Orchvate internal development use.*