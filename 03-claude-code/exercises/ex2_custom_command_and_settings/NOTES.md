# Permissions rationale (Exercise 2, Part B, step 3)

Why each rule in `settings.json.example` is set the way it is:

- **`allow: Read(**)`** — reading files is low-risk (no side effects) and Claude needs
  to read constantly to do anything useful; gating every read behind a confirmation
  prompt would make the tool unusable in practice.
- **`allow` on test/read-only-git commands** (`pytest`, `npm test`, `git status`,
  `git diff`, `git log`) — none of these change any state; worst case they're slow or
  noisy, never destructive. Letting them run freely is what makes it practical for
  Claude to iterate (edit, test, re-edit) without a human approving every single test
  run.
- **`ask` on `git push`, `git rebase`, `git reset`** — these rewrite or move shared or
  local history. A bad `git push --force` or `git reset --hard` can destroy work that's
  expensive or impossible to recover, and the cost of asking (a few seconds of a human's
  attention) is small next to that risk. That's the justification for `ask` rather than
  `allow` — and rather than `deny`, since these are legitimate operations a developer
  does need sometimes, just ones that deserve explicit sign-off each time rather than
  running silently.
- **`ask` on `rm` and on writes under `**/migrations/**`** — file deletion and
  hand-editing of generated migrations are both hard to undo and easy to get subtly
  wrong (a hand-edited migration can silently diverge from the model it's supposed to
  represent). Neither is inherently forbidden, so `ask` rather than `deny`.
- **`deny` on reading `.env`, `.env.*`, and `secrets/**`** — these are the files most
  likely to hold live credentials. Unlike the `ask` cases, there's essentially no
  legitimate reason Claude needs the *contents* of a secrets file to do coding work, so
  this is blocked outright rather than left to a per-instance judgment call — the risk
  (a secret getting quoted back in a response, a log, or a commit) outweighs any
  plausible benefit.

The general pattern: **`allow`** = no meaningful downside to running it unsupervised;
**`ask`** = legitimate but high blast-radius or hard-to-reverse, so a human should be in
the loop each time; **`deny`** = no good reason Claude needs it at all, so don't even
offer the choice.
