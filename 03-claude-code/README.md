# Module 03 — Claude Code Operation

> **Cost note:** this entire domain is free if you have any Claude.ai subscription (Pro,
> Max, Team, or Enterprise) — Claude Code itself is the thing being studied here, and it
> authenticates with your subscription's normal usage limits, not a metered API key. See
> `00-setup/README.md` section 1.

This module covers Domain 3 of the CCDV-F blueprint: **Claude Code Operation** (3.1% of
the exam — a small, focused domain). It's a light weight in points but a dense one in
concepts: Claude Code has several distinct core components and features, and the exam
expects you to know what each one is *for*, not just that it exists.

This is an unofficial, independently-built self-study course inspired by the published
CCDV-F exam blueprint. It is not written or endorsed by Anthropic, and it does not
reproduce real exam questions.

**A note on hands-on work in this module.** Unlike most of this course, these exercises
are about configuring and operating the Claude Code CLI itself — not about calling the
Anthropic API from Python. You do **not** strictly need an API key to complete the
file/config-based exercises (writing `CLAUDE.md` files, drafting a `settings.json`,
designing a slash command on paper) — those are just structured files you can create and
reason about with a text editor. To actually *run* the CLI-based parts (starting a
session, invoking a custom command, running headless mode) you need
[Claude Code](https://docs.claude.com/en/docs/claude-code) installed and authenticated.
If you don't have it installed yet, you can still read and complete the written parts of
every exercise here.

Claude Code's exact CLI flags, file formats, and behavior change fairly often between
releases. Everything below is accurate at a **conceptual** level, but before you rely on
a specific flag name, file path, or JSON key on the real exam or in real work, check
[docs.claude.com](https://docs.claude.com) — the Claude Code section is the authority,
and this README explicitly flags the places where "check current docs" matters most.

---

## 1. What is Claude Code?

Claude Code is Anthropic's **agentic coding CLI** — a command-line tool that runs Claude
directly against a local codebase. Instead of pasting code into a chat window, you run
`claude` from inside a project directory, and Claude can read files, search the
repository, propose and apply edits, run shell commands (tests, linters, builds, git),
and iterate — all inside a permission model you control. It's built for "agentic" use:
Claude decides which tools to call and in what order to accomplish a task, rather than
you manually feeding it one file at a time.

Because Claude Code operates *on your machine, on your repo*, its behavior is shaped by
a layer of configuration and conventions that don't exist when you're just calling the
API: where it looks for standing instructions, how it decides what it's allowed to do
without asking, how a long-running task can be resumed, and how you extend it with your
own reusable prompts and delegated sub-tasks. That configuration layer is this domain.

## 2. Core components

### Rules

Rules are **persistent instructions or constraints** that apply across a session (or
across every session in a project) without you having to repeat them in every prompt.
Practically, most "rules" content lives in `CLAUDE.md` files (see the hierarchy section
below) — things like "always use type hints," "never modify files under `generated/`,"
or "run the linter before declaring a task done." The exam-relevant idea is the concept
itself: a durable, standing instruction that shapes *every* turn of a session, as
distinct from a one-off instruction typed into a single prompt.

### Skills

Skills are **packaged, reusable instruction sets** that Claude Code can invoke for a
class of task. Where a Rule is a standing constraint that's always in effect, a Skill is
more like a callable capability: a bundle of instructions (and sometimes supporting
files or scripts) that Claude loads only when the current task matches what the skill is
for — e.g., a skill for "generate a properly formatted Word document" or "run our team's
PR review checklist." Skills let you (or an organization) codify expert procedures once
and have Claude reach for them automatically when relevant, instead of you re-explaining
the procedure every time.

### Commands

Commands are **slash commands** — short, typed shortcuts (`/something`) that trigger a
predefined prompt or action. Claude Code ships with **built-in** slash commands for
things like managing the current session or clearing context, and it also supports
**custom** slash commands that you or your team define for your own repeated prompts
(e.g., `/review-pr`, `/write-tests`). Conceptually, a custom command is a small, named,
reusable prompt template — you invoke it by name instead of retyping the same
instructions every time you want that task done. Exercise 2 in this module has you
design one.

### Agents

Agents (subagents) are **delegate workers** that Claude Code can spin up to handle a
piece of a task independently — for example, dispatching a focused subagent to search
the codebase for a pattern, or to run and summarize a test suite, while the main session
keeps working on the overall task. The value is separation of concerns and context
management: a subagent can do a bounded, well-defined piece of work and report back a
summary, rather than every detail of that side-task consuming the main conversation's
context window.

### Agent Memory

Agent Memory refers to how Claude Code **persists context or notes across a session, or
over time**, beyond what fits in a single conversation's context window. This can mean
notes Claude writes for itself to pick back up later, or project-level memory that
carries forward useful facts learned while working (as opposed to CLAUDE.md, which is
memory *you* author deliberately). The exam-relevant distinction is: Agent Memory is
about *retaining* useful context across time/sessions, separate from the standing
configuration you write by hand.

## 3. Features

### Session management

A Claude Code session is one continuous unit of work. Sessions can typically be
**resumed or continued** — picking a previous session back up (with its history and
context) rather than starting from a blank slate every time you open the CLI. This
matters for multi-day or multi-step work: you don't lose everything Claude has already
learned about your codebase and your task just because you closed the terminal.

### Built-in vs. custom slash commands

- **Built-in commands** ship with Claude Code itself and typically cover session and
  tool mechanics — e.g., commands to review configuration, manage context, or control
  the session.
- **Custom commands** are ones you define yourself (see "Commands" above and Exercise 2)
  for prompts specific to your project or team.

The exam-relevant distinction is simply: built-in = provided by the tool, custom =
authored by the user/team, and both are invoked the same way, by typing `/name`.

### Headless mode

Headless mode is a **non-interactive, scriptable** way of invoking Claude Code — you run
it as a single command (e.g., in a shell script or CI pipeline) that executes a task and
exits, rather than opening an interactive back-and-forth session. This is what makes
Claude Code usable inside automation: a CI job that asks Claude to summarize a diff, a
pre-commit style check, a batch job run over many repos. Conceptually: interactive mode
is a conversation; headless mode is a one-shot (or scripted) invocation with no human in
the loop.

### Streaming mode

Streaming mode delivers output **incrementally as it's generated**, rather than waiting
for a complete response before showing anything. This is the same idea as streaming
responses from the API, applied to Claude Code's own output — useful for long-running
tasks where you want visibility into progress as it happens, and useful for tooling that
consumes Claude Code's output programmatically and wants to process it incrementally
rather than blocking until completion.

### Auto-mode

Auto-mode refers to **autonomous operation with reduced confirmation prompts** — Claude
Code proceeds through a task (making edits, running commands) without stopping to ask
permission at each step, within whatever boundaries your permissions configuration
allows. This trades a tighter human-in-the-loop workflow for speed and throughput, and
it's precisely why the permissions section of `settings.json` (below) matters: auto-mode
is only as safe as the permission boundaries you've set before turning it on.

> **Check current docs.** The exact commands, flags, and default behaviors for session
> management, headless mode, streaming mode, and auto-mode change across Claude Code
> releases. Know the *concepts* above cold for the exam; verify exact syntax against
> [docs.claude.com](https://docs.claude.com) before relying on it in real work.

## 4. The CLAUDE.md hierarchy

`CLAUDE.md` is the primary place Rules-style standing instructions live, and Claude Code
looks for it at more than one level:

- **User-level** — a `CLAUDE.md` (or equivalent user-scoped config) that applies to you,
  across all projects, regardless of which repo you're working in. Good for personal
  preferences that aren't project-specific (e.g., "explain your reasoning before making
  changes").
- **Project-level (repo root)** — a `CLAUDE.md` at the root of a repository, describing
  conventions for that whole project: coding style, architecture notes, commands to run
  tests, things to never touch.
- **Nested directory level** — a `CLAUDE.md` inside a subdirectory (e.g.,
  `backend/CLAUDE.md`), scoped to that subsystem: notes relevant only when Claude is
  working inside that part of the tree.

These **combine** rather than strictly override one another: when Claude Code is
operating inside `backend/`, it's expected to honor both the root-level conventions
*and* the more specific `backend/CLAUDE.md` notes. The general mental model is
**general-to-specific layering** — broader scopes set the default, narrower scopes add
or refine guidance for their part of the tree, and where they conflict, the more
specific (closer to the current working location) instruction is what should win for
work happening in that location. Exercise 1 walks you through building exactly this
structure and reasoning about which instructions apply where.

> **Check current docs** for the exact precedence rules and file-discovery behavior
> (how many levels up/down Claude Code looks, exact merge/override semantics) — this has
> been an area of active change.

## 5. Repository initialization

Claude Code provides an **init-style command** to bootstrap its configuration for a new
repository. Conceptually, running it does things like:

- Scan the codebase to understand its structure, languages, and tooling.
- Generate a starting `CLAUDE.md` at the project root summarizing what it found
  (frameworks used, how to run tests/build, notable conventions) as a first draft for
  you to review and edit.
- Set up whatever project-local configuration directory Claude Code uses to store its
  own settings, commands, and related files for that repo.

The output is a *starting point*, not a finished configuration — you're expected to
review and edit the generated `CLAUDE.md` and settings rather than trust it blindly.

## 6. `settings.json` configuration

`settings.json` is where you configure Claude Code's **behavior**, as opposed to
`CLAUDE.md`, which configures its **knowledge/instructions**. At a conceptual level, it
typically covers:

- **Permissions** — what Claude Code is allowed to do without asking, what it must ask
  about, and what's denied outright (e.g., rules about which shell commands, file paths,
  or tools require confirmation vs. run freely vs. are blocked). This is the control
  surface that makes auto-mode safe to use.
- **Hooks** — commands that run automatically at defined points in Claude Code's
  lifecycle (e.g., before or after a tool runs, or after a file edit) — useful for
  things like auto-formatting a file after every edit, or running a linter after Claude
  finishes a task.
- **Model settings** — which model Claude Code uses for a session or task.
- Other environment/tool configuration relevant to how the CLI behaves in that project
  or for that user.

Settings can typically exist at multiple scopes too (user-level vs. project-level),
echoing the same general-to-specific idea as the `CLAUDE.md` hierarchy: broad defaults
at the user level, project-specific overrides checked into the repo. Exercise 2 has you
draft an example `settings.json` with a permissions section and a hook.

> **Check current docs** for the exact JSON schema, key names, and available hook
> events — `settings.json`'s shape is one of the faster-moving parts of Claude Code.

## 7. What's in this module

```
03-claude-code/
├── README.md                              (this file)
├── exercises/
│   ├── ex1_claude_md_hierarchy/           build a fake repo, write root + nested
│   │                                       CLAUDE.md files, reason about precedence
│   └── ex2_custom_command_and_settings/   design a custom slash command; draft a
│                                           settings.json with permissions + a hook
├── solutions/
│   ├── ex1_claude_md_hierarchy/           filled-in example solution
│   └── ex2_custom_command_and_settings/   filled-in example solution
└── quiz.md                                6 original scenario-style practice questions
```

Work through the exercises before checking the solutions — the value here is in writing
your own `CLAUDE.md` content and settings and then comparing your reasoning to the
worked example, not in reading the worked example first.
