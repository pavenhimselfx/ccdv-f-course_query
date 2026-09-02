# Reasoning: CLAUDE.md hierarchy

## 1. Working context inside `fake_repo/frontend/`

Only the **root** `fake_repo/CLAUDE.md` applies. `backend/CLAUDE.md` does not apply —
it's scoped to the `backend/` subtree, and `frontend/` is a sibling directory, not a
descendant of `backend/`. Claude Code discovers `CLAUDE.md` files by walking up from
(and within) the current working directory's tree, so a file that lives in an unrelated
sibling subtree is never in scope.

## 2. Working context inside `fake_repo/backend/`

**Both** files apply, combined: the root `CLAUDE.md` (stack, TDD, coverage, formatting,
git workflow) plus `backend/CLAUDE.md` (C#, feature-acceptance-criteria rule, test
command, migrations rule, the `Legacy/` formatting exception).

Precedence when they conflict: the **more specific (backend) file wins** for anything it
explicitly addresses. The root file still governs everything backend doesn't override.
This is the general pattern — nested scope refines/overrides the general one for work
happening in that location, rather than the two being independent or the nested file
replacing the general one wholesale.

## 3. A concrete conflict

- Root: "Format all C#/.NET code with `dotnet format` using the repo's default
  `.editorconfig` settings (4-space indentation, standard brace style) before
  committing."
- Backend: "The `Legacy/` folder wraps a vendored interop library and uses 2-space
  indentation to match that vendored code's style. Do not run `dotnet format` with
  default settings on files under `Legacy/`."

**Backend's rule wins** when Claude is working inside `backend/Legacy/`. Reasoning: the
backend rule isn't a random override, it's a *deliberate, documented exception* for a
specific, known local constraint (matching a vendored library's existing style) that the
root rule's author couldn't have anticipated when writing a project-wide default. The
person who wrote `backend/CLAUDE.md` had more context about `Legacy/` specifically than
whoever wrote the root-level formatting rule — that's exactly the situation nested scope
exists to handle. Outside `Legacy/`, elsewhere in `backend/`, the root formatting rule
still applies normally; the override is scoped to the specific subtree it names, not a
blanket "backend ignores root formatting" rule.

## 4. Why combine rather than replace?

Because most of what's in the root file is genuinely global and doesn't stop being true
just because Claude happens to be working in `backend/` right now — "Claude never runs
`git commit`/`git push` itself," "this project follows TDD," "minimum 80% coverage,"
"target .NET 8.0" all apply to backend work exactly as much as anywhere else. If a
nested `CLAUDE.md` fully *replaced* the root file instead of adding to it, every
subsystem would need to redundantly re-state every global rule just to keep it in
effect — and any of those copies could silently drift out of sync if the root policy
ever changed (e.g., if the coverage minimum moved to 85%, someone would have to
remember to update it in every subsystem's `CLAUDE.md` too). Combining lets the root
file stay the single source of truth for genuinely global policy, and lets nested files
stay small, focused only on what's actually different or additional in that subtree —
which is also just easier for a human to read and keep accurate, since a nested file
that only lists deltas is obviously scoped to "what's special about this place" rather
than being a full, easily-stale copy of everything.
