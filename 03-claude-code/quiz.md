# Quiz — Domain 3: Claude Code Operation

**These are original practice questions written for this self-study course. They are
not real CCDV-F exam questions, are not sourced from Anthropic, and are not guaranteed
to match the style, difficulty, or content of the actual exam.** They exist to check
your understanding of this module's material.

Each question states how many answers to select. Work through all six before checking
the answer key at the bottom.

---

### Q1. (Select 1)

A developer runs Claude Code inside `~/projects/shop/checkout/`, a subdirectory of a
larger repository. The repo root has a `CLAUDE.md` describing company-wide Python style
rules. The `checkout/` directory has its own `CLAUDE.md` stating: "This module still
targets Python 3.8 for a legacy compatibility reason — do not use walrus operators or
other 3.9+ syntax here, even though the rest of the repo targets 3.11."

What should Claude Code do when editing a file inside `checkout/`?

A. Ignore the root `CLAUDE.md` entirely, since a nested `CLAUDE.md` exists and takes
full precedence.
B. Ignore the `checkout/CLAUDE.md`, since the root `CLAUDE.md` represents the
company-wide standard and should always win.
C. Apply both files' guidance, following the root file's general style conventions but
deferring to `checkout/CLAUDE.md`'s more specific Python-version constraint for code
in that directory.
D. Prompt the user to pick one file to follow for the entire session, since the two
files conflict.

---

### Q2. (Select 1)

A team wants to run Claude Code as part of a nightly CI job that automatically drafts a
changelog entry from the day's merged commits, with no person available to interact with
it, and wants the job's output captured as plain text in a log file.

Which Claude Code feature is most directly relevant to enabling this use case?

A. Streaming mode
B. Headless mode
C. Agent Memory
D. The CLAUDE.md hierarchy

---

### Q3. (Select 2)

A developer is comparing two Claude Code concepts: a **Skill** and a **subagent
(Agent)**. Which two statements correctly distinguish them?

A. A Skill is a packaged, reusable set of instructions Claude loads when the current
task matches what it's for; a subagent is a delegate worker that can execute a bounded
piece of work independently and report back.
B. Skills and subagents are two names for the exact same mechanism, differing only in
which CLI version introduced the term.
C. A subagent's main purpose is to help manage context by handling a self-contained
sub-task (e.g., a codebase search) without consuming the main session's full context
budget on that sub-task's details.
D. A Skill can only be triggered by a slash command and never activates automatically
based on the task at hand.

---

### Q4. (Select 1)

A repository has never had Claude Code configured for it before. A developer runs
Claude Code's repository initialization command for the first time in that repo.

Which outcome best describes what that command is expected to do?

A. It immediately opens pull requests against every file in the repo to bring them up to
a standard style.
B. It scans the codebase, generates a starting `CLAUDE.md` describing what it found
(stack, how to test/build, notable conventions), and sets up local configuration for the
project — as a first draft the developer is expected to review and refine.
C. It deletes any existing `CLAUDE.md` files in the repo and replaces them with a
single, final, non-editable configuration.
D. It requires an active Anthropic Console billing account separate from Claude Code's
own authentication before it can run at all.

---

### Q5. (Select 1)

A team has configured `settings.json` so that Claude Code can run `pytest` and read any
file without asking, but must prompt for confirmation before running `git push
--force` or deleting a file, and is blocked outright from reading anything under a
`secrets/` directory. They now want to enable **auto-mode** so Claude proceeds through
routine multi-step tasks without stopping to confirm each one.

What is the most accurate statement about the relationship between this `settings.json`
configuration and auto-mode?

A. Auto-mode overrides `settings.json`'s permission rules, so once auto-mode is on, the
`ask` and `deny` rules no longer have any effect.
B. Auto-mode is unrelated to `settings.json`; permissions only matter in interactive
mode.
C. Auto-mode's reduced-confirmation behavior operates within the boundaries the
permissions configuration already sets — actions marked to require confirmation or
marked denied are what keep auto-mode safe to enable, rather than something auto-mode
bypasses.
D. Enabling auto-mode requires removing the `deny` section from `settings.json`, since
denied actions and auto-mode are mutually exclusive features.

---

### Q6. (Select 1)

A developer wants to define a reusable shortcut so that typing `/write-tests` always
sends Claude a detailed, consistent prompt asking it to write unit tests for whatever
file is currently open, following the team's testing conventions — without the
developer retyping those instructions every time.

Which Claude Code core component is this describing?

A. Agent Memory
B. A Rule
C. A custom slash command
D. A built-in slash command

---

## Answer key and rationale

**Q1: C.** The CLAUDE.md hierarchy combines general and specific scopes rather than
having one file fully override the other; the more specific (nested) file's guidance
wins for the location it applies to, while broader conventions from the root file still
apply wherever the nested file is silent. A and B each incorrectly treat this as
all-or-nothing; D invents a "prompt the user" behavior the hierarchy doesn't require —
Claude is expected to layer the guidance itself.

**Q2: B.** Headless mode is exactly this: a non-interactive, scriptable way of invoking
Claude Code suited to automation and CI, where the tool runs a task and exits with no
human in the loop. Streaming mode (A) is about how output is delivered as it's produced,
not about whether a human is present. Agent Memory (C) is about persisting context
across sessions, not about non-interactive invocation. The CLAUDE.md hierarchy (D)
configures standing instructions, not the interactive-vs-scripted mode of invocation.

**Q3: A and C.** A Skill is a packaged, reusable instruction set invoked for a matching
class of task; a subagent is a delegate that executes a bounded piece of work and
reports back, which helps keep the main session's context focused (C is a correct
elaboration of that same idea). B is wrong — they are distinct components with distinct
purposes. D is wrong — nothing in the material restricts Skills to only being triggered
by an explicit slash command; the described behavior is Claude reaching for a Skill
automatically when the task matches, not a command mechanic.

**Q4: B.** Repository initialization is described as scanning the codebase and producing
a starting `CLAUDE.md` plus local project configuration — a first draft meant to be
reviewed and edited, not a finished or final artifact. A, C, and D all describe behavior
well beyond (or unrelated to) what an init-style command conceptually does.

**Q5: C.** Auto-mode reduces how often Claude Code stops to ask for confirmation, but it
operates inside the permission boundaries `settings.json` already defines — `ask` and
`deny` rules are precisely what make it reasonable to turn reduced-confirmation
operation on in the first place. A, B, and D each describe auto-mode as bypassing or
being disconnected from the permissions configuration, which inverts the actual
relationship described in this module.

**Q6: C.** A named, reusable prompt shortcut invoked by typing `/name`, defined by the
user/team for a project-specific need, is a custom slash command. A Rule (B) is a
standing constraint that applies automatically across a session rather than something
explicitly invoked by name. Agent Memory (A) is about persisting context over time, not
defining a reusable prompt trigger. A built-in slash command (D) is one that ships with
Claude Code itself, not one the developer authors.
