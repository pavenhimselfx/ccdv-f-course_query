# Solution — fake_repo/backend/CLAUDE.md

This is a worked example of the **nested** CLAUDE.md called for in Exercise 1, step 3 —
scoped to `fake_repo/backend/`, extending the root file in `../sample_root_CLAUDE.md`
(this is the solution's mirror of that root file).

---

# backend/ — subsystem notes

These apply in addition to the project-wide conventions in the repo-root CLAUDE.md, for
any work happening inside `backend/`. Where something here conflicts with the root file,
follow this file while working in `backend/`.

## Structure

- `backend/api/` — Django REST Framework viewsets, one module per resource.
- `backend/core/models.py` — the core Django ORM models; most business data lives here.
- `backend/integrations/` — thin wrappers around third-party APIs (payments, email).

## Testing this subsystem specifically

- `pytest backend/ -x -q` runs just the backend suite, faster than the full
  `test-all.sh` while iterating on backend-only changes.
- Backend tests use a disposable SQLite database automatically (see
  `backend/conftest.py`) — no separate Postgres setup needed to run them locally.

## Database conventions

- Every model change needs an accompanying migration generated with
  `manage.py makemigrations` — review the generated migration file before committing;
  don't hand-write migrations.
- All datetimes are stored and handled as UTC; convert to local time only in
  presentation code, never in models or querysets.

## Exception to the root indentation rule

`backend/integrations/legacy_sms_client/` vendors an old internal library that uses
2-space indentation. Match that existing style when touching files inside
`legacy_sms_client/` specifically — do not reformat it to 4-space to match the rest of
the backend.

## Do not touch (in addition to the root-level list)

- `backend/integrations/legacy_sms_client/vendor/` — untouched vendor snapshot, kept
  as-is so future upstream updates can be diffed cleanly.
