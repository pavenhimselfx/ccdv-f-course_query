# Solution — permissions rationale (Exercise 2, Part B, step 3)

Why each rule in `settings.json.example` is set the way it is:

- **`allow: Read(**)`** — reading files is low-risk (no side effects) and Claude needs
  to read constantly to do anything useful; gating every read behind a prompt would make
  the tool unusable.
- **`allow` on test/lint commands (`pytest`, `npm test`, `ruff check`, `eslint`) and
  read-only git commands (`status`, `diff`, `log`)** — these don't change any state;
  worst case they're slow or noisy, never destructive. Letting them run freely is what
  makes it practical to let Claude iterate (edit, test, re-edit) without a human
  approving every single test run.
- **`ask` on `git push`, `git rebase`, `git reset`** — these rewrite or move shared/
  local history. A bad `git push --force` or `git reset --hard` can destroy work that's
  expensive or impossible to recover, and the *cost* of asking (a few seconds of a
  human's attention) is small next to that risk. This is the core justification for not
  putting these in `allow`, and not blocking them outright in `deny` either — they're
  legitimate operations sometimes, just ones that deserve a human's explicit sign-off
  each time.
- **`ask` on `rm` and on writes under `**/migrations/**`** — file deletion and
  hand-editing of generated migrations are both hard to undo and easy to get subtly
  wrong (a hand-edited migration can silently diverge from the model it's supposed to
  represent). Neither is inherently forbidden, so `ask` rather than `deny`.
- **`deny` on reading `.env`, `.env.*`, and `secrets/**`** — these are the files most
  likely to contain live credentials. Unlike the `ask` cases, there's essentially no
  legitimate reason for Claude to need the *contents* of a secrets file to do coding
  work, so this is blocked outright rather than left to a per-instance judgment call —
  the risk (a secret ending up quoted back in a response, a log, or a commit) outweighs
  any plausible benefit.

The general pattern: **`allow`** = no meaningful downside to running it unsupervised;
**`ask`** = legitimate but high blast-radius or hard-to-reverse, so a human should be in
the loop each time; **`deny`** = no good reason for Claude to need it at all, so don't
even offer the choice.
