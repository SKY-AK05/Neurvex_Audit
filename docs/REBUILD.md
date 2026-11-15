# REBUILD — NIWI

| Setting | Value |
| --- | --- |
| Mode | `preserve` |
| Level | `complex` |
| Fidelity | `embed` |
| Generated with | `reconstruct@2.29.16` |

This folder is a complete plan to rebuild the project from scratch.

## Mode & level

- **preserve**: keep the current architecture.
- **complex**: PRDs that also suggest improvements to fold in.
- **embed** fidelity: key code embedded directly in the PRDs.

## Build order

Ordered by dependency tier — foundations (types, data, shared UI, i18n, cross-cutting) first, feature pages next, tests & docs last.

1. [ ] **Core** → `features/01-core/PRD.md`
2. [ ] **Project Setup & Tooling** → `features/02-project-setup/PRD.md`
3. [ ] **Migrations** → `features/03-migrations/PRD.md`
4. [ ] **Sql** → `features/04-sql/PRD.md`
5. [ ] **Models** → `features/05-models/PRD.md`
6. [ ] **Utils** → `features/06-utils/PRD.md`
7. [ ] **Services** → `features/07-services/PRD.md`
8. [ ] **API** → `features/08-api/PRD.md`
9. [ ] **Frontend** → `features/09-frontend/PRD.md`
10. [ ] **Scripts** → `features/10-scripts/PRD.md`
11. [ ] **Tasks** → `features/11-tasks/PRD.md`
12. [ ] **Tests** → `features/12-tests/PRD.md`
13. [ ] **Documentation** → `features/13-documentation/PRD.md`

## Procedure

1. Start with `00-overview/PRD.md`, `architecture/ARCHITECTURE.md`, `architecture/INTERFACES.md`, and `architecture/DATA-MODEL.md`.
2. For each unit in order, open its PRD and implement it.
3. Wire shared data from `data/` (translations, schema, config).
4. Validate behavior against the requirements in each PRD.
5. Run the project's own scripts to verify: `dev`, `api`, `ui`.

## Validation checklist

- [ ] Every interface in `architecture/INTERFACES.md` is implemented (routes, endpoints, RPC/GraphQL, jobs).
- [ ] Data model matches `architecture/DATA-MODEL.md` and `data/schema/`.
- [ ] All routes respond as before.
- [ ] UI matches `architecture/DESIGN-SYSTEM.md` — design tokens reproduced exactly, components built with their variants/states, and the accessibility target met.
- [ ] Required env vars configured: `ACS_CONNECTION_STRING`, `ACS_SENDER_ADDRESS`, `ACS_SENDER_NAME`, `APP_ENV`, `CORS_ORIGINS`, `DELETE_ALL_PASSWORD`, `ENABLE_DEV_BYPASS`, `ENABLE_EMBEDDED_WORKER`, `ENABLE_LEGACY_JOB_WORKER`, `ENABLE_SERVICE_BUS_PIPELINE`, `ENTRA_CLIENT_ID`, `ENTRA_TENANT_ID`, `ENVIRONMENT`, `FRONTEND_URL`, `HUBSPOT_ACCESS_TOKEN`, `JWT_SECRET`, `KEY_VAULT_NAME`, `NIWI_BLOCKED_EMAIL_DOMAINS`, `NIWI_ORG_CACHE_INVALIDATION_FILE`, `NIWI_RATE_LIMIT_INVALIDATION_FILE`, `OUTBOX_BATCH_SIZE`, `OUTBOX_POLL_INTERVAL`, `PGDATABASE`, `PGHOST`, `PGOPTIONS`, `PGPASSWORD`, `PGPORT`, `PGUSER`, `PUBLIC_VALIDATE_LIMIT`, `REQUIRE_KEYVAULT`, `SERVICE_BUS_BATCH_SIZE`, `SERVICE_BUS_CONCURRENCY`, `SERVICE_BUS_CONNECTION_STRING`, `SERVICE_BUS_ENABLED`, `SERVICE_BUS_FQDN`, `SERVICE_BUS_LOCK_DURATION_SECONDS`, `SERVICE_BUS_MAX_DELIVERY_COUNT`, `SERVICE_BUS_QUEUE_NAME`, `SERVICE_BUS_RECEIVE_WAIT_TIME`, `SUPPORT_EMAIL`, `TESTING`, `VITE_API_BASE`, `VITE_APP_URL`, `VITE_MSAL_CLIENT_ID`, `VITE_MSAL_TENANT_ID`.
