# Module 05 — Model Selection and Optimization

> **Cost note:** all four exercises measure real token usage, latency, or cost, so they need
> a metered Console API key to run live — see `00-setup/README.md` section 2. Realistic total
> cost for this domain is trivial (well under a dollar) if you use the smallest model tier
> and set a spend cap, as that section recommends.

Domain weight: **16.8%** of the CCDV-F exam — the second-largest domain in the blueprint.
This module is dense on purpose: it covers everything from "what is a token" up through
picking a model tier for a production workload and controlling what you pay for it.

This is an unofficial, independently-built self-study module inspired by the published
CCDV-F exam blueprint (version 1.0, effective July 2026). It is not written or endorsed by
Anthropic. Model names, prices, and exact field names below are correct to the best of this
writer's knowledge as of when this module was written, but the platform moves fast —
**anywhere a specific model name, price, context-window size, or field name appears, treat
it as illustrative and verify it against [docs.claude.com](https://docs.claude.com) and
[anthropic.com/pricing](https://www.anthropic.com/pricing) before you rely on it**, and
especially before the real exam.

This README covers four skills from the blueprint:

1. LLM Fundamentals (5.2%)
2. Technical Fundamentals (6.1%)
3. Model Selection and Tradeoffs (2.7%)
4. Cost and Token Management (2.8%)

---

## 1. LLM Fundamentals

### Tokens

Claude, like other large language models, doesn't read or write in whole words or
characters — it operates on **tokens**, which are subword units produced by a tokenizer.
A token might be a whole common word ("the"), a word fragment ("token" + "ization"),
punctuation, or a piece of whitespace. You don't need to memorize the exact tokenizer
Claude uses to pass this exam, but you do need a working intuition for size estimation:

- **Rule of thumb: roughly 4 characters per token for English prose.** So a 400-character
  paragraph is very roughly 100 tokens. This is a rough heuristic, not a guarantee — code,
  non-English languages, and text with lots of unusual punctuation or numbers can tokenize
  at noticeably different ratios.
- Short, common words are often a single token. Rare words, made-up words, and non-Latin
  scripts tend to split into more tokens per character.
- Both your **input** (system prompt, messages, tool definitions, tool results) and the
  model's **output** are measured in tokens, and both count toward cost and toward the
  context window.

Why this matters practically: token counts drive both **cost** (you're billed per token,
input and output priced separately) and **fit** (whether your conversation fits in the
model's context window). When you're estimating either, start from the ~4-chars/token rule
and refine with an actual tokenizer or the API's usage numbers if you need precision.

### Context windows

A model's **context window** is the total budget of tokens it can process in a single
request — your system prompt, conversation history, tool definitions, any documents you've
included, *plus* the tokens it's allowed to generate in response, all counted against one
combined (or, depending on the model/endpoint, input-and-output-tracked-separately) budget.
Exact context window sizes differ by model and change over time as Anthropic ships new
model versions — verify the current number for the model you're using at docs.claude.com
rather than assuming a figure from memory.

Practical implications:

- A very long conversation, a large pasted document, or a big tool result can silently push
  you toward the context limit. Once you exceed it, the request fails.
- Long context isn't free — every token you send is a token you pay for (see Cost and Token
  Management below), regardless of whether the model window is "big enough."
- Techniques like summarizing old turns, trimming tool results, or using prompt caching
  (below) exist specifically to manage context-window and cost pressure in long-running
  agentic applications.

### Sampling and non-determinism

Claude generates text by repeatedly predicting a probability distribution over "what token
comes next," then **sampling** from that distribution to pick the next token — it is not
simply always picking the single most likely token. Two parameters control that sampling
that you should recognize:

- **`temperature`** — controls how "flat" vs "peaked" the sampling distribution is. Lower
  temperature (near 0) makes the model consistently favor its highest-probability tokens,
  producing more focused, repeatable-looking output. Higher temperature flattens the
  distribution, giving lower-probability tokens more of a chance and producing more varied,
  sometimes more creative, output.
- **`top_p`** (nucleus sampling) — restricts sampling to the smallest set of tokens whose
  cumulative probability mass reaches `p`, then samples within that set. It's another lever
  on the same underlying idea: how much of the probability distribution's "tail" gets a
  chance to be picked.

**Why identical prompts can produce different outputs:** because sampling is genuinely
probabilistic (subject to the parameters above), calling the API twice with the exact same
messages, same model, and even the same temperature can yield different token-by-token
choices and therefore different final text. This is **non-determinism**, and it's expected
behavior, not a bug. Setting `temperature` to 0 makes output *more* consistent and
repeatable, but even at very low temperature you should not assume byte-for-byte identical
output is guaranteed on every call — treat near-zero temperature as "more deterministic,"
not as an absolute guarantee, and design applications (especially anything with automated
tests or evals) to tolerate some output variance rather than asserting exact string matches.

### Next-token generation

Conceptually, Claude is **autoregressive**: it generates a response one token at a time,
and each new token is predicted using everything that came before it — the full prompt plus
every token the model has generated so far in this response. After each token is produced,
it gets appended to the context and fed back in to predict the *next* token, until the
model produces a stop condition (e.g., it decides the response is complete, or it hits
`max_tokens`, or a stop sequence is reached). You don't need low-level architecture detail
for the exam, but you should understand this "predict one token, append it, repeat" loop as
the mechanical explanation for both streaming responses (why you can watch text appear
token by token) and why longer outputs take proportionally longer to generate.

### Model "modes": fast/default vs. extended thinking vs. adaptive thinking / effort levels

Beyond choosing *which* model to use, Claude supports different **modes of reasoning** for
a given call:

- **Fast / default mode** — the model goes straight from your prompt to a final answer,
  without an intermediate reasoning phase. This is the lowest-latency, typically
  lowest-cost path, and it's fine for straightforward tasks (classification, simple
  extraction, short conversational replies) where the model doesn't need to work through
  multiple sub-steps to get a correct answer.
- **Extended thinking** — for harder, multi-step problems (nontrivial math, multi-step
  logic, planning-heavy agentic tasks), you can enable a mode where the model produces an
  intermediate **thinking block** (visible or summarized, depending on configuration)
  before its final answer — essentially "showing its work" before committing to a response.
  This tends to improve accuracy on hard reasoning tasks at the cost of extra latency and
  extra output tokens (the thinking content itself consumes tokens and is billed as
  output). Extended thinking is typically configured with some kind of **thinking budget** —
  a cap on how many tokens the model may spend reasoning before it must answer.
- **Adaptive thinking / effort levels** — rather than a fixed, always-on or always-off
  choice, adaptive thinking (and the related idea of configurable **effort levels**) lets
  the amount of reasoning scale to the difficulty of the task — either the model
  dynamically decides how much internal reasoning a given prompt warrants, or the developer
  sets a coarse effort level (e.g., low/medium/high) that trades off latency/cost against
  answer quality. The exam-relevant idea: you don't have to choose a single fixed
  "thinking on" or "thinking off" setting for your whole application — you can let effort
  scale with task difficulty, which is more cost-efficient than always running maximum
  reasoning on every request. Not every model tier supports thinking modes identically —
  see Model Selection and Tradeoffs below, and verify current per-model support at
  docs.claude.com since this is an area that evolves quickly.

### Fundamental prompting techniques: zero-shot, single-shot, multi-shot

A foundational lever for output quality that costs no code changes, only prompt changes, is
how many **examples** you give the model of the task you want done:

- **Zero-shot** — you describe the task in instructions only, with no worked examples.
  Fastest to write, cheapest (shortest prompt), and works well when the task is common,
  well-specified, and the model doesn't need to see your exact expected format to get it
  right (e.g., "summarize this paragraph in one sentence").
- **Single-shot / one-shot** — you include exactly one worked example of input → desired
  output before the real task. Useful when there's a specific format or style you need
  reproduced that a text description alone doesn't pin down precisely (e.g., "extract
  fields into this exact JSON shape" is much more reliable with one concrete example of
  that JSON shape).
- **Multi-shot / few-shot** — you include several (commonly 3 or more) worked examples,
  ideally spanning edge cases and variety, not just repeats of the easy case. This tends to
  produce the most consistent, most format-faithful output, especially for classification
  and structured extraction tasks with several categories or tricky edge cases — at the
  cost of a longer (and thus more expensive, and slower) prompt on every call.

**When to use which:** start zero-shot for simple, common tasks. Move to one-shot when
output format/style consistency matters more than the extra prompt length. Move to
multi-shot when you have several distinct categories/edge cases the model needs to
discriminate between reliably, or when zero/one-shot testing shows inconsistent output —
and remember that every example you add is tokens you pay for on every single call, so
few-shot is a real cost/quality tradeoff, not a free upgrade. Exercise 2 in this module has
you measure this tradeoff directly.

---

## 2. Technical Fundamentals

### SDKs are convenience wrappers around a REST API

The official Claude SDKs (Python, TypeScript, and others) are **thin, convenience wrappers
around Claude's REST API** — specifically, calling `client.messages.create(...)` in Python
is, under the hood, the SDK building and sending an HTTPS POST request to an endpoint like
`https://api.anthropic.com/v1/messages`, with your API key in a header, a JSON request
body, and (for non-streaming calls) a JSON response body that the SDK then parses into
Python objects for you.

Why this matters for the exam and for real engineering:

- You can always drop down to raw HTTP (e.g., with `requests` or `curl`) if the SDK doesn't
  yet expose a feature, if you're debugging something the SDK is hiding from you, or if
  you're working in a language/environment without an official SDK. Understanding the
  underlying request/response shape (headers like the API key and API version, a JSON body
  with `model`, `messages`, `max_tokens`, etc., and a JSON response with `content`,
  `usage`, `stop_reason`, and so on) means you're never blocked by "the SDK doesn't support
  this."
- SDK version and API version can drift independently. The SDK is versioned software with
  its own release cadence; the underlying API also evolves. Pinning SDK versions and
  reading changelogs matters for reproducibility (this connects to Configuration Management
  concepts elsewhere in the course).
- Errors and status codes from the API (auth failures, rate limits, malformed requests) are
  standard HTTP semantics (4xx/5xx status codes) that the SDK translates into typed
  exceptions for convenience — but they're still fundamentally HTTP errors underneath, and
  troubleshooting sometimes means looking at the raw status code and response body.

### WebSockets as an alternative transport

Most Claude API usage is a standard request/response HTTP call (optionally with HTTP
streaming — chunked responses over the same connection — for token-by-token output).
**WebSockets** are a different transport: a single long-lived, bidirectional connection
that both sides can push messages over at any time, rather than a strict request-then-
response cycle. In some real-time integration contexts (for example, certain voice or
low-latency multi-turn interactive scenarios where either side needs to push updates
without waiting on a fresh request), a websocket-based connection is used to support
persistent, low-overhead bidirectional communication instead of repeated HTTP requests.

For the exam, the important conceptual points are:

- HTTP request/response (with optional streaming) is the default, most common transport
  for the Messages API and covers the overwhelming majority of application integrations.
- WebSockets exist as an alternative transport pattern for persistent, bidirectional,
  real-time integration needs — recognize the concept and when it would be reached for
  (continuous, low-latency, two-way communication) rather than needing to hand-implement
  one for this course. Check docs.claude.com for which current APIs/products offer a
  websocket-based interface, since offerings in this area change.

---

## 3. Model Selection and Tradeoffs

### The Opus / Sonnet / Haiku family

Claude models ship in a family of tiers that trade off capability against speed and cost.
The naming and exact lineup change over time (new versions ship periodically — see below),
but the conceptual tiering to know for the exam is stable:

- **Opus-class** — Anthropic's most capable tier. Best at the hardest reasoning, the most
  open-ended or ambiguous tasks, and complex multi-step agentic work where mistakes are
  costly. Slower and more expensive per token than the other tiers.
- **Sonnet-class** — the balanced, "workhorse" tier: strong general capability at
  meaningfully lower latency and cost than Opus-class. This is a common default choice for
  general application development where you need solid reasoning but not the absolute
  ceiling of capability, and where per-request latency and cost matter at production
  volume.
- **Haiku-class** — the fastest, cheapest tier, optimized for high-throughput, lower-
  complexity tasks. Less capable on hard reasoning than the larger tiers, but very cost-
  and latency-efficient for simple, well-defined, high-volume work.

**Example use-case mapping** (illustrative, not a rule to memorize verbatim):

| Task | Good fit | Why |
|---|---|---|
| Classifying high-volume support tickets into a fixed set of categories | Haiku-class | Simple, well-defined task; volume makes per-call cost/latency dominate the decision |
| General-purpose app assistant (Q&A, drafting, moderate reasoning) | Sonnet-class | Balanced capability/cost/latency fits most product surfaces |
| Complex multi-step agentic coding or research task with high accuracy requirements | Opus-class | Hardest reasoning, highest stakes for getting it right, latency/cost is secondary |
| Real-time chat autocomplete/suggestions at huge scale | Haiku-class | Latency and cost per call dominate; task is narrow |
| Deep multi-document analysis and synthesis with many reasoning steps | Opus-class (often with extended/adaptive thinking) | Task benefits from maximum reasoning depth |

A common production pattern is **not** picking one tier for an entire application, but
routing: cheap/fast tiers for simple, high-volume sub-tasks, and a more capable tier
reserved for the harder sub-tasks or as an escalation path when a cheaper tier's output
looks low-confidence.

### Thinking support across tiers

Extended thinking and adaptive thinking / effort levels (see LLM Fundamentals above) are
not necessarily available identically across every model tier and every model version —
support for these modes is a property of the specific model you select, and it has expanded
and changed as Anthropic has shipped new model generations. **Do not memorize a specific
"tier X supports thinking, tier Y doesn't" mapping from this document** — verify current
per-model support for extended/adaptive thinking at docs.claude.com before you design
around it, and expect this to be one of the more likely areas to have shifted between when
this module was written and when you take the exam.

### Breaking behavior changes across model releases

When Anthropic ships a new model version, behavior can change in ways that are not purely
"strictly better at everything" — a new version might follow instructions more literally,
change its default verbosity, refuse or comply differently on edge cases, format output
differently, or otherwise shift behavior your application implicitly depended on. This is
normal for any actively-developed model family, but it has real engineering consequences:

- **Pin model versions in production.** Using a "latest" or floating alias in production
  code means your application's behavior can change out from under you the moment
  Anthropic ships an update — sometimes for the better, sometimes breaking a prompt that
  was tuned against the old version's quirks. Pinning a specific dated model version string
  gives you control over *when* you adopt a new version.
  Note: within this course's own exercises and `verify_setup.py`, a `-latest` style alias
  is used deliberately for learning convenience — that convention is *not* a recommendation
  for production code, where a pinned version is the safer default.
- **Re-test on upgrade.** Before moving production traffic to a new model version, re-run
  your eval suite / regression tests against it (this connects directly to the Evaluation,
  Testing, and Debugging domain elsewhere in this course) rather than assuming an upgrade
  is a free improvement.
- **This ties back to Configuration Management** (Domain 2 elsewhere in this course):
  treating the model identifier as a piece of versioned configuration — reviewed,
  tested, and deliberately changed — rather than an implicit always-latest dependency, is
  the same discipline you'd apply to pinning a library version.

---

## 4. Cost and Token Management

### Token usage tracking

Every Messages API response includes a **`usage`** object reporting how many tokens the
call actually consumed — at minimum, `input_tokens` and `output_tokens`, and (when prompt
caching is in play — see below) additional fields describing cache-related token counts
(for example, tokens written to create a new cache entry vs. tokens read from an existing
cache hit; exact field names are covered as an implementation detail in Exercise 4's
solution, flagged as best-effort since field names can change — verify against
docs.claude.com). Reading and logging this `usage` object on every call is the foundation
of any cost-tracking or budgeting system: it's the ground truth for what a call actually
cost, as opposed to an estimate made before the call.

Practical uses of usage data:

- Per-request logging for debugging ("why was this call so expensive?").
- Aggregating usage across a session, a user, or a time window to build dashboards or
  alerts.
- Comparing estimated pre-call token counts (e.g., from a local tokenizer estimate) against
  actual post-call usage, to sanity-check your cost model.

### Cost modeling

Anthropic bills per token, with **separate prices for input tokens and output tokens**,
and prices differing **by model tier** (Haiku-class cheapest, Opus-class most expensive,
Sonnet-class in between — consistent with the capability tiering above). A basic cost model
for a single call is:

```
cost = (input_tokens / 1_000_000) * price_per_million_input_tokens
     + (output_tokens / 1_000_000) * price_per_million_output_tokens
```

(Anthropic typically publishes prices per million tokens; check the current unit and
figures at anthropic.com/pricing.) To model cost for an application rather than a single
call, sum this across every call in a session/request/day, broken out by model if you're
routing across tiers. **Do not hardcode specific dollar figures into production logic or
into your mental model long-term** — prices change, and any cost-modeling code should treat
per-token prices as configuration (a lookup table keyed by model name, ideally sourced from
a config file or constants module you update when pricing changes) rather than inline
literals scattered through the codebase. Exercise 4 has you build exactly this kind of
pluggable pricing config.

### Caching techniques: prompt caching and cache checkpointing

When an application repeatedly sends a large chunk of **static or slowly-changing context**
— a long system prompt, a big reference document, a large set of tool definitions, earlier
turns of a long conversation — on every call, it pays full input-token price for that same
content again and again. **Prompt caching** addresses this: you mark a point in your
request content as cacheable, and on subsequent calls that reuse the same prefix, the
cached portion is billed at a reduced rate (a cache read) instead of full input price,
rather than being re-processed and re-billed at the standard rate — with some tradeoff on
the write side (writing to the cache the first time typically costs a bit more than a
normal input token) and the cache having a limited lifetime (it expires after a period of
inactivity).

- **Cache checkpointing / cache breakpoints** — a single request isn't limited to one
  all-or-nothing cache boundary. You can mark **multiple breakpoints** within one prompt
  (for example: cache the system prompt and tool definitions at one boundary, and
  separately cache a large reference document included in the conversation at another
  boundary), so that different static sections can be reused independently across calls
  that vary in other ways. This is especially valuable in agentic loops, where a large,
  unchanging system prompt/tool-definition block is resent on every turn of a multi-turn
  tool-use conversation — caching that block turns an otherwise-linearly-growing input cost
  into a much smaller marginal cost per turn.
- The **mechanics** (exact request field names/structure for marking a cache breakpoint,
  cache TTL, minimum cacheable prefix length, exact discount/surcharge multipliers) are
  implementation details that have evolved and will keep evolving — this module gives you
  the concept and Exercise 4's solution shows an illustrative, best-effort code shape, but
  **verify exact mechanics at docs.claude.com** before implementing this in a real
  application.

**When caching pays off:** caching helps most when you have a large static prefix reused
across *many* calls in a short window (a long system prompt hit on every turn of a chat
session, a big document repeatedly referenced across many questions about it, a large
fixed tool-definition block in an agentic loop). It helps little or not at all for one-off
calls with mostly-unique content, since you pay the cache-write cost once and need
repeated reuse to earn it back.

---

## Where to verify specifics

This README deliberately avoids treating any of the following as memorization targets,
because they change over time — always check current values at
[docs.claude.com](https://docs.claude.com) and
[anthropic.com/pricing](https://www.anthropic.com/pricing):

- Exact current model name strings and which generation is newest
- Exact context window sizes per model
- Exact per-token / per-million-token prices, and cache read/write pricing multipliers
- Exact `usage` object field names, especially cache-related fields
- Which model tiers currently support extended thinking / adaptive thinking, and their
  exact configuration parameters (e.g., thinking budgets, effort-level options)
- Which product surfaces currently offer a websocket-based interface

What *is* stable and exam-worthy is the set of concepts above: what a token is, why context
windows matter, why sampling is non-deterministic, the zero/one/few-shot spectrum, the
fast/extended/adaptive-thinking mode spectrum, the Opus/Sonnet/Haiku capability-vs-cost
tradeoff shape, why pinning model versions matters, and how token usage tracking + cost
modeling + prompt caching fit together as a cost-optimization toolkit.
