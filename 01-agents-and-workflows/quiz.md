# Domain 1 Quiz: Agents and Workflows

**This is original practice content written for this unofficial self-study
course.** These 8 questions are illustrative practice items only — they are
not reproductions of, or drawn from, the real CCDV-F exam item bank. Question
style (scenario framing, "select N" instructions, answer format) is modeled
on the tone of the sample questions published in the official exam guide,
but the content itself is original.

Each question states how many answers to select. Work through all 8, then
check your answers against the Answer Key and Rationale section at the end.

---

**Question 1** (select 1)

A team needs to process end-of-day sales reports: for every report, extract
the total revenue and top-selling item, then always email a fixed-format
summary to the regional manager. The steps, their order, and their number
never vary from report to report. Which architecture best fits this
requirement, and why?

A. An agent with a single `send_email` tool, because agents are more capable
   than workflows in general.
B. A workflow, because the step sequence is fully known in advance and
   doesn't depend on what any individual report contains.
C. A manager/subagent hierarchy, because email sending should be isolated
   from data extraction.
D. An agent with no tools at all, relying purely on the model's own
   judgment to decide when to stop.

---

**Question 2** (select 2)

Which TWO of the following are accurate statements about the distinction
between a workflow and an agent?

A. A system that makes multiple sequential calls to Claude is automatically
   an agent, regardless of how the calls are sequenced.
B. In an agent, the model itself decides how many tool calls to make and
   when the task is complete, rather than that being fixed in code ahead of
   time.
C. A workflow can still call an LLM at every step; what makes it a workflow
   is that the code controls the sequence and stopping point, not the model.
D. Agents are strictly better than workflows because they can handle any
   workflow's task at equal or lower cost.

---

**Question 3** (select 1)

A support-ticket triage system currently hard-codes: "always classify the
ticket, then always look up the customer's account tier, then always route
to one of four fixed queues based on both results." A team member proposes
converting it to a full agentic loop with a dozen tools (refund lookup,
account lookup, escalation, sentiment check, etc.) so it can "handle
anything." What is the strongest architectural concern with this proposal
as described?

A. Agents cannot use more than a handful of tools at once, so a dozen tools
   would exceed a hard platform limit.
B. The current task's steps and their order are already fully known and
   bounded, so introducing model-controlled step sequencing trades away
   predictability and cost-boundedness without a corresponding need for
   adaptive step sequencing.
C. Hooks cannot be attached to workflows, only to agents, so the team would
   lose auditability by staying with a workflow.
D. Subagents are required any time more than one tool is involved.

---

**Question 4** (select 1)

In a manager/subagent pipeline, each subagent is dispatched with an
isolated context containing only its own subtask, rather than the full
transcript the manager has accumulated. What is the primary architectural
reason for this isolation?

A. Isolated contexts are required by the Claude API and cannot be avoided.
B. It prevents unrelated information (other subtasks, dead ends, verbose
   intermediate output) from biasing or distracting the subagent's
   reasoning on its own narrow task, and keeps each subagent's context
   small enough to stay within budget as the number of subtasks grows.
C. It guarantees that subagents will always produce identical output given
   the same subtask, removing model nondeterminism.
D. It allows the subagent to use a completely different tool-calling
   protocol than the manager.

---

**Question 5** (select 1)

A developer is deciding between hand-rolling a custom tool-use loop directly
against the Messages API and building on the Claude Agent SDK for a new
internal tool that will execute shell commands and write files on a
developer's machine, with a requirement that certain destructive actions
require human approval before running. Which factor most strongly favors
using the Agent SDK here rather than a minimal hand-rolled loop?

A. The Agent SDK is required to use tools at all; the raw Messages API has
   no tool-use support.
B. The task needs permissioning around sensitive actions (approval gating
   for destructive operations) and operational concerns the SDK provides
   out of the box, rather than needing to be reimplemented and
   independently hardened by hand.
C. Hand-rolled loops cannot call more than one tool per turn.
D. The Agent SDK eliminates the need to define tool schemas.

---

**Question 6** (select 2)

Which TWO of the following are legitimate uses of hooks in an agent
harness, consistent with the role of hooks as described in this domain?

A. Guaranteeing that every tool call is written to an audit log, regardless
   of what the model's own text output claims it did.
B. Making the model choose better which tool to call next by improving its
   system prompt.
C. Blocking a tool call that matches a deny-listed pattern before it
   executes, independent of how the model justified making that call.
D. Increasing the model's context window size for a single session.

---

**Question 7** (select 1)

A long-running coding agent has been active for several hours across many
tool calls (file reads, test runs, search results). The team notices output
quality degrading and, separately, is approaching the model's context-window
limit. Which technique directly addresses BOTH concerns, as discussed in
this domain?

A. Switching from an agent architecture to a workflow architecture without
   changing anything else about what information is retained.
B. Periodically compacting/summarizing older parts of the transcript (and
   pruning content, like the full output of long-past tool calls, that's no
   longer needed) so that what remains in context is both smaller and more
   relevant.
C. Increasing max_tokens on every API call.
D. Adding more tools to the agent's toolset.

---

**Question 8** (select 1)

A developer is evaluating an unfamiliar third-party agentic framework for
the first time and wants to quickly understand how it works, using the
mental model built in this domain. Which question is most useful to ask
first?

A. What programming language is the framework's own source code written in?
B. How many GitHub stars does the framework have?
C. How does this framework represent the tool-use loop, and how does it
   handle control flow (branching, looping, multi-step/multi-agent
   composition) between steps?
D. Which specific version of Claude does the framework's documentation
   mention by name?

---

## Answer key and rationale

**Q1: B.**
The task's steps (extract revenue, extract top item, send fixed-format
email) are fully known in advance and never vary by input — that's the
textbook case for a workflow, not an agent. (A) is wrong because "agents are
more capable in general" is not the deciding factor and isn't even
consistently true — capability isn't the axis that matters, predictability
of step sequence is. (C) is wrong because nothing about this task decomposes
into independent subtasks worth isolating; a manager/subagent hierarchy adds
coordination overhead this task doesn't need. (D) is wrong on its face — a
tool-less agent couldn't send an email at all, and more fundamentally,
"purely the model's own judgment" is precisely the property this fixed-order
task doesn't need.

**Q2: B and C.**
(B) is the core definition of an agent: model-controlled step count and
stopping condition. (C) correctly identifies that "workflow" is about who
controls the sequence, not about whether an LLM is involved — a workflow can
call Claude at every single step and still be a workflow. (A) is wrong: a
fixed sequential chain of Claude calls is a workflow, not an agent, no
matter how many calls there are — sequencing controlled by code, not by the
model's own decisions, is the defining trait. (D) is wrong and overstated:
agents are not strictly better or cheaper; they trade predictability and
cost-boundedness for flexibility, which is a cost, not a pure win.

**Q3: B.**
The concern described in this domain's decision criteria is precisely this:
when steps and their order are already fully known and bounded, converting
to a model-controlled loop sacrifices predictability, auditability, and
cost-boundedness without buying anything, since there's no genuine
unpredictability in the step sequence for the added flexibility to help
with. (A) is a fabricated hard limit not supported by anything in this
domain. (C) is false — hooks are described as applying to agent loops for
injecting deterministic logic; nothing says a workflow "loses" auditability
it already has via its own fixed code path (if anything a workflow's fixed
path is inherently more auditable). (D) is a fabricated rule; subagents are
a judgment call based on task decomposability, not a requirement triggered
by tool count.

**Q4: B.**
This restates the two concrete reasons given for context isolation: avoiding
context pollution/drift from irrelevant material, and keeping context size
under control as subtasks scale. (A) is false — nothing about the Claude API
requires this; it's a deliberate architectural choice the developer makes.
(C) is false — isolating context does not make an LLM deterministic; the
model can still produce different output on different runs of the same
prompt. (D) is a fabricated claim with no basis — subagents use the same
tool-calling mechanics as the manager, just with a different, narrower
context.

**Q5: B.**
The scenario specifically calls out sensitive, destructive actions needing
approval gating — exactly what the Agent SDK's permissioning layer (and
hooks) are built to provide already, versus reimplementing and independently
hardening that logic by hand. (A) is false — the raw Messages API does
support tool use (that's exactly what Exercise 2 builds by hand without the
SDK). (C) is a fabricated limitation; a single turn can include multiple
tool_use blocks. (D) is false — you still define tool schemas whether or not
you use the SDK.

**Q6: A and C.**
Both are stated uses of hooks: deterministic, always-runs auditing
independent of the model's self-report, and blocking/validating a tool call
before execution regardless of the model's stated justification — hooks
exist to provide guarantees that don't depend on the model behaving a
particular way. (B) is not a hook use — improving a system prompt is a
prompting change, not deterministic code attached to a fixed point in the
loop, and it doesn't guarantee anything (the model could still ignore it).
(D) is unrelated to what hooks do; hooks don't change the size of the
context window.

**Q7: B.**
Compaction/summarization plus pruning of stale content is exactly the
technique this domain identifies for long-running agents: it reduces what's
in context (addressing the window-limit concern) while removing irrelevant
material that would otherwise degrade reasoning quality (addressing the
quality-degradation concern) — one technique, both problems, because they
share the same root cause (context bloated with material that's no longer
useful). (A) doesn't address either concern — swapping architecture without
changing what's retained in context does nothing to the actual transcript
size or relevance. (C) doesn't shrink the input context at all — max_tokens
governs the output length of a single response, not how much prior
transcript is sent in. (D) would make both problems worse, not better, by
adding more potential tool-call transcript into an already-strained context.

**Q8: C.**
This domain's explicit framing for evaluating any unfamiliar agentic
framework is to look past its specific vocabulary and ask how it represents
the shared underlying primitives — the tool-use loop and control flow
between steps — since that mapping is what lets you transfer understanding
from one framework to another. (A), (B), and (D) are all surface details
(implementation language, popularity, a documentation mention) that tell you
nothing about the framework's actual architecture or how to reason about
agents built with it.
