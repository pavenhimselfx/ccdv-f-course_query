# Example nested CLAUDE.md (for reference — read before writing your own)

This is an illustrative example of what a **nested subdirectory** `CLAUDE.md` might look
like — in this case, for a `backend/` folder inside the same fictional monorepo whose
root file is shown in `sample_root_CLAUDE.md`. Notice how it doesn't repeat the root
file's rules (running tests, code style, commit conventions) — it only adds detail that
is specific to this subsystem. Don't copy it verbatim — write your own for
`fake_repo/backend/CLAUDE.md`.

---

# Backend-specific notes (applies within backend/)

These notes are in addition to the project-wide conventions in the repo-root
`CLAUDE.md`. If anything here conflicts with the root file, follow this file for work
happening inside `backend/`.

## Structure

- `backend/app/api/` — route handlers, one file per resource.
- `backend/app/models/` — SQLAlchemy ORM models.
- `backend/app/services/` — business logic; route handlers should stay thin and delegate
  here.

## Testing this subsystem specifically

- `pytest backend/tests -x` runs just the backend suite (faster than the full `make
  test` while iterating).
- Tests that hit the database use a throwaway SQLite file, not Postgres — no setup
  needed to run them locally.

## Database conventions

- Every new table needs a corresponding Alembic migration — generate it with `alembic
  revision --autogenerate -m "..."` and review the generated file by hand before
  committing.
- All timestamps are stored in UTC; convert at the API boundary, never in the database
  layer.

## Exception to the root indentation rule

The `backend/app/legacy_billing/` folder wraps an old vendored client that uses 2-space
indentation throughout. Match that file's existing style within
`legacy_billing/` specifically, even though the rest of the backend uses standard
Black-formatted 4-space Python.

## Do not touch (in addition to the root-level list)

- `backend/app/legacy_billing/vendor_client.py` — untouched vendor code, kept as-is
  intentionally so upstream diffs stay applyable.
