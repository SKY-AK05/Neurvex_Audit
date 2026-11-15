# Interface surface

| Setting | Value |
| --- | --- |
| Mode | `preserve` |
| Level | `complex` |
| Fidelity | `embed` |
| Generated with | `reconstruct@2.29.16` |

The NIWI API contract is served via FastAPI with Pydantic serialization, SlowAPI rate limiting, Entra ID JWT verification, and standard HTTP error semantics.

## Resolved routes (deterministic — verify against source)

| Method | Kind | Route | Handler file |
| --- | --- | --- | --- |
| GET | api | `/` | `app/main.py:178` |
| GET | api | `/api/admin/dashboard` | `app/api/routes.py:2028` |
| GET | api | `/api/admin/submissions/dead-lettered` | `app/api/routes.py:1852` |
| POST | api | `/api/admin/submissions/dead-lettered/replay-all` | `app/api/routes.py:1965` |
| POST | api | `/api/admin/submissions/{submission_id}/replay` | `app/api/routes.py:1897` |
| GET | api | `/api/auth/config` | `app/api/routes.py:1669` |
| POST | api | `/api/auth/verify` | `app/api/routes.py:1682` |
| POST | api | `/api/book-call` | `app/api/routes.py:1535` |
| GET | api | `/api/drafts/resume` | `app/api/drafts.py:146` |
| POST | api | `/api/drafts/save` | `app/api/drafts.py:95` |
| DELETE | api | `/api/form/questions/{question_id}` | `app/api/form_builder.py:250` |
| PUT | api | `/api/form/questions/{question_id}` | `app/api/form_builder.py:221` |
| GET | api | `/api/form/sections` | `app/api/form_builder.py:106` |
| POST | api | `/api/form/sections` | `app/api/form_builder.py:136` |
| DELETE | api | `/api/form/sections/{section_id}` | `app/api/form_builder.py:182` |
| PUT | api | `/api/form/sections/{section_id}` | `app/api/form_builder.py:157` |
| POST | api | `/api/form/sections/{section_id}/questions` | `app/api/form_builder.py:200` |
| GET | api | `/api/health` | `app/main.py:124` |
| GET | api | `/api/health/cache-metrics` | `app/main.py:161` |
| GET | api | `/api/health/pool-metrics` | `app/main.py:154` |
| GET | api | `/api/manage/audit-logs` | `app/api/routes.py:1825` |
| GET | api | `/api/manage/orgs` | `app/api/orgs.py:125` |
| POST | api | `/api/manage/orgs` | `app/api/orgs.py:240` |
| POST | api | `/api/manage/orgs/create` | `app/api/orgs.py:307` |
| PATCH | api | `/api/manage/orgs/invitations/{invitation_id}` | `app/api/orgs.py:724` |
| POST | api | `/api/manage/orgs/invitations/{invitation_id}/regenerate` | `app/api/orgs.py:786` |
| POST | api | `/api/manage/orgs/invitations/{invitation_id}/revoke` | `app/api/orgs.py:759` |
| GET | api | `/api/manage/orgs/unlinked` | `app/api/orgs.py:322` |
| DELETE | api | `/api/manage/orgs/{org_id}` | `app/api/orgs.py:482` |
| GET | api | `/api/manage/orgs/{org_id}` | `app/api/orgs.py:360` |
| PUT | api | `/api/manage/orgs/{org_id}` | `app/api/orgs.py:395` |
| GET | api | `/api/manage/orgs/{org_id}/assessment-links` | `app/api/orgs.py:605` |
| POST | api | `/api/manage/orgs/{org_id}/assessment-links` | `app/api/orgs.py:561` |
| POST | api | `/api/manage/orgs/{org_id}/assessment-links/default` | `app/api/orgs.py:585` |
| DELETE | api | `/api/manage/orgs/{org_id}/assessment-links/{token_id}` | `app/api/orgs.py:632` |
| GET | api | `/api/manage/orgs/{org_id}/invitations` | `app/api/orgs.py:702` |
| POST | api | `/api/manage/orgs/{org_id}/invitations` | `app/api/orgs.py:652` |
| POST | api | `/api/manage/orgs/{org_id}/link` | `app/api/orgs.py:886` |
| PUT | api | `/api/manage/orgs/{org_id}/links/{submission_id}` | `app/api/orgs.py:845` |
| POST | api | `/api/manage/orgs/{org_id}/message` | `app/api/orgs.py:966` |
| GET | api | `/api/manage/orgs/{org_id}/report-preview` | `app/api/orgs.py:935` |
| POST | api | `/api/manage/orgs/{org_id}/restore` | `app/api/orgs.py:526` |
| PATCH | api | `/api/manage/orgs/{org_id}/status` | `app/api/orgs.py:444` |
| GET | api | `/api/manage/settings/rate-limits` | `app/api/routes.py:1480` |
| PUT | api | `/api/manage/settings/rate-limits` | `app/api/routes.py:1491` |
| POST | api | `/api/manage/settings/rate-limits/reset` | `app/api/routes.py:1516` |
| GET | api | `/api/manage/users` | `app/api/routes.py:1706` |
| POST | api | `/api/manage/users` | `app/api/routes.py:1721` |
| DELETE | api | `/api/manage/users/{email}` | `app/api/routes.py:1748` |
| GET | api | `/api/org/dashboard` | `app/api/org.py:140` |
| POST | api | `/api/org/register` | `app/api/org.py:27` |
| GET | api | `/api/org/verify` | `app/api/org.py:67` |
| POST | api | `/api/public/assessment/resolve-legacy-org` | `app/api/public.py:65` |
| POST | api | `/api/public/assessment/resolve-link` | `app/api/public.py:46` |
| POST | api | `/api/public/email/validate` | `app/api/public.py:100` |
| POST | api | `/api/public/invitations/validate` | `app/api/public.py:150` |
| POST | api | `/api/public/organisations/validate` | `app/api/public.py:110` |
| GET | api | `/api/settings` | `app/api/routes.py:1409` |
| PUT | api | `/api/settings` | `app/api/routes.py:1422` |
| POST | api | `/api/settings/delete-all-records` | `app/api/routes.py:1767` |
| POST | api | `/api/settings/notifications/toggle` | `app/api/routes.py:1449` |
| GET | api | `/api/settings/rate-limits` | `app/api/routes.py:1481` |
| PUT | api | `/api/settings/rate-limits` | `app/api/routes.py:1492` |
| POST | api | `/api/settings/rate-limits/reset` | `app/api/routes.py:1517` |
| GET | api | `/api/submissions` | `app/api/routes.py:404` |
| POST | api | `/api/submissions/filter` | `app/api/routes.py:506` |
| GET | api | `/api/submissions/saved-filters` | `app/api/routes.py:645` |
| POST | api | `/api/submissions/saved-filters` | `app/api/routes.py:685` |
| DELETE | api | `/api/submissions/saved-filters/{filter_id}` | `app/api/routes.py:736` |
| GET | api | `/api/submissions/{submission_id}` | `app/api/routes.py:883` |
| PUT | api | `/api/submissions/{submission_id}/email` | `app/api/routes.py:1210` |
| PATCH | api | `/api/submissions/{submission_id}/organisation` | `app/api/routes.py:1091` |
| POST | api | `/api/submissions/{submission_id}/regenerate-email` | `app/api/routes.py:1247` |
| PATCH | api | `/api/submissions/{submission_id}/respondent` | `app/api/routes.py:957` |
| PATCH | api | `/api/submissions/{submission_id}/scores` | `app/api/routes.py:998` |
| POST | api | `/api/submissions/{submission_id}/send` | `app/api/routes.py:1352` |
| GET | api | `/api/submissions/{submission_id}/status` | `app/api/routes.py:763` |
| POST | api | `/api/submit` | `app/api/routes.py:129` |
| POST | api | `/api/support` | `app/api/routes.py:1630` |
| GET | api | `/audit` | `app/main.py:170` |

## Interface table

| Method / Trigger | Path / Operation | Kind | Handler file | Auth | Notes & Side Effects |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/health` | HTTP REST | `app/main.py:124` | None | Returns `{status: "healthy", database: "connected"}`. Read-only. |
| GET | `/api/health/pool-metrics` | HTTP REST | `app/main.py:154` | None | Returns active, min, max, and available database connections. |
| POST | `/api/submit` | HTTP REST | `app/api/routes.py:129` | None (Public) | Ingests 44 assessment inputs. Atomic write to `raw_submissions` and `service_bus_outbox`. Returns HTTP 202 in <25ms with `submission_id`. |
| GET | `/api/submissions/{id}/status` | HTTP REST | `app/api/routes.py:763` | None (Public) | Checks ingestion state (`pending`, `completed`, `failed`) for client polling. |
| POST | `/api/drafts/save` | HTTP REST | `app/api/drafts.py:95` | None (Public) | Upserts partial survey answers to `draft_submissions`. Returns `resume_token`. |
| GET | `/api/drafts/resume` | HTTP REST | `app/api/drafts.py:146` | None (Public) | Queries `draft_submissions` by `resume_token`. Returns saved form answers. |
| POST | `/api/public/organisations/validate` | HTTP REST | `app/api/public.py:110` | None (Public) | Validates whether employer is registered and active in cached organization directory. |
| POST | `/api/public/assessment/resolve-link` | HTTP REST | `app/api/public.py:46` | None (Public) | Validates access token or invite code. Increments `use_count`. |
| GET | `/api/auth/config` | HTTP REST | `app/api/routes.py:1669` | None (Public) | Returns Entra ID public client credentials (tenantId, clientId, redirectUri). |
| POST | `/api/auth/verify` | HTTP REST | `app/api/routes.py:1682` | None (Public) | Verifies Bearer JWT signature via JWKS. Checks email in `admin_users`. Returns role and session. |
| GET | `/api/admin/dashboard` | HTTP REST | `app/api/routes.py:2028` | Bearer (admin) | Aggregated statistics: total submissions, score averages, pillar radar data, recent activity. |
| GET | `/api/admin/submissions/dead-lettered` | HTTP REST | `app/api/routes.py:1852` | Bearer (super) | Lists outbox messages in `failed` state with error tracebacks. |
| POST | `/api/admin/submissions/{id}/replay` | HTTP REST | `app/api/routes.py:1897` | Bearer (super) | Resets outbox status to `pending`, resets `retry_count=0`. Re-enqueues for processing. |
| POST | `/api/admin/submissions/dead-lettered/replay-all` | HTTP REST | `app/api/routes.py:1965` | Bearer (super) | Bulk re-enqueues all failed outbox submissions. |
| GET | `/api/manage/orgs` | HTTP REST | `app/api/orgs.py:125` | Bearer (admin) | Paginated list of organizations with response totals and inclusion maturity scores. |
| POST | `/api/manage/orgs` | HTTP REST | `app/api/orgs.py:240` | Bearer (admin) | Creates a new organization with unique name and domain. Inserts into `organizations`. |
| PUT | `/api/manage/orgs/{id}` | HTTP REST | `app/api/orgs.py:395` | Bearer (admin) | Updates organization details. Refreshes in-memory organization cache. |
| DELETE | `/api/manage/orgs/{id}` | HTTP REST | `app/api/orgs.py:482` | Bearer (super) | Soft deletes organization (`is_deleted=TRUE`). Purges active tokens. |
| POST | `/api/manage/orgs/{id}/assessment-links` | HTTP REST | `app/api/orgs.py:561` | Bearer (admin) | Generates a campaign token in `assessment_access_tokens` with optional max quota. |
| POST | `/api/manage/orgs/{id}/invitations` | HTTP REST | `app/api/orgs.py:652` | Bearer (admin) | Generates trackable invitation URL. Inserts into `organization_invitations`. |
| GET | `/api/submissions` | HTTP REST | `app/api/routes.py:404` | Bearer (admin) | Paginated list of audit submissions with filters (date range, score, organization, tier). |
| GET | `/api/submissions/{id}` | HTTP REST | `app/api/routes.py:883` | Bearer (admin) | Fetches complete scored submission breakdown and 40 Likert responses. |
| PATCH | `/api/submissions/{id}/organisation` | HTTP REST | `app/api/routes.py:1091` | Bearer (admin) | Reassigns submission to another organization. Writes audit trail to `submission_reassignments`. |
| POST | `/api/submissions/{id}/regenerate-email` | HTTP REST | `app/api/routes.py:1247` | Bearer (admin) | Re-renders HTML scorecard email and dispatches via Azure Communication Services. |
| GET | `/api/manage/users` | HTTP REST | `app/api/routes.py:1706` | Bearer (super) | Lists all authorized administrators and roles from `admin_users`. |
| POST | `/api/manage/users` | HTTP REST | `app/api/routes.py:1721` | Bearer (super) | Invites or adds a new administrator email with specified role. |
| DELETE | `/api/manage/users/{email}` | HTTP REST | `app/api/routes.py:1748` | Bearer (super) | Revokes administrator access. Deletes record from `admin_users` and cascades sessions. |
| POST | `/api/settings/delete-all-records` | HTTP REST | `app/api/routes.py:1767` | Bearer (super) | Destructive purge of non-production test data. Requires confirmation token. |
| GET | `/api/form/sections` | HTTP REST | `app/api/form_builder.py:106` | Bearer (admin) | Retrieves dynamic form sections and child questions for the survey editor. |
| PUT | `/api/form/questions/{id}` | HTTP REST | `app/api/form_builder.py:221` | Bearer (super) | Updates question text, order index, or required status. |
| POST | `/api/support` | HTTP REST | `app/api/routes.py:1630` | None (Public) | Logs inquiry into `support_requests` and triggers email to support team. |
| Cron (5s) | `outbox_dispatcher` | Daemon Job | `app/tasks/outbox_dispatcher.py` | System | Queries pending outbox entries using `SKIP LOCKED` and delegates to worker. |
| Daemon | `service_bus_worker` | Daemon Job | `app/tasks/service_bus_worker.py` | System | Consumes outbox events, calculates 8-pillar scores, updates DB, sends report email. |
