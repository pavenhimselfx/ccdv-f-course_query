# backend

Subsystem-specific notes for `backend/`. These are in addition to the project-wide
conventions in the root `CLAUDE.md`, which still applies here. If anything in this file
conflicts with the root file, follow this file for work happening inside `backend/`.

- The backend is written in **C#**.
- Every new feature needs a test with written acceptance criteria **before** it's
  implemented — not just "a test exists," but the acceptance criteria are written down
  first, then a test encodes them, then the implementation follows. This sharpens the
  root project's general TDD rule specifically for backend feature work.
- Run backend tests with `dotnet test Backend.Tests/Backend.Tests.csproj`.
- Never hand-edit files under `Migrations/`. Generate them with
  `dotnet ef migrations add <Name>` and review the generated file before committing.
- **Exception to the root formatting rule:** the `Legacy/` folder wraps a vendored
  interop library and uses **2-space indentation** to match that vendored code's style.
  Do not run `dotnet format` with default settings on files under `Legacy/` — format
  those files by hand to match the surrounding style instead.
