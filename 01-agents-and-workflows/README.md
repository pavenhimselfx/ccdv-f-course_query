# Domain 1: Agents and Workflows

**Exam weight: 14.7% of CCDV-F**

> **Cost note:** `exercises/ex1_workflow_vs_agent.py` and
> `exercises/ex3_manager_subagent_pattern.py` now run on the **Claude Agent SDK**
> (`claude-agent-sdk`), authenticated against a Claude.ai subscription via
> `CLAUDE_CODE_OAUTH_TOKEN` instead of a metered key — if you have a Team, Enterprise,
> Pro, or Max subscription, these two run at zero marginal cost. See
> `00-setup/README.md` section 1 for the one-time setup (`claude setup-token`,
> exporting the token, installing `claude-agent-sdk`). `exercises/ex2_basic_tool_use_loop.py`
> deliberately still uses the raw Messages API (its whole point is hand-rolling the
> tool-use loop the SDK would otherwise hide) and still needs a metered Console API
> key — see `00-setup/README.md` sections 2–3. Each exercise's own docstring says
> which path it needs.

This is an unofficial, independently-built self-study module preparing you for the
"Claude Certified Developer – Foundations" (CCDV-F) exam, blueprint version 1.0
(effective July 2026). It is not published or endorsed by Anthropic. Everything in
this module — explanations, exercises, and practice questions — is original
content written to teach the public blueprint's skills, not a reproduction of any
real exam item.

The blueprint breaks this domain into three skills:

| Skill | Weight |
|---|---|
| Agent Architecture | 4.5% |
| Agent Construction with Claude | 5.3% |
| Agent Patterns and Frameworks | 4.9% |

Read this file in order — each section builds on the last. Then work through
`exercises/` in order (`ex1` → `ex2` → `ex3`); each one assumes the intuition
built by the previous one. Check your work against `solutions/` only after you've
made a genuine attempt. Finish with `quiz.md`.

A note on currency: Claude's tooling in this space (the Agent SDK, hosted
deployment options, hooks APIs) moves quickly, and this module was written
against the author's knowledge as of early-to-mid 2026. Treat concrete API
names, method signatures, and product names here as "roughly right, verify
before you ship." The canonical, current source is always
[docs.claude.com](https://docs.claude.com) and the Claude Agent SDK
documentation. Concepts and decision criteria age much more slowly than API
surface — that's where this module puts most of its weight.

---

## 1. Agent Architecture (4.5%)

### 1.1 Workflow vs. agent: the core distinction

The single most important conceptual distinction in this domain — and the one
the exam leans on hardest — is the difference between a **workflow** and an
**agent**. Both involve calling an LLM one or more times to accomplish a task.
The difference is *who decides the sequence of steps*.

**A workflow is a fixed code path.** You, the developer, write the control
flow — the `if` statements, the loop bounds, the order of operations — and the
LLM is invoked at specific, predetermined points inside that flow to perform a
specific, bounded piece of reasoning (classify this, extract that, summarize
this). The LLM does not decide what happens next; your code does. If step 2
needs to run after step 1 regardless of what step 1's output says, that's
workflow logic. Chains, pipelines, routing-by-classification, and
parallelized-then-aggregated calls are all workflows in this sense, even
though each individual call to Claude is generative and non-deterministic in
its *output*. The *path* through the system is deterministic.

**An agent lets the LLM decide its own steps.** Instead of you hard-coding
"call Claude to extract fields, then call Claude to validate them, then call
Claude to decide if a human should review," you give Claude a goal, a set of
tools, and a loop: Claude looks at the current state, decides what to do next
(often by requesting a tool call), your code executes that tool and returns
the result, and Claude looks again — repeating until *Claude itself* decides
the task is complete (typically by returning a final text answer instead of
another tool call). The number of steps, their order, and even whether a
given tool gets called at all are not fixed in your code; they emerge from
the model's reasoning at run time. This is often called a "tool-use loop" and
it's the architectural heart of what "agent" means in this ecosystem — not
autonomy in some vague philosophical sense, but concretely: **the model
controls the loop, not your code.**

It's worth being precise about a common confusion: using an LLM at all does
not make something an agent, and having multiple LLM calls does not make
something an agent either. A three-step chain where Claude call #1's output
is fed into Claude call #2's prompt, always in that order, is a workflow — a
perfectly good one. What makes a system an agent is that the *loop
termination and step sequence* are under the model's control rather than
your code's.

### 1.2 Decision criteria: when to use which

Prefer a **workflow** when:

- The task has a known, boundable set of steps and you can enumerate them in
  advance. If you can draw the flowchart, you can probably hard-code the flow.
- Predictability, auditability, and cost control matter more than
  flexibility. A fixed number of LLM calls means a fixed (or tightly bounded)
  cost and latency, and every run takes the same shape, which makes it much
  easier to test, log, and reason about failures.
- The task is narrow enough that giving the model open-ended tool access
  would be pure surface area for error with no corresponding benefit — e.g.
  "classify this ticket into one of six categories" doesn't need an agent.
- You need strong guarantees about ordering (e.g., "never call the payment
  API before the fraud check has returned"). A workflow enforces that in code;
  an agent only enforces it if the model reliably chooses to, which is a
  probabilistic guarantee, not a hard one.

Prefer an **agent** when:

- The number and order of steps genuinely can't be known ahead of time
  because they depend on what earlier steps discover. Debugging a failing
  build, researching an open-ended question, or navigating a multi-page UI
  are classic examples: what you do next depends entirely on what you just
  learned.
- The task benefits from the model being able to recover from its own
  mistakes mid-task — e.g., try a tool call, see it fail, try a different
  approach — without you having to anticipate every failure mode in your
  control flow.
- You're willing to trade some predictability and cost-boundedness for
  flexibility and the ability to handle novel situations without new code.

In practice, many production systems are neither purely one nor the other:
a workflow with one step that is itself a small bounded agentic loop (e.g., a
research sub-step that gets up to five tool calls before it must return) is
extremely common, and recognizing that hybrid as legitimate — not a
contradiction — is itself something the exam may probe. The general framing
worth internalizing: **start with the simplest workflow that could plausibly
work, and reach for agentic autonomy only when the task's step sequence is
genuinely unpredictable in advance.** Agents are more expensive to run, harder
to test exhaustively, and harder to debug when something goes wrong, because
the failure could be in the model's reasoning about *what to do* rather than
just in the correctness of *what it produced*. That cost has to be justified
by a real need for adaptive step sequencing, not just because "agent" sounds
more impressive than "script."

### 1.3 Manager/supervisor hierarchies and subagents

Once a task is agentic, a second architectural question arises: should it be
*one* agent with one growing context, or *multiple* agents coordinating?

A **manager/supervisor pattern** (also called an orchestrator pattern) puts
one agent — the manager — in charge of decomposing a larger task into
subtasks and delegating each subtask to a separate agent invocation, a
**subagent**, then collecting and synthesizing the subagents' results into a
final answer. Structurally this looks like: manager reasons about the task →
manager dispatches subtask A to subagent A (a fresh Claude call/session with
only the information relevant to subtask A) → subagent A does its work and
returns a result → manager repeats for subtasks B, C, ... → manager combines
everything into a coherent final output. The manager may dispatch subagents
sequentially or in parallel, and it may use the results of one subagent to
decide whether it even needs to dispatch another.

Why give a subagent *isolated* context rather than just letting one agent do
everything in a single long-running loop? Several concrete benefits:

- **Context isolation.** A subagent that only sees its own subtask isn't
  distracted or biased by the transcript of unrelated exploration the manager
  or sibling subagents did. This matters a lot in practice: irrelevant tool
  calls, dead ends, and verbose intermediate output from other parts of the
  task can otherwise pollute the model's context and measurably degrade the
  quality of its reasoning on the thing actually in front of it right now
  ("context poisoning" or "context drift").
- **Parallelism.** Independent subtasks can be dispatched to subagents
  concurrently, which a single serial loop cannot do — this can turn a task
  that would take N sequential LLM round-trips into one that takes closer to
  the duration of the slowest branch.
- **Specialization.** A subagent can be given a narrower, more specific
  system prompt, a smaller and more targeted toolset, and even a different
  model tier suited to its subtask (a cheap/fast model for simple lookups, a
  stronger model for the subtask that needs deep reasoning), rather than one
  agent carrying a single system prompt and toolset broad enough to cover
  every possible subtask.
- **Context-window economy.** Each subagent's context stays small and
  focused, and only the *distilled result* — not the full working transcript
  — gets added back to the manager's context. This lets the overall system
  handle tasks whose total working context would never fit in one window.

The tradeoff is real complexity: multiple agent invocations to orchestrate,
results to reconcile (what if two subagents disagree?), more total API calls
and latency in the sequential-dispatch case, and a harder debugging story
because a failure could originate in the manager's decomposition, in a
subagent's execution, or in the manager's synthesis step. The pattern earns
its complexity when subtasks are genuinely separable (little need for one
subagent to know what another is doing while it works), when parallel
execution meaningfully reduces latency, or when specialization (different
prompts/tools/models per subtask) produces meaningfully better results than
one generalist agent could. For a task that's small enough to fit comfortably
in one context window and doesn't decompose into independent pieces, a single
agent is simpler, cheaper, and easier to reason about — don't reach for a
manager/subagent hierarchy by default.

---

## 2. Agent Construction with Claude (5.3%)

### 2.1 What the Claude Agent SDK is for

Everything described in section 1 — a tool-use loop, optional subagent
dispatch, context management — has to actually be *built*: something has to
send the messages, parse tool-use requests out of the response, execute the
requested tool, feed results back, decide when to stop, enforce permissions
around what tools may run and on what, and (usually) log/stream all of it.
The **Claude Agent SDK** is Anthropic's supported toolkit for building exactly
this kind of harness in code, rather than writing the loop by hand every
time. Conceptually, it packages up:

- The tool-use loop itself (send messages, detect `tool_use` blocks, dispatch
  to your tool implementations, append `tool_result` blocks, repeat until a
  stopping condition).
- A permissions layer for gating what an agent is allowed to do — e.g.
  requiring approval before a filesystem-writing or shell-executing tool
  actually runs, or restricting which tools/paths are reachable at all.
- Hooks (see 2.3) for injecting your own deterministic code at defined points
  in that loop.
- Session and context-management conveniences (continuing a conversation,
  managing what stays in context across turns).
- Support for built-in and custom tools, and for structuring subagents.

The reason this matters architecturally is that "hand-roll a `while True:`
loop around the Messages API" (which you'll do yourself in Exercise 2) and
"use the Agent SDK" are two points on the same spectrum, not two unrelated
things. The hand-rolled loop is the mental model; the SDK is a
production-hardened, batteries-included implementation of that same mental
model, with permissioning, hooks, and operational concerns already solved so
you don't reinvent them per project. Knowing when the raw Messages API is
enough (a simple, low-stakes tool-use loop) versus when you want the SDK's
guardrails (anything touching the filesystem, shell, external side effects,
or that needs auditable permissioning) is itself an exam-relevant judgment
call.

This domain's exercises are set up to let you see both layers directly
rather than just read about the distinction. Exercise 2 hand-rolls the raw
tool-use loop against the Messages API — you'll build the `tool_use`/
`tool_result` mechanics yourself. Exercises 1 and 3 build the same kind of
loop (a tool-calling agent in Exercise 1, isolated subagent calls in
Exercise 3) on top of the Claude Agent SDK instead, where that same
machinery is handled for you. Working through both is genuinely useful exam
prep, not redundant repetition: this skill's blueprint entry explicitly
covers "custom agent loops and harnesses" (what Exercise 2 builds) alongside
"the Claude Agent SDK" (what Exercises 1 and 3 use) as separate tested
points, and having hand-built the former makes it much easier to say
precisely what the latter is abstracting away for you.

### 2.2 Deployment models: self-hosted vs. Anthropic-hosted

Once an agent is built, it has to run somewhere, and Anthropic offers more
than one shape of "somewhere":

- **Self-hosted**: you deploy the agent harness (whether hand-rolled or built
  on the Agent SDK) on your own infrastructure — your servers, your
  containers, your cloud account — calling the Claude API yourself. You own
  the full operational surface: compute, scaling, secrets management,
  sandboxing for any tool that executes code or touches the filesystem,
  logging/observability, and update cadence. This gives you maximum control
  over environment, data residency, and integration with your existing
  infra, at the cost of having to build and maintain all of that
  infrastructure yourself.
- **Anthropic-hosted / managed**: Anthropic runs the agent execution
  environment for you (the specifics of which managed offerings exist and
  what they're called shift over time — check current docs), trading some of
  that infrastructure control for reduced operational burden: you don't
  manage the compute or sandboxing yourself, and you get an integration
  surface (API/webhooks/etc.) rather than a server you deploy.

The decision criteria mirror any build-vs-managed-service tradeoff:
self-hosting wins when you need tight control over the execution
environment, custom infrastructure integration, specific compliance/data
residency requirements, or you're already running comparable infrastructure
elsewhere; managed hosting wins when you want to minimize operational
overhead and get to a working deployment faster, and your requirements fit
within what the managed offering exposes. This is an area where exact product
names and capabilities are likely to have moved since this module was
written — verify current specifics at docs.claude.com before relying on any
particular claim about what's available.

### 2.3 Hooks: deterministic actions inside a nondeterministic loop

An agent loop is, by design, largely under the model's control — that's what
makes it an agent rather than a workflow. But "largely" is doing real work in
that sentence: production agents almost always need *some* guarantees that
don't depend on the model choosing correctly every time. **Hooks** are the
mechanism for that: they let you attach your own deterministic code to fixed
points in the agent loop's lifecycle — for example, before a tool executes,
after a tool executes, when the agent is about to finish, or when a new
session starts — so that certain logic runs *every time*, regardless of what
the model decided to do.

Typical uses for hooks:

- **Guardrails/validation**: block or rewrite a tool call before it executes
  (e.g., refuse a shell command matching a deny-list, regardless of whether
  the model "meant well").
- **Auditing/logging**: record every tool call and its result to an
  append-only log for compliance, independent of anything the model itself
  reports.
- **Deterministic side effects**: always run a formatter after a file-editing
  tool, always post a status update after a particular step, always persist
  session state at defined checkpoints.
- **Permission enforcement**: require human approval before a sensitive tool
  actually runs, implemented as code that cannot be talked out of running by
  a cleverly-phrased model output.

The unifying idea is that hooks give you a place to put logic that *must*
hold regardless of model behavior — the deterministic backbone underneath a
nondeterministic loop — rather than trying to get the same guarantee purely
through prompting ("please always log your tool calls"), which is inherently
best-effort. This is conceptually the same reason workflows are attractive
in section 1.1: determinism where you need it, model judgment where you want
flexibility. Hooks let you have both *inside a single agent*, instead of
forcing an all-or-nothing choice between "workflow" and "agent."

---

## 3. Agent Patterns and Frameworks (4.9%)

### 3.1 Recurring design patterns

A handful of patterns recur across almost every non-trivial agent, independent
of which specific SDK or framework you use to build it:

- **Tool-use loop.** Already covered above — the foundational pattern.
  Everything else in this section is really a refinement or extension of it.
- **Sub-agents.** Also covered above (section 1.3) as an architectural
  choice; as a *pattern* it shows up not just in explicit manager/subagent
  designs but in smaller forms too — e.g. spinning off an isolated,
  throwaway agent call to do one bounded piece of research or verification
  and return only a summary, without that call's full transcript ever
  entering the main agent's context.
- **Memory.** Two distinct kinds are worth keeping separate in your head.
  *Short-term / session memory* is just the conversation transcript
  (including tool calls and results) that lives within the current context
  window — it disappears when the session ends unless something persists
  it. *Long-term / persisted memory* is information deliberately written out
  to durable storage (a file, a database, a vector store) so that it survives
  across sessions and can be retrieved in a future run — e.g. a running
  summary of user preferences, facts learned in a previous conversation, or
  progress notes on a multi-day task. Building a good agent often means
  deciding explicitly what belongs in each: everything needed for the
  current step stays in short-term context, and anything that needs to
  outlive the session gets deliberately written to long-term storage rather
  than assumed to persist on its own (it won't — the context window is not a
  database).
- **Context-window management.** A long-running agent accumulates a
  transcript — every tool call, every tool result, every intermediate
  thought — and eventually that transcript will not fit in the model's
  context window, or even before hitting the hard limit, a very long, mostly
  irrelevant-by-now transcript degrades output quality and wastes tokens on
  every subsequent call. The practical answers are **pruning** (dropping or
  truncating old, no-longer-relevant content — e.g., the full output of a
  tool call from many steps ago, once its conclusion has been acted on) and
  **compaction/summarization** (periodically replacing a stretch of the
  transcript with a shorter summary that preserves what still matters, so
  the agent doesn't have to re-read every raw tool result to remember what
  happened). Recognizing that this is a *design requirement* for any agent
  expected to run for many steps — not an edge case you can ignore until it
  breaks — is exam-relevant.

### 3.2 Agentic frameworks: third-party abstractions over the same loop

Beyond Anthropic's own Agent SDK, a broader ecosystem of open-source
frameworks exists for building agents and multi-step LLM workflows,
independent of any one model provider. You should recognize these by name
and roughly what problem they solve, without needing deep hands-on expertise
in all of them for this exam:

- **LangGraph**: a framework for defining agents and multi-step LLM
  applications as explicit graphs — nodes representing steps (including LLM
  calls and tool calls) and edges representing control flow between them,
  including conditional branches and cycles (loops). It's particularly
  suited to workflows and agents where you want to visualize and reason
  about the control-flow graph explicitly, including hybrids that mix fixed
  workflow segments with agentic loops.
- **PydanticAI**: an agent framework built around Pydantic's data-validation
  model, emphasizing type-safe, structured inputs and outputs for agents and
  tool calls — useful when you want strong static guarantees about the shape
  of data flowing into and out of the model, rather than parsing loosely
  typed text or dicts by hand.
- **Strands** (Strands Agents): an agent-building SDK/framework centered on
  a model-driven tool-use loop, similarly aimed at making it straightforward
  to define tools and let a model orchestrate their use toward a goal.

The exam-relevant takeaway is not "memorize each framework's API surface" but
rather: **these are all different abstractions over the same underlying
primitives** — an LLM, a set of tools described to it, a loop that executes
requested tool calls and feeds results back, and (in most of them) some
facility for multi-step graphs or multi-agent composition. Recognizing that
commonality is what lets you evaluate a new or unfamiliar framework quickly:
ask "how does this represent the tool-use loop, and how does it handle
control flow between steps?" and you'll generally be able to map it onto the
concepts in this README regardless of its specific vocabulary. None of these
frameworks are Anthropic products; they're independent, third-party
abstractions that happen to work well with Claude (and typically with other
model providers too), which is a distinction worth keeping straight from the
Anthropic-authored Claude Agent SDK covered in section 2.

---

## Where to go from here

Work through `exercises/ex1_workflow_vs_agent.py`, then `ex2`, then `ex3`, in
that order. Each exercise's docstring explains what to build and how to know
you've succeeded, and notes that you can work through it by reading and
predicting output even without an API key configured. Compare your work
against `solutions/` afterward. Finish with `quiz.md` to self-check your
understanding of all three skills in this domain before moving to the next
module.
