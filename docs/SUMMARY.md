# NIWI — reconstruction summary

> Generated with `reconstruct@2.29.16` · mode `preserve` · level `complex` · fidelity `embed`

## Project
- **Stack:** Python · FastAPI
- **Notable libraries:** Playwright
- **Size:** 236 files · 62498 lines
- **Package manager(s):** npm, pip
- **Routes:** 80 · **Features:** 13

## Features (build order)
1. **Core** — Groups 16 file(s); routes: /, /audit. → `features/01-core/PRD.md` (16 file(s))
2. **Project Setup & Tooling** — 10 configuration/tooling file(s): build, lint, env, CI. → `features/02-project-setup/PRD.md` (10 file(s))
3. **Migrations** — Groups 23 file(s). → `features/03-migrations/PRD.md` (23 file(s))
4. **Sql** — Groups 5 file(s). → `features/04-sql/PRD.md` (5 file(s))
5. **Models** — Groups 4 file(s). → `features/05-models/PRD.md` (4 file(s))
6. **Utils** — Groups 4 file(s). → `features/06-utils/PRD.md` (4 file(s))
7. **Services** — Groups 16 file(s). → `features/07-services/PRD.md` (16 file(s))
8. **API** — Groups 8 file(s); routes: /api/admin/dashboard, /api/admin/submissions/dead-lettered, /api/admin/submissions/dead-lettered/replay-all, /api/admin/submissions/{submission_id}/replay, /api/auth/config, /api/auth/verify. → `features/08-api/PRD.md` (8 file(s))
9. **Frontend** — Groups 37 file(s). → `features/09-frontend/PRD.md` (37 file(s))
10. **Scripts** — Groups 15 file(s). → `features/10-scripts/PRD.md` (15 file(s))
11. **Tasks** — Groups 2 file(s). → `features/11-tasks/PRD.md` (2 file(s))
12. **Tests** — Groups 43 file(s). → `features/12-tests/PRD.md` (43 file(s))
13. **Documentation** — 4 documentation file(s). → `features/13-documentation/PRD.md` (4 file(s))

## Interface & data surface
- Routes resolved: 80
- Route candidates to verify: 32
- API candidates (RPC / GraphQL / gRPC / OpenAPI): 0
- Schema / data-model candidates: 35

## Unknowns to resolve
- The data model is not structured by the engine — extract entities, fields, types, and relations from `hints.schemaCandidates` into `architecture/DATA-MODEL.md`.
- Auth/middleware signals were found — read `hints.authCandidates` and record the auth rule per operation in the `architecture/INTERFACES.md` interface table's Auth column.
- Design-system source files were found (Tailwind/theme configs, token modules, global CSS) — capture the visual contract (tokens with their exact values, theming, typography, components, a11y) from `hints.designSystemCandidates` in `architecture/DESIGN-SYSTEM.md`.

## Next steps
Open `REBUILD.md` for the dependency-ordered build order and validation checklist, then feed each `features/<slug>/PRD.md` to an agent, using `data/` and `source/` as ground truth.
