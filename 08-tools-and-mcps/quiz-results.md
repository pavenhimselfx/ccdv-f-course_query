# Domain 8 Quiz — My Results (2026-09-17)

Score: 6/8. See `quiz.md` for the original questions and the course's own
answer key/rationale — this file is my personal answer log plus reasoning
for each question, including why the two misses were wrong.

| Q | My answer | Correct | Result |
|---|-----------|---------|--------|
| 1 | B | B | ✅ |
| 2 | B | B | ✅ |
| 3 | A, D | A, D | ✅ |
| 4 | B | B | ✅ |
| 5 | A, C | A, C | ✅ |
| 6 | A | C | ❌ |
| 7 | A, C | A, C | ✅ |
| 8 | B | C | ❌ |

---

**Q1 — Response with `stop_reason: "tool_use"` and a `tool_use` block:
correct next step.** Answered B — correct. Claude never executes anything
itself; it only requests execution via a `tool_use` block, so the
developer's code must run the corresponding function and respond with a
`tool_result` block whose `tool_use_id` matches, so Claude can correlate
the result with its request. A misreads `tool_use` as an error state
(it's normal, expected output); C has it backwards (Claude requests, your
code executes); D would stall the conversation forever since
`stop_reason` never becomes `"end_turn"` until a `tool_result` is
supplied. This is exactly the mechanical loop
[ex1_tool_design_and_error_handling.py](exercises/ex1_tool_design_and_error_handling.py)
demonstrated, just run by the Agent SDK's `query()` internally instead of
hand-rolled.

**Q2 — Vague tool description/params causing malformed or skipped
calls.** Answered B — correct. The model relies entirely on a tool's
description and parameter documentation to decide when and how to call
it — there's no separate human-onboarding step the way there is for API
docs. "Processes an item" with an undocumented `data` field gives the
model nothing to work with, producing exactly the described symptoms. A
overstates the problem (tool use is generally reliable when tools are
well-specified); C is a real good practice but doesn't address the stated
vagueness symptom; D is simply false. This is the same principle I applied
writing ex1's tool descriptions — e.g. explicitly stating `create_order`
"DECREMENTS stock" and is "not reversible" so Claude only calls it once
inputs are confirmed.

**Q3 — Uncaught `ConnectionError` from a `create_invoice` tool after a
downstream timeout.** Answered A, D — correct. A is the central
error-handling practice: catch the exception, return structured
`tool_result` error content (typically `is_error: true`) instead of
letting it crash the loop — exactly what I implemented and verified for
all three tools in
[ex1_tool_design_and_error_handling.py](exercises/ex1_tool_design_and_error_handling.py)
(confirmed offline by calling each handler directly with bad inputs and
checking the `is_error` result). D is the idempotency guidance: a timeout
is exactly the scenario where a caller might retry and accidentally
double-create a mutating side effect, so idempotency support is sound
practice. B is false — Claude has no ability to detect a crashed process,
it only sees the transcript; a crash just stops the conversation. C
directly contradicts "a fabricated success is worse than a visible error."

**Q4 — Web search vs. `refund_customer`: implementation and governance.**
Answered B — correct. General web search suits a hosted/built-in tool;
`refund_customer` touches private internal billing data and must be a
custom client-side tool, and because it's consequential and hard to
reverse, is a strong candidate for a human-in-the-loop or policy-based
approval checkpoint before executing. A ignores that consequence/
reversibility (not implementation mechanics) should drive approval
requirements; C is actually unsafe (hosted tools can't reach private
internal systems); D is false given the stakes involved.

**Q5 — Near-duplicate tool pairs causing inconsistent selection.**
Answered A, C — correct. Merge or sharply differentiate overlapping tools
(A), and use actual wrong-tool-choice transcripts as evidence for where
the ambiguity lives and which pair to fix (C). B does the opposite of
what's needed (more overlapping tools makes selection strictly harder);
D also worsens it by removing the disambiguating information in tool
names.

**Q6 — Matching an MCP primitive to its purpose.** Answered A ("a
resource is a callable action with a JSON Schema of inputs that performs
a side effect"). **Wrong** — that's actually the definition of a *tool*,
mislabeled as "resource." Correct: **C** — a prompt is a reusable,
possibly parameterized message template an MCP server exposes for a
connected client to surface or inject. A and B each swapped the correct
behavior onto the wrong primitive name (A describes a tool but calls it a
resource; B describes a resource but calls it a tool) — I fell for
exactly that swap. The clean split to remember: **resource** = readable,
URI-addressed context/data, no side effects, no caller-supplied params;
**tool** = callable action with a JSON Schema of inputs, can have side
effects; **prompt** = a reusable message template. This is the same
mismatched-label shape as
[ex2_build_an_mcp_server.py](exercises/ex2_build_an_mcp_server.py)'s three
primitives — `get_current_time` (tool, has a side-effect-free but
argument-taking action), `server-info://about` (resource, URI-addressed,
zero arguments), `time_report` (prompt, a reusable message template) —
which I built and tested correctly, but didn't map back onto this quiz's
label-swap trap.

**Q7 — Deployment/transport choice for a new MCP server wrapping an
internal knowledge base.** Answered A, C — correct. A: stdio,
process-based launch is the simplest, lowest-overhead pattern for a
single local client/server pairing — exactly the transport
[ex2_build_an_mcp_server.py](exercises/ex2_build_an_mcp_server.py) used,
verified end-to-end through Claude Code as a real stdio client. C: the
LLM-powered application is always the MCP client and the server always
responds, regardless of transport — a fixed relationship, not something
transport choice changes. B is false (transport is a deployment decision
about reach/topology, not a hard limit on tool count — my own server
exposed a tool, a resource, and a prompt all over the same stdio
transport with no issue). D is also false — transport is a
deployment-layer detail underneath the protocol; it doesn't change which
primitives a server may expose.

**Q8 — Real-time shipment status via a proprietary logistics system,
consumed by exactly one internal application, no reuse planned.**
Answered B (Skill, "because it's fundamentally a multi-step procedure").
**Wrong** — correct: **C** (custom tool). This scenario is explicitly
about *reaching a new external system* Claude doesn't already have access
to — that's decision point 3/4 territory (bespoke logic, single
application, no reuse), not decision point 2's "procedure using tools
Claude already has." A Skill only fits when the needed tools already
exist and are reachable; nothing here says Claude already has a way to
query the logistics system — that access itself is the missing piece,
which is what a tool provides, not a Skill. This maps directly onto my
own [ex3_tools_vs_skills_vs_mcp_decision.md](exercises/ex3_tools_vs_skills_vs_mcp_decision.md):
Scenario 3 (the deletion checklist) was correctly a Skill *specifically
because* the tools already existed and were reachable; this quiz
scenario is structurally much closer to my Scenario 2 (bespoke logic, one
app, no existing access, no reuse) — same framework, and I got Scenario 2
right in my own exercise but missed the equivalent shape here.

---

## Pattern to remember

Both misses share one root cause: **applying the right concept to the
wrong label or the wrong condition-check**. Q6 had the right content
attached to the wrong primitive name (a tool's definition, labeled
"resource"). Q8 answered the wrong framework question first — jumping to
"is this a procedure?" (decision point 2) without first confirming
whether the tools even exist yet, when the scenario's real signal was "a
new external system, single app, no reuse" (decision points 3/4). Both
are things I demonstrably got right when actually *building* the
equivalent case in ex2 and ex3 — the gap wasn't understanding, it was
correctly mapping a new scenario's surface wording back onto the
underlying framework rather than pattern-matching on a surface cue
("sounds like steps" → Skill; "primitive with a schema" → the first name
that came to mind). Worth a deliberate pause next time: name which
decision-framework question actually applies *before* picking an answer
that merely sounds plausible.
