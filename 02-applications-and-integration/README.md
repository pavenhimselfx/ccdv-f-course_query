# Module 02 — Applications and Integration

> **Cost note:** `ex1` and `ex6` (written/design exercises) need no live calls at all. `ex2`
> through `ex5` exercise raw Messages API mechanics (streaming, vision, prompt caching, batch
> API, async concurrency) directly, so they need a metered Console API key — see
> `00-setup/README.md` section 3 for the full free-vs-metered breakdown across this course.

This module corresponds to **Domain 2: Applications and Integration** of the CCDV-F exam
blueprint (v1.0, effective July 2026) — worth **33.1%** of the exam, the single largest
domain. It's also the most practical domain: it's about how you actually build software
around the Claude API, not just how you write a good prompt.

This is an unofficial, independently-built self-study course inspired by the published
CCDV-F exam blueprint. It is not written or endorsed by Anthropic, and none of the
questions in this module's `quiz.md` are reproductions of real exam items — they are
original practice content written in a similar style, same as the blueprint's own sample
questions are described as illustrative only.

The six skills in this domain, with their individual blueprint weights:

| Skill | Weight |
|---|---|
| Understanding Requirements | 3.4% |
| Systems Life Cycle | 2.8% |
| Claude API Mechanics | 6.8% |
| Software Engineering Foundations | 7.4% |
| Claude Application Design | 8.6% |
| Configuration Management | 4.1% |

A note before you start: the Claude platform (SDK versions, exact parameter names, model
names, pricing, product names) moves fast. Everything below reflects my best understanding
as of this writing, but treat [docs.claude.com](https://docs.claude.com) as the tiebreaker
whenever something here looks stale or doesn't match what you see in practice — especially
exact method signatures, field names, and current model/product names.

---

## 1. Understanding Requirements (3.4%)

Before you write a line of code that calls Claude, you need to know what you're actually
building and what constraints it has to satisfy. The blueprint frames this as **functional
and infrastructure requirements based on business requirements and solution architecture**
— which is a fancy way of saying: translate "the business wants X" into "the system must do
Y, and it must run in environment Z."

**Functional requirements** describe *what the system does*, in terms a non-engineer could
verify: "the tool answers employee questions about the HR policy document," "the tool
refuses to answer questions about compensation for anyone other than the requesting
employee," "the assistant summarizes a support ticket in under 150 words." For a
Claude-powered feature, functional requirements typically cover:

- What inputs the system accepts (free text? documents? images? structured forms?)
- What outputs it must produce, and in what shape (prose? JSON matching a schema? a
  citation-backed answer?)
- What the system must *never* do (leak another tenant's data, fabricate a policy that
  doesn't exist, take an irreversible action without confirmation)
- Who the users are and what they're allowed to ask for

**Infrastructure (non-functional) requirements** describe *how well* and *under what
constraints* the system must operate — and this is where a lot of Claude-specific
architecture decisions get made:

- **Latency**: "sub-5-second responses" rules out some patterns (e.g., long extended-thinking
  budgets, or waiting on a same-request batch job) and pushes you toward streaming so the
  user perceives a fast first token even if generation takes longer.
- **Cost**: a high-volume, low-margin feature might need a smaller/cheaper model, prompt
  caching for repeated context, or the batch API for anything that isn't user-facing.
- **Throughput / concurrency**: how many requests per second, and does that call for async
  HTTP, connection pooling, or queuing?
- **Compliance and data residency**: does the data need to stay within a specific cloud
  region or vendor boundary? This can push you toward invoking Claude through a particular
  cloud platform's model-hosting offering rather than Anthropic's own API, or toward
  specific data-retention settings.
- **Tenant isolation**: "must never leak from other tenants' data" is an infrastructure
  requirement that shapes how you construct prompts (never concatenate multiple tenants'
  context into one call), how you scope any retrieval step, and how you log/cache (a shared
  cache keyed only by prompt content could leak across tenants if you're not careful about
  what's in the cached prefix).
- **Availability and failure behavior**: what happens when the API errors, rate-limits, or
  times out? Requirements should say so explicitly (e.g., "falls back to a cached answer,"
  "shows a retry button," "never fails silently").

Good requirements gathering produces a short, explicit list of both kinds, because
architecture decisions later in this module — model choice, streaming vs. batch, caching,
sync vs. async — are almost always *justified by* one of these requirements. On the exam,
expect scenario questions that describe a business need and ask you to pick the
requirement, or the architecture choice that requirement implies.

## 2. Systems Life Cycle (2.8%)

This skill is about applying standard **SDLC** (Software/Systems Development Life Cycle)
thinking to Claude-powered features specifically. The classic stages — plan, design, build,
test, deploy, operate, maintain — all still apply; what changes is what happens at each
stage when an LLM is a core system component.

- **Plan**: capture the functional/infrastructure requirements above; decide up front
  whether this is a realtime, user-facing feature or a batch/offline workload — that
  decision ripples through every later stage.
- **Design**: choose the model family/size, decide on the API features you'll need
  (tools? vision? extended thinking? streaming?), sketch the prompt/context architecture,
  and design the data flow so sensitive data only reaches Claude when and how it's
  supposed to.
- **Build**: implement against the Messages API (or an SDK), write the system prompt,
  define tool schemas, wire up error handling and retries.
- **Test**: this is where LLM systems differ most from traditional software — you need
  *evaluations* (structured test sets with expected behaviors, not just unit tests) in
  addition to conventional tests, because outputs are non-deterministic. (Domain 4 of this
  course covers eval/testing/debugging in depth; here, just know it's a distinct SDLC stage
  for Claude apps, not a stage you skip because "it's just a prompt.")
- **Deploy**: roll out behind a flag or to a subset of traffic where possible; pin model
  versions (see Configuration Management below) so a deploy doesn't silently change
  behavior underneath you.
- **Operate**: monitor cost, latency, error rates, and — for LLM systems specifically —
  output quality drift and safety/policy violations, not just uptime.
- **Maintain**: prompts, tool schemas, and even model versions need ongoing upkeep as
  models are updated/deprecated, as the business requirements shift, and as you learn from
  production traffic what the system gets wrong.

The exam-relevant point: infrastructure and business requirements (skill 1, above) should
visibly shape decisions at *every* SDLC stage for a Claude feature, not just at the start.
A compliance requirement discovered late (design or build stage) might force you back to
plan; a cost requirement discovered in operate might force a re-design around caching or
batch.

## 3. Claude API Mechanics (6.8%)

This is the technical core of the domain: how the Claude API actually behaves, at the level
of requests and responses.

### The Messages API shape

The core endpoint is `POST /v1/messages` (or `client.messages.create(...)` in the Python
SDK). A request has, at minimum:

```python
response = client.messages.create(
    model="claude-sonnet-4-5-20250929",   # pin a specific dated version — see Config Mgmt
    max_tokens=1024,
    system="You are a helpful assistant for Acme's support team.",  # optional, top-level
    messages=[
        {"role": "user", "content": "How do I reset a customer's password?"},
    ],
)
```

Key shape facts worth internalizing:

- `system` is a **top-level parameter**, not a message with `role: "system"` — this is a
  common point of confusion coming from other chat APIs.
- `messages` alternates `user`/`assistant` turns; `content` can be a plain string, or a
  **list of content blocks** (text, image, tool_use, tool_result, etc.) when you need more
  than one kind of content in a turn.
- The response's `content` is itself a list of content blocks (usually one `text` block for
  a simple reply, but more when tools or thinking are involved).
- `usage` on the response reports input/output token counts — and, with caching, a
  breakdown of cached vs. non-cached input tokens (see below).
- `stop_reason` tells you *why* generation ended (`end_turn`, `max_tokens`, `tool_use`,
  `stop_sequence`, etc.) — always worth checking, especially to detect truncation.

### Tools

The `tools` parameter lets you describe functions Claude can decide to call, each with a
JSON Schema for its inputs:

```python
tools=[{
    "name": "lookup_order",
    "description": "Look up an order by ID and return its status.",
    "input_schema": {
        "type": "object",
        "properties": {"order_id": {"type": "string"}},
        "required": ["order_id"],
    },
}]
```

When Claude wants to use a tool, it returns a `tool_use` content block instead of (or
alongside) text, with `stop_reason: "tool_use"`. Your code executes the actual function,
then sends the result back as a `tool_result` content block in a new `user` message so
Claude can continue. (Domain 8 of this course covers tool/MCP design in much more depth;
here, know the request/response mechanics.)

### Streaming (SSE)

Streaming delivers the response incrementally over **Server-Sent Events** instead of
waiting for the whole completion. You use it for **UX**, primarily: a user sees the first
tokens within a few hundred milliseconds instead of waiting for the full response to
finish generating, which matters a lot for a sub-5-second-feeling chat UI even when total
generation time is similar. The Python SDK exposes this as a context-managed stream you
iterate over (see `ex2_streaming_and_vision.py`), yielding text deltas, tool-input deltas,
and structured start/stop events you can hook into.

Streaming is not free of tradeoffs: it complicates error handling (a stream can fail
partway through, after you've already shown the user some output), it's harder to cache a
full response for reuse, and it doesn't reduce total tokens or cost — it only changes
*when* you see them.

### Vision

Claude accepts images as content blocks alongside text, letting you ask questions about a
screenshot, photo, chart, or scanned document:

```python
{"role": "user", "content": [
    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64_data}},
    {"type": "text", "text": "What's the total on this receipt?"},
]}
```

Images can be supplied as base64-encoded data or (depending on current SDK/API support) a
URL source. Multiple images can appear in one message. Vision is just another content
block type — it composes with tools, system prompts, and multi-turn conversation the same
way text does.

### Extended thinking

Extended thinking lets Claude allocate an explicit token budget to internal reasoning
before producing its final answer, exposed back to you as a distinct `thinking` content
block (separate from the final response text). It's most useful for tasks with real
multi-step reasoning, math, or planning, where letting the model "show its work" internally
improves the final answer's quality. It costs latency and tokens, so it's a poor fit for
requirements that emphasize low latency or low cost on simple requests — another example of
skill 1 (requirements) shaping a skill 3 (API mechanics) decision. Extended thinking has its
own interaction rules with tool use and streaming that are worth checking against current
docs before relying on them, since this is an area that has evolved.

### Prompt caching

Prompt caching lets you mark a prefix of your request (e.g., a long system prompt, a big
document, a tool definitions block) with `cache_control` so that identical prefix can be
reused across calls instead of being reprocessed from scratch:

```python
system=[{
    "type": "text",
    "text": long_policy_document_text,
    "cache_control": {"type": "ephemeral"},
}]
```

The first call with a new prefix is a **cache write** (usually a bit more expensive than a
normal call); subsequent calls that share the same prefix within the cache's lifetime are
**cache reads** (substantially cheaper and faster for that portion of the input). The
response's `usage` breaks this out — look for fields like `cache_creation_input_tokens` and
`cache_read_input_tokens` alongside the normal input/output counts.

Caching pays off when you have a **large, static (or slowly-changing) block of context
reused across many requests** — a long system prompt, a knowledge-base document, a big
few-shot example set, a large tool-definitions block — and calls sharing that prefix happen
frequently enough (cache lifetimes are short, on the order of minutes) to actually hit the
cache before it expires. It does **not** help when context is different on every call, when
call volume is too low/sparse to land within the cache window, or when the static portion
is small relative to the per-call overhead of using it. `ex3_prompt_caching.py` has you
observe this directly.

### Invoking Claude through third-party vendors

Anthropic's own API (`api.anthropic.com`) isn't the only way to reach Claude. Claude models
are also offered through major third-party cloud AI/model-hosting platforms, which matters
for infrastructure requirements around data residency, existing cloud billing
relationships, enterprise procurement, or IAM integration. The mental model to take into
the exam: the Messages API *shape* (roles, content blocks, tools, streaming) is
substantially consistent across these access paths, but exact SDK client setup,
authentication mechanism, available model identifiers, and regional availability differ by
vendor and change over time — treat this as "know this exists as an architectural option
and why a team might choose it," not "memorize a specific vendor's current product name or
pricing," and check docs.claude.com and the vendor's own docs for current specifics before
building against one.

### Batch API vs. realtime

The **Message Batches API** is an asynchronous, bulk-submission path: you submit a set of
requests together, Claude processes them off the interactive path (typically within a
window on the order of 24 hours, though check current docs for the exact SLA), and you poll
for completion and retrieve results once ready. It's priced at a discount relative to
realtime calls. This is the right tool for **non-urgent, high-volume** workloads — batch
classification of a large document set, bulk summarization, offline evaluation runs,
nightly data enrichment — anything where no human is waiting synchronously on a specific
response.

**Realtime** (a normal, possibly-streamed `messages.create` call) is the right tool when a
human or another system is waiting on the response *now* — chat UIs, inline
autocomplete-style features, anything with a latency requirement measured in seconds.

The tradeoff, in one line: batch trades latency for cost and throughput; realtime trades
cost for immediacy. `ex4_batch_vs_realtime.py` and `ex5_async_concurrent_calls.py` both dig
into this, including the middle ground — realtime calls issued *concurrently* — and when
that's the better fit versus true batch.

## 4. Software Engineering Foundations (7.4%)

This skill is the least Claude-specific and the most "you should already know this as a
developer" — but the exam frames it through the lens of building Claude-integrated systems.

**REST and JSON.** The Claude API is a REST-ish JSON-over-HTTPS API: you POST a JSON body
to an endpoint, authenticate via an API key header, and get a JSON response back with a
status code. Understanding standard REST conventions (resource-oriented URLs, verbs mapped
to HTTP methods, status codes signaling success/client-error/server-error) and being
comfortable reading/constructing/validating JSON is foundational — every SDK is, underneath,
a wrapper around this.

**Sync vs. async Python.** A single `client.messages.create(...)` call is fine written
synchronously. But the moment you need to make **multiple independent Claude calls
concurrently** — fanning out over a batch of user records, calling Claude alongside other
I/O-bound work — a naive Python `for` loop making blocking calls one at a time leaves
significant wall-clock time on the table, because each call is mostly *waiting on network
I/O*, not using CPU. This is exactly the situation `asyncio` is built for: use the async
Claude client (`anthropic.AsyncAnthropic`) with `await` and `asyncio.gather(...)` to issue
several calls concurrently and let the event loop overlap their waiting time. This is not
the same tool as the batch API — async concurrency still hits the realtime, non-discounted
endpoint and still requires your process to stay up and manage the fan-out; batch hands the
whole set to Anthropic to process on its own schedule. `ex5_async_concurrent_calls.py`
contrasts the two.

**Version control practices for prompts and code.** Prompts are code, from a version-control
standpoint: system prompts, tool schemas, and example sets that are subject to change and
that materially affect behavior belong in your repository, reviewed and diffed the same as
any other source file — not hardcoded inline where a change is invisible in a diff, and not
edited live only in a vendor console with no history. Tag or comment prompt versions clearly
enough that you can correlate "behavior changed" with "which prompt version was live."

**SDLC integration.** Tie back to skill 2: your normal engineering practices (CI running
your eval suite, code review, staged rollouts, feature flags) should wrap around Claude
-integrated code exactly as they would around any other feature — an LLM call is not a
reason to skip your existing SDLC discipline.

**Code review for LLM-integrated code.** Beyond normal code review concerns, reviewing
Claude-integrated code should specifically check: are prompts/instructions reviewed with
the same scrutiny as code (not just glanced at)? Is user-provided content clearly separated
from trusted instructions in how the prompt is constructed (prompt-injection surface)? Are
API errors and rate limits handled, not just the happy path? Is there a hardcoded model
name that should be a pinned, documented version? Is sensitive data being sent to the API
in a way that violates a stated infrastructure requirement (skill 1)?

**Refactoring at small and large scale.** Small-scale (function-level) refactoring of
Claude-integrated code looks like: extracting a repeated "build the messages list" pattern
into a helper, pulling a hardcoded prompt string into a template with named parameters,
consolidating duplicated error-handling around `messages.create` calls. Large-scale
(system-level) refactoring looks like: migrating a set of sequential realtime calls to the
batch API as volume grows, introducing prompt caching across a system that previously sent
the same large context on every call, or splitting a single do-everything prompt into a
multi-step pipeline (e.g., a retrieval step feeding a smaller, focused generation step) as
requirements or scale change. The exam may frame either as "here's a pattern, what's the
best refactor," so practice recognizing both scales.

## 5. Claude Application Design (8.6%)

This is the second-largest skill in the domain, and it's about *design judgment* for how a
Claude-powered application is put together — beyond just "call the API correctly."

**Claude across interfaces.** Claude is reachable through several different surfaces, and
each has a somewhat different shape and conventions: the **API/SDKs** (raw, fully
programmatic — you control every instruction), **Claude Code** (a coding-agent CLI/IDE
integration with its own tool ecosystem, permission model, and conventions like `CLAUDE.md`
— covered more in Domain 3 of this course), **Claude Desktop** (a consumer app with its own
extension/MCP-connection model), and **claude.ai** (the web chat product with Projects,
custom instructions, etc.). The exam-relevant point: instruction-following conventions can
differ slightly by interface — for example, what counts as a "system prompt" and how much
of it is user-editable vs. platform-defined varies between raw API use and a product like
claude.ai or Claude Code, which layer their own system-level scaffolding around
user-provided instructions. When designing an application, know *which* interface you're
targeting and don't assume behavior tuned for one transfers exactly to another.

**Content boundaries.** A well-designed prompt keeps a clear boundary between:

- **System content** — stable instructions that define the assistant's role, constraints,
  and behavior; not something the end user should be able to override.
- **User content** — the actual request or data from the person interacting with the
  system; must be treated as *untrusted* if it originates from outside your organization
  (this matters a lot for prompt-injection resistance).
- **Tool content** — results returned from tool execution, which is *also* effectively
  untrusted input if the tool touches external/user-controlled data (a web page, a
  document, a database row someone else wrote), even though it arrives through the
  `tool_result` channel rather than directly from the user.

Blurring these — e.g., concatenating untrusted document text directly into the system
prompt — is a recurring design mistake worth being able to spot.

**Schema design for structured outputs.** When you need Claude's output to be
machine-parseable (feeding another system, populating a database record), design the schema
you ask for deliberately: keep it as small as it needs to be, use clear field names and
types, prefer enums over free text where the value set is fixed, and decide up front how
you'll validate and handle a response that doesn't match the schema (retry with the error
shown back to Claude, in many designs). Whether you enforce this via a tool-call-shaped
schema, an explicit "respond with JSON matching this schema" instruction, or a
structured-output feature, is itself a design decision to make deliberately rather than by
default.

**Session/conversation hygiene.** A multi-turn conversation's `messages` list only grows —
nothing removes old turns automatically. Left unmanaged, this means every call resends the
entire history, which increases latency, cost, and (eventually) risks exceeding the
context window. Good hygiene means deliberately deciding a strategy: trimming or
summarizing older turns, capping history length, or starting a fresh session at natural
task boundaries — rather than letting a conversation grow unbounded by default.

**Plugin management.** Claude Code and related tooling support a plugin/extension model
(covered in depth in Domain 3 and Domain 8 of this course). At the application-design level,
the relevant judgment is: only install plugins from sources you trust, understand what
capabilities/permissions a plugin grants before enabling it, and keep track of which
plugins a project depends on (see Configuration Management, next) so a teammate — or your
future self — can reproduce the same setup.

## 6. Configuration Management (4.1%)

This skill is about the concrete config artifacts that keep a Claude-integrated project
reproducible and maintainable over time.

**`CLAUDE.md`.** A `CLAUDE.md` file (used by Claude Code, and readable by any Claude-based
tool that looks for it) gives Claude persistent, project-specific context and instructions
— coding conventions, architecture notes, commands to run tests, things to never do in this
repo. Its purpose is the same as good onboarding docs for a human engineer, except Claude
reads it automatically at the start of a session. Keep it accurate and current: a stale
`CLAUDE.md` that references removed commands or old conventions actively misleads the
assistant. `ex6_config_files.md` has you write one.

**`settings.json`.** Claude Code (and similar tools) read project- and user-level
`settings.json` files for configuration: permission rules (what tools/commands are
auto-allowed vs. require confirmation), environment variables to inject, hooks, model
defaults, and other tool behavior. Treat it as configuration-as-code: check it into version
control at the project level (excluding anything secret), and know that user-level settings
typically layer on top of or get overridden by project-level settings — check current docs
for the exact precedence rules, since this is another area that evolves.

**Pinning model versions.** Every model has a "latest"-style alias (e.g., a family name
without a date) and one or more **dated, specific versions** (e.g.,
`claude-sonnet-4-5-20250929`). For anything beyond quick experimentation, pin the specific
dated version in your configuration rather than relying on an alias:

- An alias can start pointing at a new underlying model at a time outside your control,
  silently changing your application's behavior, cost, or latency profile.
- A pinned version gives you a deliberate, reviewed upgrade path — you test against the new
  version and update the pin in a commit, the same as bumping any other dependency.
- The tradeoff: pinned versions are eventually deprecated on a timeline set by Anthropic, so
  pinning trades "surprise behavior change" for "you must actively track deprecation
  notices and migrate before a cutoff" — check the console/docs for deprecation dates on
  whatever you pin.

**Prompt versioning.** Treat prompts (system prompts, tool descriptions, few-shot examples)
as versioned artifacts, same as code: store them in version control, note *why* a change
was made in the commit message, and — for anything with real behavioral stakes — consider
tagging or naming prompt versions explicitly so you can correlate a production incident or
an eval regression back to the exact prompt text that was live.

**Plugin dependency management.** Where a project depends on specific Claude Code plugins
or MCP servers, record *which* plugins/versions the project expects (the same instinct as a
`requirements.txt` or `package.json`) rather than relying on whatever happens to be
installed locally, so the setup is reproducible for teammates and in CI.

---

## Where to go next

Work through `exercises/` in order — they build on each other loosely (streaming/vision,
then caching, then batch, then async, tying back to the same underlying API mechanics), then
check your work against `solutions/`. Finish with `quiz.md` to self-test across all six
skills. As with every module in this course, treat anything here that looks stale against
[docs.claude.com](https://docs.claude.com) as the docs being right and this README being
out of date.
