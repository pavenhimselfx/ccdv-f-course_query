# Exercise 2 — Custom Slash Command + settings.json

**Type:** File/config exercise. No API key required. If you have Claude Code installed,
the optional last step lets you try wiring the command up for real.

## Goal

1. Design a custom slash command (`/review-pr`) at a conceptual level — what it's called,
   what it does, and what prompt/instructions it runs.
2. Draft an example `settings.json` with a permissions section and one hook, and explain
   what each field is for.

## Background

Custom slash commands are reusable prompt shortcuts you define for your own project or
workflow — see the README's "Commands" and "Built-in vs. custom slash commands"
sections. `settings.json` is where Claude Code's *behavior* is configured — permissions
(what it may do without asking), hooks (commands that run automatically at points in its
lifecycle), model settings, and related configuration — see the README's `settings.json`
section.

## Part A — Design `/review-pr`

Write a file `review_pr_command.md` in this folder describing the command as if you were
specifying it for someone else to implement. Cover:

1. **Name** — the slash command's invocation, e.g. `/review-pr`.
2. **One-line description** — what a user sees when browsing available commands.
3. **Intended usage** — when would someone type this? What arguments, if any, might it
   take (e.g., a PR number, a branch name, or "the currently-diffed changes")?
4. **The prompt/instructions it runs** — write out, in full, the instruction text you'd
   want this command to send to Claude. Be concrete: what should it check for (e.g.,
   missing tests, unclear naming, security concerns, whether the diff matches the PR
   description), and what format should its output take (e.g., a bulleted list grouped
   by severity)?
5. **Anything it should explicitly *not* do** — e.g., "does not push commits or comment
   on the PR itself, only prints a review to the terminal."

Think of this the way you'd think of designing a good function: a clear name, a single
well-defined job, explicit inputs, and a predictable output shape.

## Part B — Draft a settings.json

Open `settings.json.example` in this folder — it's a skeleton with comments explaining
each section, and a couple of `___FILL_ME_IN___` placeholders. Your job:

1. Fill in the `permissions` section with rules that would make sense for a team that
   wants Claude Code to be able to run tests and read files freely, but must always ask
   before running anything that touches git history (force-push, rebase) or before
   deleting files.
2. Fill in the one example hook so that it runs a formatter (e.g., `black` or `prettier`,
   pick one appropriate to a language you know) automatically after Claude edits a file.
3. In a short paragraph at the bottom of the file (as a JSON comment or in a companion
   note — JSON doesn't support comments natively, so either keep the placeholder's
   comment-via-underscore-key convention or add a short `NOTES.md` alongside it), explain
   *why* you set the permissions the way you did — what's the risk you're guarding
   against for each rule?

## Part C — (If you have Claude Code installed) Try it for real

Check the current Claude Code docs for the actual, current file locations and JSON shape
for custom commands and `settings.json` — these details move between releases, which is
why this exercise has you design conceptually first. If you want to go further, try
creating a real custom command and a real `settings.json` permissions rule in a scratch
project, and confirm the behavior matches what you designed.

## Check your work

Compare against `../../solutions/ex2_custom_command_and_settings/`. As with Exercise 1,
there's no single correct answer — what matters is that your command has a clear,
bounded job and your permission rules map to a concrete, articulable risk.
