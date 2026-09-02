# Domain 3 Quiz — My Results (2026-09-02)

Score: 5/6. See `quiz.md` for the original questions and the course's own
answer key/rationale — this file is my personal answer log plus reasoning
for each question, including why the one miss was wrong.

| Q | My answer | Correct | Result |
|---|-----------|---------|--------|
| 1 | A | C | ❌ |
| 2 | B | B | ✅ |
| 3 | A, C | A, C | ✅ |
| 4 | B | B | ✅ |
| 5 | C | C | ✅ |
| 6 | C | C | ✅ |

---

**Q1 — Nested CLAUDE.md (checkout/, pinned to Python 3.8) vs. root CLAUDE.md
(company-wide style, Python 3.11).** Answered A ("ignore the root
CLAUDE.md entirely, since a nested one exists"). Correct: **C** — apply
both, with the nested file winning only for what it specifically
addresses (the Python-version constraint), while the root file's general
style conventions still apply everywhere the nested file is silent. This
is the exact same precedence question as
[../03-claude-code/exercises/ex1_claude_md_hierarchy](exercises/ex1_claude_md_hierarchy/my_reasoning.md)'s
Task 4 — and I got the underlying logic right when I built that exercise
myself (root's global rules still apply in `backend/`; only the specific
`Legacy/` formatting override wins locally, not a wholesale replacement).
The trap here is treating "a nested file exists" as "the nested file wins
on everything" rather than "the nested file wins only on what it actually
takes a position on."

**Q2 — CI job needs to run Claude Code non-interactively, no human
available, plain-text log output.** Answered B (headless mode) — correct.
Headless mode is exactly a non-interactive, scriptable invocation suited to
automation/CI, running a task and exiting with no human in the loop.
Streaming mode is about *when* output is delivered, not whether a human is
present; Agent Memory is about persisting context across sessions, not
invocation mode; the CLAUDE.md hierarchy configures standing instructions,
unrelated to interactive-vs-scripted invocation.

**Q3 — Skill vs. subagent, pick 2 distinguishing statements.** Answered A,
C — correct. A Skill is a packaged, reusable instruction set Claude loads
when the current task matches what it's for; a subagent is a delegate that
executes a bounded piece of work independently and reports back (A). A
subagent's main purpose is managing context — handling a self-contained
sub-task like a codebase search without spending the main session's full
context budget on that sub-task's details (C). Rejected: they are not the
same mechanism under different names (B), and nothing restricts Skills to
slash-command-only activation — the whole point is Claude reaching for one
automatically when the task matches (D).

**Q4 — What does Claude Code's repo-init command actually do on a
never-configured repo?** Answered B — correct. It scans the codebase and
produces a starting CLAUDE.md (stack, test/build commands, notable
conventions) plus local project configuration — a first draft meant to be
reviewed and refined, not a finished, destructive, or billing-gated action.
The wrong options each invented behavior well beyond what an init-style
command conceptually does (mass PRs, deleting/replacing existing config
non-editably, requiring separate Console billing).

**Q5 — Relationship between settings.json permissions and auto-mode.**
Answered C — correct. Auto-mode reduces how often Claude Code stops to
confirm routine steps, but it operates *within* the boundaries
settings.json already sets — `ask` and `deny` rules are precisely what
make it safe to enable reduced-confirmation operation in the first place,
not something auto-mode overrides or is disconnected from. The wrong
options all invert this relationship (auto-mode overriding permissions,
being unrelated to them, or requiring `deny` to be removed).

**Q6 — Reusable `/write-tests` shortcut sending a consistent detailed
prompt.** Answered C (a custom slash command) — correct. A named, reusable
prompt shortcut invoked by typing `/name`, authored by the user/team for a
project-specific need, is exactly what a custom slash command is. A Rule
is a standing constraint applied automatically across a session rather
than explicitly invoked by name; Agent Memory persists context over time,
not a prompt trigger; a built-in slash command ships with Claude Code
itself rather than being authored by the developer.

---

## Pattern to remember

The one miss repeats a trap I'd already correctly avoided once in
practice: **"a more specific scope exists" is not the same as "the more
specific scope wins on everything."** A nested CLAUDE.md (or, by the same
logic, any more-specific config layered over a general one) only overrides
what it explicitly takes a position on — general rules from the broader
scope keep applying wherever the specific one is silent. This is the same
family of trap flagged in [../01-agents-and-workflows/quiz-results.md](../01-agents-and-workflows/quiz-results.md)
and [../02-applications-and-integration/quiz-results.md](../02-applications-and-integration/quiz-results.md):
an answer that's too absolute ("ignore entirely," "always wins") is a
strong signal to re-check whether the real rule is actually a combination/
layering rule instead.
