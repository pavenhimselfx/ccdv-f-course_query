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

*(Write your CLAUDE.md here or in a separate file.)*

## Task 2 — Write a `settings.json`

Create a `settings.json` for this project. It doesn't need to be exhaustive, but it
should include:

- At least one permission rule (something that should be auto-allowed, e.g. running
  the test suite, and/or something that should require confirmation, e.g. anything
  that touches real customer data files).
- At least one custom setting relevant to this project (use your judgment for a
  plausible field -- e.g. an environment variable to inject, or a default model
  setting).

*(Write your settings.json here or in a separate file.)*

## Task 3 — Explain your choices

For each field/section you wrote in Tasks 1 and 2, write one sentence explaining what
it's for and why you included it. This is the part that actually tests understanding --
anyone can copy a template, but you should be able to say *why* each piece matters for
this specific project.

*(Write your explanations here.)*

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
