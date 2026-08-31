# Domain 1 Quiz — My Results (2026-08-31)

Score: 6/8. See `quiz.md` for the original questions and the course's own
answer key/rationale — this file is my personal answer log plus reasoning
for each question, including why the two misses were wrong.

| Q | My answer | Correct | Result |
|---|-----------|---------|--------|
| 1 | A | B | ❌ |
| 2 | B, C | B, C | ✅ |
| 3 | B | B | ✅ |
| 4 | B | B | ✅ |
| 5 | B | B | ✅ |
| 6 | A, C | A, C | ✅ |
| 7 | A | B | ❌ |
| 8 | C | C | ✅ |

---

**Q1 — Sales report emailer.** Answered A (agent, "agents are more capable
than workflows in general"). Correct: **B**, workflow. "More capable in
general" is never the deciding factor on this exam — the deciding factor is
whether the step sequence is fixed and known in advance. Here it always is:
extract revenue, extract top item, send one fixed-format email, every
report, no exceptions. That's a workflow by definition, regardless of how
capable an agent could theoretically be at the same task.

**Q2 — Workflow vs. agent, pick 2.** Answered B, C — correct. B: an agent is
defined by the *model* deciding call count and stopping point, not code
deciding it ahead of time. C: a workflow can still call an LLM at every
step — what makes it a workflow is that the code controls sequencing and
stopping, not the presence or absence of LLM calls. Rejected A (call count
alone doesn't make something an agent — a fixed chain of N calls is still a
workflow) and D (agents are not strictly better/cheaper; flexibility is
traded for predictability, not a pure win).

**Q3 — Triage system, convert to full agentic loop?** Answered B — correct.
The steps and order here are already fully known and bounded (classify →
look up tier → route to one of four queues). Converting that to a
model-controlled loop with a dozen tools sacrifices predictability,
auditability, and cost-boundedness without buying anything, since there's no
real unpredictability in the step sequence for that flexibility to help
with. "Handle anything" is a solution to a problem this system doesn't have.

**Q4 — Why isolate subagent context?** Answered B — correct. Isolation
exists to (1) keep irrelevant material — other subtasks, dead ends, verbose
intermediate output — from biasing the subagent's reasoning on its own
narrow task, and (2) keep each subagent's context small and bounded even as
the number of subtasks grows. Not an API requirement (A), doesn't remove
model nondeterminism (C), and has nothing to do with tool-calling protocols
(D).

**Q5 — Hand-rolled loop vs. Agent SDK for a destructive-action tool.**
Answered B — correct. The scenario's requirement — human approval gating
before destructive shell/file actions — is exactly the kind of
permissioning and operational concern the Agent SDK already provides,
versus reimplementing and independently hardening that logic by hand in a
custom loop. Not because the raw API lacks tool support (A, false — that's
literally what Exercise 2 hand-built), and not because of any real
limitation on tool calls per turn (C) or schema requirements (D).

**Q6 — Legitimate uses of hooks, pick 2.** Answered A, C — correct. Hooks
exist to provide guarantees that don't depend on the model behaving a
particular way: an audit log that's written regardless of what the model's
own text claims (A), and blocking a disallowed tool call before it executes
regardless of the model's stated justification (C). Improving a system
prompt (B) is a prompting change, not deterministic code at a fixed point in
the loop — the model could still ignore it. Context window size (D) is
unrelated to what hooks do entirely.

**Q7 — Long-running agent: quality degrading + near context limit.**
Answered A (switch agent → workflow, without changing what's retained).
Correct: **B**, compaction/pruning. The question explicitly says "without
changing anything else about what information is retained" — that phrase is
the tell that A doesn't touch the actual root cause, which is stale content
bloating the transcript. Relabeling the architecture doesn't shrink
anything if the same information stays in context. You need an actual
content-reduction technique — periodically summarizing older transcript and
pruning content (like full past tool-call output) that's no longer
needed — which shrinks context size (fixing the window-limit problem) and
removes irrelevant material (fixing the quality-degradation problem) in one
move, since both problems share the same root cause.

**Q8 — Evaluating an unfamiliar agent framework.** Answered C — correct.
The useful first question is how the framework represents the tool-use loop
and handles control flow (branching, looping, multi-step/multi-agent
composition) — the shared underlying primitives that transfer across any
framework. Source language (A), GitHub popularity (B), and a documentation
mention of a specific Claude version (D) are all surface details that say
nothing about the framework's actual architecture.

---

## Pattern to remember

Both misses (Q1, Q7) picked an answer that sounded architecturally
sophisticated but didn't actually address the mechanism in question:
- Q1: "agents are more capable" — capability is never the deciding axis;
  fixed-vs-variable step sequence is.
- Q7: "switch architecture labels" — relabeling isn't the same as changing
  what's actually in context; only a real content-reduction technique fixes
  a context-bloat problem.

General tell for this exam: an answer that changes a label/architecture
*without* changing the underlying mechanism that actually causes the
problem is usually a distractor.
