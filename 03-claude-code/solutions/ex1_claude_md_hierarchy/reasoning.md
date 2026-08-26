# Solution — reasoning write-up (Exercise 1, step 4)

This is the worked example of `my_reasoning.md`, reasoning about the sample
`sample_root_CLAUDE.md` and `sample_backend_CLAUDE.md` in this folder, for the fictional
`fake_repo` (a Django `backend/` + React `frontend/` project).

**1. Working inside `fake_repo/frontend/`:** only the root `fake_repo/CLAUDE.md`
applies. `backend/CLAUDE.md` is scoped to the `backend/` subtree and has no bearing on
work happening in `frontend/` — it would be noise (and in places actively wrong, e.g.
its 2-space indentation exception) if it applied there. If there were also a
`fake_repo/frontend/CLAUDE.md`, that would apply too, layered on top of the root file,
the same way `backend/CLAUDE.md` layers onto the root file when working in `backend/`.

**2. Working inside `fake_repo/backend/`:** both `fake_repo/CLAUDE.md` (root) and
`fake_repo/backend/CLAUDE.md` (nested) apply. They combine rather than one replacing the
other. Where they conflict, the more specific file — `backend/CLAUDE.md`, since it's
closer to where the work is actually happening — should win for that location. General
project-wide defaults still hold anywhere the nested file is silent (e.g. the commit
message conventions, which `backend/CLAUDE.md` never mentions, still apply in
`backend/`).

**3. Concrete conflicting example:** root says "4-space indentation everywhere... unless
a subsystem's own CLAUDE.md says otherwise"; `backend/CLAUDE.md` says "match the
existing 2-space style inside `legacy_sms_client/`." Inside
`backend/integrations/legacy_sms_client/` specifically, the nested rule should win — and
notice the root file even anticipates and explicitly permits this kind of override,
which is good practice: a root CLAUDE.md that acknowledges subsystems may need
exceptions is easier to extend consistently than one that's silent on the question and
leaves Claude to guess which file "wins." Outside that one folder but still within
`backend/`, the general 4-space rule still applies, since nothing in
`backend/CLAUDE.md` says otherwise there.

**4. Why combine instead of full replacement:** most of what's in a root CLAUDE.md
(overall stack, test/lint commands that touch the whole repo, git conventions, broad
"do not touch" lists like `.env`) is still true and still useful no matter which
subdirectory Claude is working in. If a nested CLAUDE.md fully replaced the root file
instead of adding to it, every subsystem's file would have to re-state all of that
shared context to avoid losing it — repetitive, and it guarantees the copies drift out
of sync as the project evolves. Combining lets each nested file stay short and focused
only on what's genuinely different about that part of the tree, while the root file
remains the single source of truth for anything project-wide.
