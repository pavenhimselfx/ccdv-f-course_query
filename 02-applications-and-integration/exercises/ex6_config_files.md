# Exercise 6 — Writing Config Files (written / hands-on exercise)

**Skill covered:** Configuration Management

No API key needed for this one. You can do it purely by writing text, though if you
have Claude Code installed you're welcome to actually drop these files into a scratch
project directory and see how Claude Code picks them up.

## The scenario

You're starting a small internal project: a Python CLI tool called `ticket-triage` that
reads support tickets from a local CSV file, calls Claude to classify each ticket's
urgency and category, and writes the results back out to a new CSV. It's a small team
project (3 developers) that will live in a shared git repo.

## Task 1 — Write a `CLAUDE.md`

Create a `CLAUDE.md` for this project (you can write it inline in this file, or as a
separate `CLAUDE.md` alongside this exercise). It should give Claude Code enough
project-specific context to be genuinely useful when a developer asks it to make a
change. At minimum, include:

- A one-paragraph description of what the project does.
- The command(s) to run the tool and to run its tests.
- At least one project-specific convention or constraint Claude should follow (e.g.,
  "never commit a real CSV of customer ticket data, only the redacted sample in
  `sample_data/`" or "the Claude model version is pinned in `config.py` -- don't
  change it without asking").
- A short note on where the system prompt used for classification lives, so Claude
  knows to look there rather than guessing.

```markdown
# ticket-triage

`ticket-triage` is a small internal CLI tool that reads support tickets from a local CSV
file, sends each ticket's text to Claude for urgency and category classification, and
writes the enriched rows to a new CSV. Used by the support team to prioritize inbound
tickets faster than manual triage.

## Commands

- Run the tool: `python -m ticket_triage run --in tickets.csv --out tickets_classified.csv`
- Run tests: `pytest`

## Conventions and constraints

- Never commit a real CSV of customer ticket data. Only the redacted example in
  `sample_data/example_tickets.csv` belongs in git; real files live in the gitignored
  `data/` directory.
- The Claude model version is pinned in `ticket_triage/settings.py` as `CLAUDE_MODEL`.
  Don't bump it without first running `pytest tests/test_classification_regressions.py`
  against the new version.
- The classification system prompt lives in `ticket_triage/prompts/system_prompt.txt` --
  edit it there, don't write a new inline prompt elsewhere in the codebase.
- This is a 3-person team project; keep PRs small and get one review before merging to
  main.
- This project targets Python 3.11+ and uses the sync `anthropic.Anthropic` client, not
  async. Ticket volume is low enough that sequential calls are fine -- don't introduce
  asyncio here without discussing it first, to keep the code simple for a small team.
```

## Task 2 — Write a `settings.json`

Create a `settings.json` for this project. It doesn't need to be exhaustive, but it
should include:

- At least one permission rule (something that should be auto-allowed, e.g. running
  the test suite, and/or something that should require confirmation, e.g. anything
  that touches real customer data files).
- At least one custom setting relevant to this project (use your judgment for a
  plausible field -- e.g. an environment variable to inject, or a default model
  setting).

```json
{
  "permissions": {
    "allow": [
      "Bash(pytest *)",
      "Bash(python -m ticket_triage run --in sample_data/* *)"
    ],
    "ask": [
      "Write(data/*)",
      "Bash(python -m ticket_triage run --in data/* *)"
    ]
  },
  "env": {
    "TICKET_TRIAGE_ENV": "dev"
  },
  "model": "claude-sonnet-4-5-20250929"
}
```

## Task 3 — Explain your choices

For each field/section you wrote in Tasks 1 and 2, write one sentence explaining what
it's for and why you included it. This is the part that actually tests understanding --
anyone can copy a template, but you should be able to say *why* each piece matters for
this specific project.

**CLAUDE.md:**

- The one-paragraph description orients Claude (or a new teammate) to what the project
  even does before it's asked to change anything, instead of guessing from file names.
- The commands section means Claude doesn't have to search the repo or guess how to run
  the tool/tests before verifying a change actually works.
- The "never commit real customer data" rule is a safety/compliance constraint, not a
  style preference -- exactly the kind of thing that needs to be stated explicitly,
  because it's easy for an agent (or a rushed human) to violate by default without it.
- The model-pin note ties a config change to the specific regression test that should
  catch behavior shifts from it, so a version bump doesn't silently change classification
  behavior in production.
- The system-prompt-location note prevents Claude from inventing a second, inconsistent
  prompt somewhere else in the codebase when asked to "improve the classification logic."
- The PR/review note is a lightweight team-process constraint specific to a 3-person repo,
  where informal review discipline matters more than it would solo.
- The sync-vs-async note heads off a plausible but unwanted "helpful" refactor -- an agent
  (or an eager teammate) reaching for `asyncio.gather` to "speed this up" the way ex5 did,
  even though this tool's low ticket volume doesn't need it and the team deliberately
  chose simplicity over that performance gain. CLAUDE.md isn't just describing what
  exists; it's also for blocking specific improvements that sound good in isolation but
  aren't wanted here.

**settings.json:**

- `permissions.allow` for tests and for running the tool against the redacted sample data:
  both are safe to auto-approve since neither can touch real customer data or do anything
  destructive -- routine actions a developer would approve every time anyway.
- `permissions.ask` for anything touching `data/` (real customer tickets): this is the
  exact boundary named in `CLAUDE.md` -- real data is higher-stakes, so those actions
  should prompt for confirmation instead of running silently.
- `env.TICKET_TRIAGE_ENV`: a project-specific environment variable so the tool defaults
  to a consistent runtime mode across the team without everyone setting it manually.
- `model`: pins the same dated model version referenced in `CLAUDE.md` and
  `ticket_triage/settings.py`, so a Claude Code session defaults to the same version the
  application itself uses, avoiding a discrepancy between "what Claude Code assumes" and
  "what the app actually runs."

**A note on precedence:** this `settings.json` is meant to live at the *project* level
(checked into git), not the user level, because these are team-wide rules everyone
working on `ticket-triage` should share -- the auto-allow/ask boundary around real
customer data isn't something any individual developer should be able to silently
loosen for themselves. A developer's genuinely personal preferences (e.g. their own
editor integration settings) belong in a user-level settings file instead, which
typically merges with or overrides the project-level file depending on the field --
worth checking current docs.claude.com for the exact precedence rules rather than
assuming.

## How to know you succeeded

A strong answer:

- Has a `CLAUDE.md` that's specific to *this* project, not generic boilerplate that
  could apply to any repo (a bad sign: nothing in it would need to change if you
  swapped in a completely different project).
- Includes at least one real constraint that matters for safety/correctness (e.g. don't
  commit real customer data), not just style preferences.
- Has a `settings.json` with plausible, valid-looking JSON structure (check it parses --
  `python -m json.tool < settings.json` is a quick way to check if you wrote a real file).
- Explicitly separates "things that are auto-allowed" from "things that need
  confirmation" in the permissions you describe, and the choice makes sense (running
  tests: safe to automate; touching real customer data: should not be automatic).
- Explains *why*, not just *what*, for each field.

Check your answer against `solutions/sol6_config_files.md` when done -- note that config
file schemas for tools like Claude Code evolve, so treat the solution's exact field
names as illustrative of the pattern, and check current docs.claude.com if you're
setting this up for a real project.
