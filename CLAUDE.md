# CLAUDE.md

This repo is a self-study course for the Claude Certified Developer – Foundations
(CCDV-F) exam. See `README.md` for the full course structure, domain weights, and
recommended order. This file is about *how to work through it with a developer*,
based on a full run-through that already happened here — follow this path for the
next developer unless they ask for something different.

## Environment

- Python virtual environment lives at `.venv/` (see `00-setup/README.md`). Use its
  interpreter (`.venv/Scripts/python.exe` on Windows) rather than a bare `python`
  on PATH, which may resolve to a different, unrelated install.
- Two auth paths exist: `CLAUDE_CODE_OAUTH_TOKEN` (subscription, via
  `claude setup-token`, free under Team/Enterprise) and `ANTHROPIC_API_KEY`
  (metered Console key). `00-setup/README.md` has a table of exactly which
  exercises need which — several run entirely free on subscription auth.
- `.mcp.json` at the repo root registers Domain 8's `ex2` MCP server with Claude
  Code for `ex2b`'s live-client test — safe to leave in place across a fresh
  attempt at this course.

## Recommended workflow with a new developer

**First, ask how hands-on they want to be with the code**, rather than assuming.
The path described below assumes a developer who wants Claude to implement each
exercise's TODOs directly while they read, run, and discuss — that's a legitimate
and common preference, but confirm it rather than assuming it, and check memory
for any saved preference on this before asking again.

For each exercise, in order, within each domain (also taken in order):

1. **Implement the TODOs directly.** Read the exercise's docstring/instructions
   fully first — several exercises assume specific SDK shapes (the `@tool`
   decorator, `create_sdk_mcp_server`, MCP's `FastMCP`/`MCPServer`) that drift
   between versions, which is the exercise's own explicit warning, not a
   hypothetical.
2. **Actually run it whenever a credential is available.** Don't stop at "it
   compiles." A large share of the real value in this course came from running
   exercises for real and hitting genuine, current drift:
   - Stale model names (e.g. `claude-sonnet-4-5`, `claude-opus-4-latest`) needed
     correcting to the current lineup in nearly every domain.
   - `mcp` 2.x renamed `FastMCP` to `MCPServer` and moved its import path
     (`mcp.server.fastmcp` → `mcp.server.mcpserver`).
   - The `anthropic` SDK's HTTP dependency is `httpx2`, not `httpx`, in this
     environment.
   - `temperature`/`top_p`/`top_k` are deprecated on newer-generation models in
     favor of `output_config.effort` — but support is model-specific, not
     SDK-version-specific (verify per model, don't assume).
   - A `thinking` content block can precede the `text` block once reasoning is
     involved — extract response text by filtering `block.type == "text"`,
     never by indexing `response.content[0]` directly.
   When something doesn't work as the exercise assumes, treat it as a real
   finding worth fixing and explaining, not an obstacle to route around quietly.
3. **When a bug turns up — including one an exercise's own inline hint
   suggested — fix it and say why.** Several exercises' own suggested
   implementations had real, confirmable bugs (e.g. a `datetime` + `timedelta`
   offset pattern that produced a technically-inconsistent ISO timestamp).
   Verify with a direct test before and after the fix; don't just trust that a
   fix "should" work.
4. **Record reflection/observation sections in the exercise file itself**,
   as comments, grounded in real output actually observed — not a hypothetical
   prediction — whenever a live run is possible. This makes the file useful on
   its own later, without needing to dig through chat history.
5. **Compare against `solutions/` afterward**, and report real differences
   honestly (a gap, a sharper phrasing, an added consideration) rather than
   claiming a match that isn't precise.

### After finishing a domain's exercises

Append a **"Key takeaways from working the exercises"** section to that domain's
`README.md` — concrete, empirical findings from what was actually built and run
(bugs found, real measured numbers, surprising results), not a restatement of the
conceptual material already in the README.

### Taking a domain's `quiz.md`

- Present questions interactively. A 4-option single-select question fits the
  answer-picker tool directly; a 5-option "select two" question doesn't fit that
  tool's option limit and needs to be posed as plain text in the same message.
- No hints, no reactions, no discussion before every question in the current
  batch is answered.
- Grade honestly afterward with full reasoning for *every* question, not just
  the misses — cross-link misses back to the specific exercise where the same
  concept was already built, when there is one.
- Save results to `<domain>/quiz-results.md` — see "Keep out of git" below.

### The capstone practice exam (`09-practice-exam/practice-exam.md`)

This file is explicitly designed to simulate real exam conditions: timed, solo,
**no AI assistance**, one sitting. That's a real conflict with the interactive
quiz pattern used for the domain quizzes — **ask the developer how they want to
run it** rather than assuming the same interactive style applies, since using
Claude as a live Q&A partner here works against the file's own stated purpose.

Before or while administering it, **check whether the answer key has a
structural position bias** (e.g. the correct option landing in the same letter
too often) rather than trusting it's randomized. This course's own practice exam
had exactly that defect — the correct answer was "B" in ~89% of single-select
items — discovered only because it was asked about directly. If found, rebalance
option positions (keep each option's actual text and correctness, just change
which letter carries it) rather than continuing to administer a biased key.

Save results to `09-practice-exam/practice-exam-results.md` — gitignored, same
reasoning as the quiz results.

## Keep out of git

`quiz-results.md` (any domain) and `09-practice-exam/practice-exam-results.md`
are personal performance records — a specific developer's answers, mistakes, and
self-reflection — not course content, even though the reasoning inside them has
real educational value. Both patterns are already in `.gitignore`. If this repo
is shared with other learners, don't re-track these; each developer should
generate and keep their own copies locally.
