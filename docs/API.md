# API Reference

Base URL (local): `http://localhost:7071/api`

## POST /submit
Submit a completed audit form.

**Body:** JSON with respondent fields (`name`, `company_name`, `email`, `contact_number`) and answers `q5`–`q44` (`Yes` / `Partially` / `No` / `Not Sure`).

**Response:** `{ "success": true, "submission_id": 1 }`

---

## GET /submissions
Returns all submissions (list view).

**Response:** Array of `{ id, name, company_name, email, submitted_at, overall_avg, overall_level, status }`

---

## GET /submissions/{id}
Returns full detail for one submission including all scores and email body.

---

## PUT /submissions/{id}/email
Update the email draft before sending.

**Body:** `{ "email_body": "..." }`

---

## POST /submissions/{id}/send
Send the email via Azure Communication Services and mark as sent.

**Response:** `{ "success": true, "sent_at": "..." }`
