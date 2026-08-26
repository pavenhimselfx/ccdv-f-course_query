# Solution — fake_repo/CLAUDE.md

This is a worked example of the **root** CLAUDE.md called for in Exercise 1, step 2 —
for a fictional `fake_repo` containing a `frontend/` and `backend/` service.

---

# fake_repo — project conventions

`fake_repo` is a two-service application: a Django backend (`backend/`) and a
React/Vite frontend (`frontend/`).

## Stack

- Backend: Python 3.12, Django, PostgreSQL.
- Frontend: TypeScript, React 18, Vite.
- Both services are deployed independently via Docker.

## Testing and linting

- Run `./scripts/test-all.sh` from the repo root before considering any change done —
  it runs both the backend (`pytest`) and frontend (`vitest`) suites.
- Run `./scripts/lint-all.sh` — runs `ruff` for Python and `eslint` for TypeScript. Treat
  every warning as something to fix, not suppress.

## Code style

- 4-space indentation everywhere, in both Python and TypeScript, unless a subsystem's
  own CLAUDE.md says otherwise.
- Type hints/types are required on all new functions in both languages.
- Prefer small, single-purpose functions and files over large ones.

## Git and commits

- Never commit directly to `main`; always work on a feature branch.
- Use conventional commit prefixes (`feat:`, `fix:`, `chore:`, `docs:`, `test:`).
- Never rewrite shared history (`push --force`, `rebase` on a shared branch) without
  being explicitly asked.

## Do not touch

- `**/migrations/` — Django migrations; regenerate with `manage.py makemigrations`
  rather than hand-editing.
- `.env`, `.env.*` — may contain secrets; never read, print, or modify.
- `frontend/node_modules/`, `backend/.venv/` — dependency directories, never edited by
  hand.
