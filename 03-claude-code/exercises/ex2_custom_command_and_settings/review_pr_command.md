# `/review-pr` command design

## Name

`/review-pr`

## One-line description

Reviews the current branch's diff against a base branch for missing tests, unclear
naming, and security concerns, grouped by severity.

## Intended usage

Run by a developer right before opening a PR, as a self-review pass to catch obvious
problems before a human reviewer spends time on them. Takes one optional argument: a
base branch to diff against (defaults to `main` if omitted), e.g. `/review-pr develop`.

## The prompt/instructions it runs

```
You are performing a pre-submission code review of the current branch's changes against
{{base_branch, default: main}}.

1. Get the diff between the current branch and {{base_branch}}.
2. Read surrounding file context where needed, not just the raw diff lines, so you can
   judge each change's intent rather than pattern-matching on diff text alone.
3. Check specifically for:
   - Missing or weak test coverage for new or changed logic.
   - Naming (variables, functions, files) that would slow a reviewer down.
   - Security concerns: hardcoded secrets/credentials, unsanitized input reaching a
     shell command, SQL query, or template, missing auth/permission checks on new
     endpoints.
   - Whether the diff's actual content matches the PR title/description, if one is
     available.
   - Leftover debug code: stray print/console.log statements, commented-out blocks,
     TODOs with no context.
   - Code smells: duplicated logic that should be extracted, a function/method doing
     too many unrelated things, deep nesting that could be flattened with early
     returns, magic numbers/strings that should be named constants, and dead code.
     Treat these as judgment calls, not objective defects -- when flagging one, name
     the specific readability/maintainability cost you expect it to cause, not just
     "this looks smelly."
4. Do not modify any files or fix anything automatically -- this command only reports
   findings.
5. Print findings as a bulleted list grouped under three headings, in this order:
   "Blocking" (should not merge as-is), "Should fix" (real but non-blocking), "Nit"
   (optional polish). Under each finding, name the file and approximate location, and
   explain the concern in one or two sentences. If a category has nothing to report,
   state that explicitly rather than omitting the heading. Code smells almost never
   belong under "Blocking" -- file them under "Should fix" if they're likely to cause
   real maintenance pain, otherwise "Nit."
```

## What it should explicitly not do

- Never pushes commits, opens a PR, or comments on an existing PR/issue -- it only
  prints the review to the terminal for the developer to read and act on themselves.
- Never silently rewrites or auto-fixes anything it finds -- a human decides what to do
  with each finding.
- Doesn't require a hosted PR to exist -- it works purely off the local diff, so it's
  useful even before a PR is opened.

## Design notes (why it's shaped this way)

- **Single, bounded job.** It reviews and reports -- it doesn't also try to fix, format,
  or submit. Keeping it read-only makes it safe to run without extra permission prompts,
  since it never needs write access to git remotes or a PR host.
- **Explicit output shape.** Grouping by severity makes the output predictable and easy
  to scan, and maps directly onto "must fix before requesting review" vs. "can wait."
- **Optional argument with a sane default.** Most repos diff against `main`, so
  requiring the argument every time would be friction, but allowing an override covers
  repos with a different default branch or long-lived release branches.
- **Code smells are explicitly marked as judgment calls, not objective defects.**
  Unlike "missing tests" or "hardcoded secret," a smell (duplication, a function doing
  too much, deep nesting) is a maintainability opinion, not a fact about the code. The
  prompt asks Claude to justify each one with a concrete cost, and the severity rule
  keeps them out of "Blocking" by default -- without that guardrail, a review command
  that treats subjective style opinions with the same weight as a security hole would
  quickly train developers to ignore its output altogether.
