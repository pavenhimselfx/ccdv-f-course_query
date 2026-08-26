# Exercise 1 — The CLAUDE.md Hierarchy

**Type:** File/config exercise. No API key or running Claude Code required — you can
complete this entirely with a text editor, though if you do have Claude Code installed,
step 5 is worth actually trying for real.

## Goal

Build a small fake repository with a project-root `CLAUDE.md` and a nested subdirectory
`CLAUDE.md`, then reason through — and write down — which instructions apply when Claude
Code is asked to work at the root vs. inside the subdirectory.

## Background

Claude Code reads `CLAUDE.md` files at multiple scopes (user-level, project root, and
nested subdirectories) and combines them, with more specific scopes refining or
overriding the general one for work happening in that location. See the README's
"CLAUDE.md hierarchy" section before starting if you haven't already.

## Steps

### 1. Create the fake repo structure

Anywhere in your own workspace (this doesn't need to be a real, working codebase — empty
placeholder files are fine), create:

```
fake_repo/
├── CLAUDE.md
├── frontend/
│   └── (empty is fine, or a placeholder file)
└── backend/
    ├── CLAUDE.md
    └── (empty is fine, or a placeholder file)
```

You can do this with plain shell commands, e.g.:

```bash
mkdir -p fake_repo/frontend fake_repo/backend
touch fake_repo/CLAUDE.md fake_repo/backend/CLAUDE.md
```

### 2. Write the root CLAUDE.md

In `fake_repo/CLAUDE.md`, write realistic **project-wide** conventions — the kind of
thing that should apply no matter which part of the repo Claude is working in. Aim for
5–8 concrete rules. Think about things like:

- Language/framework and version in use
- How to run the test suite and linter
- Commit message conventions
- Directories or files Claude should never modify (secrets, generated code, vendored
  dependencies)
- General code style expectations

This course includes an example at `sample_root_CLAUDE.md` in this folder — write your
own first, then compare.

### 3. Write the backend CLAUDE.md

In `fake_repo/backend/CLAUDE.md`, write **subsystem-specific** notes that only make
sense when Claude is working inside `backend/` — things that would be noise at the root
level but matter a lot once you're in this subtree. Aim for 4–6 items. Think about
things like:

- The backend's specific framework/library choices (that might differ from the
  project-wide default, or add detail to it)
- A backend-specific test or migration command
- Data model or database conventions
- A backend-specific "never touch this" (e.g., a migrations directory, a generated
  client)
- Anything that would actively conflict with, or sharpen, a root-level rule

This course includes an example at `sample_backend_CLAUDE.md` in this folder — write
your own first, then compare.

### 4. Reason through precedence — write it down

Create a file `my_reasoning.md` in this folder and answer, in your own words:

1. If Claude Code is invoked with its working context inside `fake_repo/frontend/`,
   which `CLAUDE.md` file(s) apply? Which do not?
2. If Claude Code is invoked with its working context inside `fake_repo/backend/`, which
   file(s) apply, and in what order of precedence if two instructions conflict?
3. Write one concrete example rule in your root `CLAUDE.md` and one concrete example
   rule in your `backend/CLAUDE.md` that **conflict** with each other (e.g., root says
   "use 4-space indentation," backend says "this subsystem uses 2-space indentation to
   match the legacy driver library"). Which one should win when Claude is working inside
   `backend/`, and why?
4. Why does it make sense for CLAUDE.md files to *combine* (both apply) rather than for
   the nested file to completely replace the root file?

### 5. (If you have Claude Code installed) Try it for real

Run Claude Code with working directory set to `fake_repo/backend/` and ask it something
like "what conventions should I follow while working in this directory?" — see whether
its answer reflects awareness of both files. Note: exact discovery/precedence behavior
can change between Claude Code versions, so treat this as a sanity check on the concept,
not a graded step.

## Check your work

Compare your `CLAUDE.md` files and `my_reasoning.md` against
`../../solutions/ex1_claude_md_hierarchy/`. There's no single "correct" CLAUDE.md
content — what matters is that your root file is genuinely project-wide, your backend
file is genuinely subsystem-specific, and your reasoning about precedence is sound.
