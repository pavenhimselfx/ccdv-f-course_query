# Solution 6 — Writing Config Files

Reference answer for `exercises/ex6_config_files.md`. Config file schemas for tools like
Claude Code evolve over time -- treat the exact field names below as illustrative of the
*pattern* (what kind of thing goes in each file, and why), and check current
docs.claude.com if you're setting this up for a real project.

## Task 1 — `CLAUDE.md`

```markdown
# ticket-triage

`ticket-triage` is a small internal CLI tool that reads support tickets from a local CSV
file, calls Claude to classify each ticket's urgency (P1-P4) and category (billing,
technical, account, other), and writes the results to a new CSV alongside the original.

## Commands

- Run the tool: `python -m ticket_triage.cli --input tickets.csv --output triaged.csv`
- Run tests: `pytest tests/`
- Run just the classification-logic tests: `pytest tests/test_classify.py`

## Conventions and constraints

- The classification system prompt lives in `ticket_triage/prompts/classify_system.md`.
  Check there first before writing a new one inline anywhere else.
- The Claude model version is pinned in `ticket_triage/config.py` as `MODEL_VERSION`.
  Don't change this value without opening a PR that also updates
  `tests/golden_classifications.json` (our eval baseline) -- a silent model bump can shift
  classification behavior.
- Never commit a real CSV of customer ticket data. Only `sample_data/redacted_sample.csv`
  (already-redacted, synthetic-looking data) belongs in the repo. Real input/output CSVs
  should stay in the gitignored `local_data/` directory.
- This project targets Python 3.11+ and uses the sync `anthropic.Anthropic` client (not
  async) -- ticket volume is low enough that sequential calls are fine; don't introduce
  asyncio here without discussing it first, to keep the code simple for a 3-person team.
```

**Why each part is there:** the description orients Claude (or a new teammate) to what the
project even is in one read. The commands section means Claude doesn't have to guess how
to run tests before making a change and verifying it. The system-prompt-location note
prevents Claude from inventing a second, inconsistent prompt somewhere else in the repo.
The model-pin-and-eval-baseline note ties a config change to the test suite that should
catch regressions from it, tying Configuration Management directly to Software Engineering
Foundations (code review / testing discipline). The "never commit real customer data" rule
is a safety/compliance constraint, not a style preference -- exactly the kind of thing that
belongs in `CLAUDE.md` because it's easy for an agent (or a rushed human) to violate by
default if it isn't stated. The sync-vs-async note heads off a plausible but unwanted
"helpful" refactor.

## Task 2 — `settings.json`

```json
{
  "permissions": {
    "allow": [
      "Bash(pytest *)",
      "Bash(python -m ticket_triage.cli --input sample_data/* *)"
    ],
    "ask": [
      "Bash(python -m ticket_triage.cli --input local_data/* *)",
      "Write(local_data/*)"
    ]
  },
  "env": {
    "TICKET_TRIAGE_LOG_LEVEL": "INFO"
  },
  "model": "claude-sonnet-4-5-20250929"
}
```

**Why each part is there:**

- `permissions.allow` for running tests and running the tool against the redacted sample
  data: both are safe to auto-approve because they can't touch real customer data or do
  anything destructive -- routine, low-risk actions a developer would approve every time
  anyway, so auto-allowing them keeps the workflow fast.
- `permissions.ask` for anything touching `local_data/` (real ticket data): this is
  exactly the boundary called out in `CLAUDE.md` -- real customer data is higher-stakes,
  so those actions should prompt for confirmation rather than run silently, even though
  the tool is legitimately meant to be run against that data by a human.
- `env.TICKET_TRIAGE_LOG_LEVEL`: a project-specific environment variable so classification
  runs log at a consistent, useful verbosity by default across the team, without every
  developer having to set it manually in their own shell.
- `model`: pins the same dated model version referenced in `CLAUDE.md` and
  `ticket_triage/config.py`, so a Claude Code session working on this project defaults to
  the same version the application itself is pinned to -- reducing the chance of someone
  debugging a discrepancy caused by two different model versions being in play at once.

## A note on precedence

If this project also has a user-level (not just project-level) `settings.json` on a
developer's machine, know that one layer typically overrides or merges with the other
(exact precedence rules are worth checking in current docs) -- the project-level file
above should be checked into version control so it's consistent for the whole team,
while anything genuinely personal (an individual's editor preference, for instance)
belongs at the user level instead.
