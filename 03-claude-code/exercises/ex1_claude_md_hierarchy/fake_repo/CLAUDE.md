# fake_repo

`fake_repo` is an internal order-tracking system: an ASP.NET Core Web API backend
(`backend/`) and a React frontend (`frontend/`), deployed as two separate services. This
file covers conventions that apply project-wide, no matter which part of the repo you're
working in — see `backend/CLAUDE.md` for backend-specific detail.

## Stack

- This project targets **.NET 8.0 (LTS)**. Don't change the target framework version
  without discussing it with the team first.

## Process: Test-Driven Development

- This project follows **TDD**: for any new behavior, write a failing test first, then
  write the implementation that makes it pass. Don't write production code before a
  test exists for it.
- Minimum **80% test coverage** across the solution. A change that drops overall coverage
  below 80% should not be merged.

## Formatting

- Format all C#/.NET code with `dotnet format` using the repo's default `.editorconfig`
  settings (4-space indentation, standard brace style) before committing.

## Git workflow

- Claude must **never** run `git commit` or `git push` itself. A human always reviews
  the diff and executes those commands.
- When asked to prepare a commit, Claude drafts the commit message for the human to
  review and use — Claude does not commit it themselves.

## Do not touch

- `appsettings.*.Production.json` and any `*.local.json` config file — these may contain
  connection strings or API keys; never read, print, or modify them.
- `bin/`, `obj/`, `node_modules/` — build output and installed dependencies, never
  hand-edited.
- Anything under `**/Migrations/` — see `backend/CLAUDE.md` for the correct way to
  generate these.
