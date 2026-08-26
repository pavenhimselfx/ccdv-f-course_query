# Solution — `/review-pr` command design

Worked example for Exercise 2, Part A.

## Name

`/review-pr`

## One-line description

"Review the current diff against main for missing tests, unclear naming, and obvious
security issues, and summarize findings by severity."

## Intended usage

Typed by a developer after they've finished a change locally, before opening a pull
request (or right after opening one) — a self-review pass that catches obvious problems
before a human reviewer spends time on them. Takes one optional argument: a base branch
to diff against (defaults to `main` if omitted), e.g. `/review-pr develop`.

## The prompt/instructions it runs

```
You are performing a pre-submission code review of the current branch's changes against
{{base_branch, default: main}}.

1. Get the diff between the current branch and {{base_branch}}.
2. Read enough surrounding context (not just the diff lines) to actually judge each
   change, not just pattern-match on the diff text.
3. Check for, specifically:
   - Missing or inadequate test coverage for new/changed logic.
   - Unclear naming (variables, functions, files) that would slow a reviewer down.
   - Obvious security concerns: secrets or credentials committed, unsanitized input
     reaching a shell command / SQL query / template, missing auth checks on new
     endpoints.
   - Whether the diff's actual content matches what the PR title/description (if any)
     claims it does.
   - Leftover debug code (print statements, commented-out blocks, TODOs without
     context).
4. Do NOT rewrite or fix anything automatically. This command only reports findings.
5. Output a bulleted list grouped under three headings, in this order: "Blocking"
   (should not merge as-is), "Should fix" (real but non-blocking), "Nit" (optional
   polish). Under each finding, name the file and rough location, and explain the
   concern in one or two sentences. If a category has nothing to report, state that
   explicitly rather than omitting the heading.
```

## What it should explicitly not do

- Does not push commits, open a PR, or post a comment on an existing PR — it only prints
  the review to the terminal for the developer to read and act on themselves.
- Does not silently auto-fix anything it finds — a human decides what to do with each
  finding.
- Does not require a hosted PR to exist; it works purely off the local diff, so it's
  useful before a PR is even opened.

## Design notes (why it's shaped this way)

- **Single, bounded job.** It reviews and reports — it doesn't also try to fix, format,
  or submit. Keeping it read-only makes it safe to run under auto-mode without extra
  permission prompts, since it never needs write access to git remotes or the PR host.
- **Explicit output shape.** Grouping by severity (Blocking / Should fix / Nit) makes
  the output predictable and easy to scan, and easy for a human to decide "do I need to
  fix this before I ask for review, or can it wait."
- **Optional argument with a sane default.** Most of the time the base branch is `main`,
  so requiring the argument every time would be friction; but letting it be overridden
  covers repos with a different default branch or long-lived release branches.
