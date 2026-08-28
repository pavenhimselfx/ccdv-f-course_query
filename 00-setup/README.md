# Module 00 — Environment Setup

This module gets you from zero to "I can make a Claude call from Python" — and, importantly,
helps you figure out which parts of that can be **free** given what access you already have.
Every later module in this course assumes you have completed at least one of the paths below.

This is an unofficial, independently-built self-study course inspired by the published
CCDV-F exam blueprint. It is not written or endorsed by Anthropic, and it does not
reproduce real exam questions. Anthropic's own documentation is the authority on anything
technical here — see the last section of this README.

## 0. Two different ways to talk to Claude from code — and which one costs money

Before anything else, it's worth being clear on a distinction the exam itself tests
(Domain 2: Claude Application Design) and that directly affects your wallet: there are two
separate products here, with separate billing.

- **The raw Messages API** (the `anthropic` Python package, `client.messages.create(...)`) —
  this is pay-per-token, billed through **platform.claude.com** (the Console), and needs a
  credit card on file even though new accounts get a small amount of free trial credit.
  This is what most "Domain 2: Claude API Mechanics" content (streaming, vision, prompt
  caching, batch API) and "Domain 5: Cost and Token Management" exercises exercise directly
  — because that's literally the thing being tested.
- **Claude Code and the Claude Agent SDK** — these can instead authenticate with a
  **Claude.ai subscription** (Pro, Max, Team, or Enterprise) using OAuth, and usage draws
  from your subscription's normal usage limits, **not** separate metered billing. If you
  have a Team or Enterprise seat through work, this path costs you nothing extra.

If you have a paid Claude.ai account through Knowit (Team/Enterprise), read section 1 below
first — a large share of this course's exercises can run entirely on that, for free. Section
2 covers the metered API key path, which you'll still want for the handful of exercises that
specifically test raw API-level mechanics no subscription product exposes.

## A note for Windows users: shell syntax differs from the examples below

Every `export VAR="value"` command in this README is bash syntax (Mac/Linux, or Git Bash on
Windows). If you're in CMD or PowerShell instead, it won't work as written — translate it:

- **PowerShell:** `$env:VAR = "value"` (quotes are fine here — PowerShell strips them
  correctly).
- **CMD:** `set VAR=value` — and **don't** quote the value. Unlike bash, CMD does not strip
  quote characters from `set`, so `set VAR="value"` sets `VAR` to the literal text `"value"`,
  quotes included, which will break authentication in a confusing way (not an obvious error).
- Not sure which shell you're actually in? Check the prompt: PowerShell's starts with `PS`,
  e.g. `PS C:\Users\you\...>`. Plain CMD has no `PS` prefix. This matters because `set`/`echo
  %VAR%` (CMD) and `$env:VAR`/`echo $env:VAR` (PowerShell) are not interchangeable — mixing
  them silently does nothing rather than erroring clearly.
- Both `set` and `$env:VAR =` are **session-only** — closing the terminal window loses the
  variable, same as an un-persisted `export`. There's no exact equivalent of adding a line to
  `~/.bashrc`; if you want a variable to persist across terminals/reboots, use System
  Properties → Environment Variables (or `setx VAR value` in CMD, which only affects *new*
  terminals, not your current one).
- The Windows install command from [code.claude.com](https://code.claude.com) may install the
  `claude` binary without adding its folder to PATH. If `claude --version` isn't recognized
  right after installing, check whether `%USERPROFILE%\.local\bin` is on your PATH (System
  Properties → Environment Variables → User variables → Path) and add it if missing, then open
  a brand-new terminal — existing terminal windows won't pick up a PATH change.

## 1. Free path: use your Knowit Team/Enterprise subscription

If your `claude.ai` account is on a Team or Enterprise plan, you can run Claude Code and the
Claude Agent SDK ag  ainst that subscription with no separate billing:

1. **Install Claude Code** (the CLI) per the current instructions at
   [code.claude.com](https://code.claude.com) (the install command has changed over time —
   check there rather than trusting an old `npm install` snippet from elsewhere).
2. **Generate a long-lived subscription token** for scripted/non-interactive use:

   ```bash
   claude setup-token
   ```

   This opens a browser authorization flow against your Claude.ai account. Once approved, it
   prints a token to your terminal — it is **not** saved anywhere automatically, so copy it.
3. **Export it as an environment variable:**

   ```bash
   export CLAUDE_CODE_OAUTH_TOKEN="the-token-you-just-got"
   ```

   With this set (and no `ANTHROPIC_API_KEY` in your environment — see the precedence note
   below), both the `claude` CLI and the Claude Agent SDK will authenticate against your
   subscription's usage limits instead of asking for a metered key.
4. **Install the Agent SDK for Python** alongside this course's other dependencies if you
   want to work through Agent-SDK-flavored exercises (this is a separate package from the
   `anthropic` Messages API package — check the current package name and API at
   [code.claude.com](https://code.claude.com), since Python Agent SDK conventions have moved
   around; as of this writing it installs from PyPI and mirrors the TypeScript SDK's shape).
5. **Verify:** run `claude -p "Reply with the single word: ready"` from your terminal. A
   successful reply confirms the subscription auth path works end to end, at zero marginal
   cost to you.

**Important precedence note:** if `ANTHROPIC_API_KEY` is set in your environment at the same
time, Claude Code and the Agent SDK will prefer the metered key and bill through the Console
instead of your subscription. Keep the two paths separate — `unset ANTHROPIC_API_KEY` before
a session where you want to guarantee you're using your subscription, and check `/status`
inside Claude Code to confirm which credential is active.

**What this path does *not* cover:** the raw `anthropic` Python package's `client.messages
.create(...)` calls always bill through the metered Console API key, regardless of what
subscription you hold — there is currently no way to point that specific package at your
Claude.ai subscription instead. So exercises that specifically exist to teach raw
Messages-API mechanics (streaming, vision content blocks, `cache_control` prompt caching,
the Message Batches API, reading token-usage/cost fields off a response) still need the
metered key path in section 2. See the table in section 3 for exactly which exercises those
are.

## 2. Metered path: create an Anthropic Console API key

Use this for the exercises flagged "needs metered key" in the table below, or if you don't
have a Team/Enterprise subscription available.

1. Go to [platform.claude.com](https://platform.claude.com) and sign up or log in.
2. If prompted, create a new organization (workspace) or join one you've been invited to. If
   Knowit already has a Console org tied to your Team subscription, ask whoever administers
   it whether they can invite you with a scoped **"Claude Code" role** (can only create
   limited-purpose keys) rather than opening a personal billing relationship — worth asking
   before adding a personal card.
3. In the left sidebar, find **API Keys** (sometimes nested under Settings, depending on the
   current console layout).
4. Click **Create Key**, give it a name like `ccdv-f-course`, and copy the key immediately —
   most consoles only show the full key value once, at creation time.
5. Save that key somewhere temporary and safe (a password manager is ideal) until you wire
   it into your environment below.
6. **Set a spend limit immediately**, before running anything: the Console's billing/usage
   settings let you cap monthly spend. Set it low (a few dollars) — every exercise in this
   course uses short prompts and the cheapest model tier, so realistic total cost for
   working through all of them is well under a dollar, and a spend cap means you genuinely
   cannot be surprised by a bill.

New accounts typically come with a small amount of free trial credit on top of that, but a
valid card is required to generate a key at all, even before that credit is used — this
isn't specific to your situation, it's how the Console works for everyone. Pricing changes
over time, so don't rely on numbers from this README — check current rates at
[anthropic.com/pricing](https://www.anthropic.com/pricing) before running anything at scale.

### Store the key safely

Treat an API key like a password: anyone who has it can spend money on your account.

- **Never commit it to version control.** Don't paste it into source files, notebooks you
  intend to push, or commit messages.
- **Prefer an environment variable.** Set `ANTHROPIC_API_KEY` in your shell, and the
  official SDK will pick it up automatically without you passing it in code:

  ```bash
  export ANTHROPIC_API_KEY="sk-ant-...your-key..."
  ```

  Add that line to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.) if you want it
  available in every new terminal, or just export it in the session you're working in.

- **Or use a `.env` file with `python-dotenv`.** This repo includes `.env.example` as a
  template. Copy it to a real `.env` file and fill in your key:

  ```bash
  cp .env.example .env
  # then edit .env and paste your real key in
  ```

  `.env` should be listed in your project's `.gitignore` so it never gets staged or
  committed — only `.env.example` (which contains no real secret) belongs in version
  control. `verify_setup.py` in this folder shows how `python-dotenv` loads a `.env` file
  automatically if one is present.

If you ever suspect a key has leaked (pushed to a public repo, pasted somewhere public),
revoke it immediately from the API Keys page in the console and create a new one.

## 3. Which exercises need which path?

Rough guide — check each exercise's own docstring/instructions for the exact word on
whether it needs a live call at all:

| Domain | Free via Team subscription (Claude Code / Agent SDK) | Needs a metered Console API key |
|---|---|---|
| 00 — Setup | `claude -p "..."` verification | `verify_setup.py` as written (uses the raw SDK) — or just skip it and rely on the `claude -p` check instead |
| 01 — Agents and Workflows | ex1 and ex3 now run on the Claude Agent SDK under subscription auth | ex2 deliberately still hand-rolls the raw Messages API tool-use loop — that's the point of the exercise |
| 02 — Applications and Integration | Requirements/config exercises (ex1, ex6) need no calls at all | Streaming, vision, caching, batch API, async exercises (ex2–ex5) — these *are* the raw API mechanics being tested |
| 03 — Claude Code | All of it — this domain is Claude Code itself | — |
| 04 — Eval, Testing, Debugging | Trace-analysis exercise (ex2) needs no live calls | Error-handling exercise (ex1) needs at least one real call to see real exception types |
| 05 — Model Selection and Optimization | — | All four exercises measure real token/latency/cost behavior, which requires the metered API |
| 06 — Prompt and Context Engineering | Context pruning/compaction (ex1) is a local simulation | Prompt iteration (ex2) and structured-output (ex3, partially) need live calls |
| 07 — Security and Safety | Guardrail hook (ex2) and secrets hygiene (ex3) are local logic exercises | Prompt-injection defense (ex1) needs one live call to confirm the fix works |
| 08 — Tools and MCPs | All of it: the tool-use exercise (ex1) now runs on the Claude Agent SDK under subscription auth; building the MCP server (ex2) never needed a key; testing it (ex2b) now uses Claude Code instead of a Python client script | — |
| 09 — Practice exam | All of it — it's reading and self-grading | — |

**Domains 1 and 8 have already been reworked this way:** Domain 1's `ex1` and `ex3`, and all
of Domain 8, now run on the Claude Agent SDK / Claude Code under subscription auth instead of
the metered API. Domain 1's `ex2` deliberately still uses the raw Messages API on purpose —
hand-rolling the tool-use loop is itself the thing that exercise teaches, and abstracting it
away with the SDK would defeat the point (its docstring explains this). Everything else in
the table above — Domain 2's API-mechanics exercises, Domain 5's token/cost measurements, and
the "confirm it actually works live" steps in Domains 4, 6, and 7 — genuinely tests raw
Messages-API-level behavior that no subscription product exposes, so those still need the
metered path in section 2. That's a fairly small, deliberate set of exercises, and total cost
for all of them together is trivial if you use the cheapest model tier and set a spend cap.

## 4. Set up a Python virtual environment

Use a virtual environment so this course's dependencies don't collide with anything else on
your machine.

```bash
python3 -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

`requirements.txt` in this folder installs:

- `anthropic` — the official Python SDK for the raw Messages API (metered path)
- `python-dotenv` — loads variables from a `.env` file into your environment
- `requests` — used in a few later exercises that talk to HTTP endpoints directly
- `pytest` — used to run this course's exercise/solution test suites

It does **not** install the Claude Agent SDK or Claude Code — install those separately per
section 1 if you're taking the subscription path.

## 5. Verify your setup

**Metered path:** with your virtual environment active and `ANTHROPIC_API_KEY` set (directly,
or via `.env`), run:

```bash
python verify_setup.py
```

This sends one small, cheap request to the Messages API and prints the response. A
successful run means your key, network access, and installed packages all work together —
you're ready for the metered-key exercises. If it fails, the script prints troubleshooting
hints for the most common causes (missing key, invalid key, missing package, network/proxy
issues).

**Subscription path:** run `claude -p "Reply with the single word: ready"` as described in
section 1. A successful reply means you're ready for the subscription-based exercises.

## 6. What if I don't have either set up yet?

Most of this course's exercises can be read, reasoned about, and partially completed without
ever calling Claude — predicting what a prompt will produce, writing the Python code that
would call the API, reviewing a tool-use schema, spotting a security issue in a sample agent,
and so on. You can work through a lot of material this way. But full hands-on completion —
actually running exercises and checking real output — requires one of the two paths above, so
don't put this module off for long.

## 7. Keep the official docs open while you study

This course is a study aid, not a replacement for Anthropic's documentation, and the Claude
platform (models, SDKs, tool schemas, pricing, subscription features) moves fast enough that
specific details here can drift out of date between when this was written and when you read
it. Keep [docs.claude.com](https://docs.claude.com) and [code.claude.com](https://code.claude.com)
open in tabs while you work through this course — between them they cover the API reference,
the Claude Agent SDK, Claude Code, and MCP (Model Context Protocol). Anywhere this course's
wording and the official docs disagree, trust the official docs. That especially applies to
exact SDK method/package names, CLI flags, and authentication precedence rules — the
patterns shown here are correct as of this writing, but double-check them if something
doesn't behave the way this module says it should.
