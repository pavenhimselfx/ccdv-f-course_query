# Domain 6: Prompt and Context Engineering

**Exam weight: 11.0% of CCDV-F**

> **Cost note:** `ex1` (context pruning/compaction) is a local simulation and needs no live
> calls. `ex2` and `ex3` need at least one live call each to compare real outputs, so they
> need a metered Console API key — see `00-setup/README.md` section 3.

This is an unofficial, independently-built self-study module preparing you for the
"Claude Certified Developer – Foundations" (CCDV-F) exam, blueprint version 1.0
(effective July 2026). It is not published or endorsed by Anthropic. Everything in
this module — explanations, exercises, and practice questions — is original
content written to teach the public blueprint's skills, not a reproduction of any
real exam item.

The blueprint breaks this domain into three skills:

| Skill | Weight |
|---|---|
| Context Engineering | 3.8% |
| Prompt Engineering | 4.6% |
| Output Handling | 2.6% |

Read this file in order — each section builds on the last. Then work through
`exercises/` in order (`ex1` → `ex2` → `ex3`); each one assumes the intuition
built by the previous one. Check your work against `solutions/` only after you've
made a genuine attempt. Finish with `quiz.md`.

A note on currency: exact API shapes for tool-use forcing, structured-output
features, and context/token accounting move over time. This module was written
against the author's knowledge as of early-to-mid 2026. Treat concrete method
names and parameter names here as "roughly right, verify before you ship." The
canonical, current source is always [docs.claude.com](https://docs.claude.com).
The underlying *principles* — why context degrades, why placement affects
instruction weight, why you should never trust raw model output blindly — age
far more slowly than any particular API surface, and that's where this module
puts most of its weight.

---

## 1. Context Engineering (3.8%)

### 1.1 Why context accumulates, and why that's a problem

The Claude API is stateless: every request you send is self-contained, and the
model has no memory of anything outside the `messages` array you include in
that specific call. This has a direct, easy-to-miss consequence for any
multi-turn or agentic session — a chat that goes back and forth, or a tool-use
loop that runs for many steps: to give Claude "memory" of the conversation so
far, your code has to resend the *entire* prior transcript (every user turn,
every assistant turn, every tool call and every tool result) on every single
request. A conversation isn't a stream Claude remembers; it's a growing list
you reconstruct and hand over, in full, each time.

For a short back-and-forth this is a non-issue. It becomes a real engineering
problem for long-running agentic sessions specifically, because two things
compound:

- **Tool outputs are often large and numerous.** An agent that reads files,
  greps a codebase, calls an API, or runs a shell command accumulates raw tool
  results — often far larger than the reasoning text around them — and every
  one of those results, once appended to the transcript, gets resent on every
  subsequent call unless something removes it.
- **The transcript only grows.** Nothing evicts old turns automatically. A
  session that runs for fifty tool calls has, by the fifty-first, a transcript
  containing all fifty raw results plus all the reasoning in between — even
  though most of those results were only relevant to a step that finished
  fifteen calls ago.

Two distinct failures follow from this:

- **Hitting the context window limit.** Every Claude model has a finite
  context window (input + output tokens combined, model-dependent). A
  transcript that grows without bound will eventually not fit, and the
  request fails outright.
- **Context drift / bloat — quality degradation *before* the hard limit.**
  Long, cluttered context isn't just an eventual capacity problem; it actively
  makes the model's output worse well before you run out of room. A
  transcript stuffed with stale, superseded, or irrelevant information (an
  early failed approach the agent already abandoned, a tool result whose
  conclusion was already extracted and acted on, a long detour down a dead
  end) dilutes the signal the model needs to reason well about the *current*
  step. Models also don't attend to all parts of a long context equally well —
  content buried in the middle of a very long transcript tends to get weighted
  less reliably than content near the start or end. The practical upshot:
  more context is not free, and "just keep everything, tokens are cheap" is a
  trap for anything long-running. Bloated context also means every subsequent
  call re-processes (and re-bills, in both tokens and latency) content that no
  longer earns its place.

Recognizing this as a **design requirement** for any agent expected to run for
many steps — not a bug you patch after it breaks — is the mindset this skill
is really testing.

### 1.2 Pruning tool outputs

**Pruning** is the targeted removal or truncation of specific, individually
identifiable pieces of context that have outlived their usefulness — most
often, the raw output of a tool call from earlier in the session. The pattern:
a tool call returns a large result (a full file, a big search-result page, a
verbose API response); the agent reads it, extracts or acts on the part that
matters, and then — critically — that raw blob does not need to keep being
resent verbatim for the rest of the session. Before re-adding it to context on
the next turn (or before it re-enters context via history), you prune it:

- **Truncate** to a bounded size — first/last N lines or characters, with a
  marker showing content was cut (`"... [34,000 chars omitted] ..."`), rather
  than silently dropping it.
- **Replace with an extracted essential** — instead of the full 50 KB file
  read, keep only the three fields the agent actually needed from it.
- **Drop entirely**, once its conclusion has already been folded into the
  agent's reasoning or into a later message, and nothing downstream needs to
  re-read the raw source.
- **Cap proactively at insertion time** — many agent harnesses set a maximum
  size for any single tool result *before* it ever enters the transcript, so
  a single runaway tool output (e.g., a command that unexpectedly dumps
  megabytes of logs) can't blow the context budget in one step.

The judgment call is always the same: has this specific piece of content
already done its job? If yes, it's a pruning candidate. Pruning is *local* and
*selective* — it targets individual oversized or stale items without touching
the overall shape of the conversation.

### 1.3 Compaction: periodic summarization

**Compaction** operates at a coarser grain than pruning. Rather than
targeting one oversized tool result, compaction periodically collapses a
*stretch* of the transcript — many turns' worth of reasoning, tool calls, and
results — into a single, much shorter summary message that preserves what
still matters (key facts learned, decisions made, current state/plan) and
discards the blow-by-blow detail of how the agent got there. Typical trigger
conditions: a turn-count threshold, an estimated-token threshold, or a natural
checkpoint (a subtask just completed). After compaction, the agent continues
working from "here's a compact summary of everything so far" plus its most
recent, still-fully-detailed turns, instead of the full raw history.

Pruning and compaction are complementary, not competing techniques: pruning
handles "this one thing is now too big to keep verbatim," while compaction
handles "this whole span of the conversation can be replaced by a shorter
account of what happened." A production agent typically does both — pruning
individual large tool results as it goes, and compacting the accumulated
transcript wholesale at intervals.

Compaction is not free of risk: summarization is inherently lossy, and a
detail that seemed unimportant when summarized can turn out to matter later
(a specific error message, an exact value, a caveat that got smoothed away).
Good compaction preserves *decisions and state*, not just prose, and a
well-designed agent keeps a way to recover more detail if the summary later
proves insufficient (e.g., the raw data still exists in a log or a file, even
if it's no longer inline in the model's context).

### 1.4 Context isolation through subagents and multi-step workflows

The third technique doesn't manage a single, ever-growing context at all — it
avoids growing one context past its useful size in the first place, by
splitting work across multiple contexts. This is the same manager/subagent
pattern covered in Domain 1, viewed through a context-engineering lens: rather
than one agent accumulating the full transcript of every subtask it ever
touches, a manager delegates a bounded subtask to a **subagent** that starts
from a fresh, minimal, task-specific context — just what it needs for its one
job, not the parent's entire history of unrelated exploration, dead ends, and
other subagents' transcripts. The subagent does its work, and only its
*distilled result* — not its full working transcript — gets added back into
the manager's context.

This is context isolation, and it delivers two of the same benefits pruning
and compaction chase, by a different route:

- **The manager's context stays small**, because it only ever accumulates
  results, never the full working detail of how each subtask was solved.
- **Each subagent's context stays clean and on-topic**, because it was never
  polluted with the manager's other business in the first place — there's
  nothing to prune or compact away, because it was never added.

The same idea shows up in ordinary multi-step agentic workflows even without
a formal manager/subagent split: breaking one large, open-ended task into
discrete stages, each of which gets its own comparatively fresh, tightly
scoped context relevant to that stage, rather than one monolithic
conversation that has to carry everything from the first stage through the
last. The unifying principle across all three techniques in this skill is the
same: **don't let context grow just because it can — actively decide what
deserves to still be there.**

---

## 2. Prompt Engineering (4.6%)

### 2.1 Instruction clarity

The single highest-leverage thing you can do to a prompt is make its
instructions specific and unambiguous. "Summarize this" is vague: summarize
to what length, for what audience, keeping or dropping what kind of detail,
in what format? Every one of those unstated dimensions is a place where the
model has to guess, and different guesses on different calls is exactly what
produces inconsistent output across runs. "Summarize the following support
ticket in exactly two sentences: the first stating the customer's core
problem, the second stating what resolution they're asking for. Do not
include greetings, signatures, or ticket metadata" leaves far less to chance.
Clarity means naming the task, the scope, the audience, and the boundaries
explicitly rather than assuming the model will infer the one interpretation
you had in mind.

### 2.2 Few-shot examples

A **few-shot example** is a demonstration, included in the prompt, of the
exact input/output pattern you want — often one to five examples, each
showing a realistic input paired with the output you'd consider correct for
it. Few-shot examples earn their keep especially when:

- The desired *format* is easier to show than to describe precisely (an exact
  JSON shape, a specific bullet structure, a particular tone).
- There's an edge case or convention you want the model to follow that a
  plain instruction tends to miss (e.g., how to handle a ticket with no clear
  resolution requested).
- You've observed the model doing something close-but-wrong under a
  zero-shot (instruction-only) prompt, and a concrete example closes the gap
  faster than more prose would.

Few-shot examples cost context (more input tokens per call) and can
overfit — the model may over-index on surface features of your examples
rather than the underlying pattern if the examples aren't varied enough — so
they're a tool to reach for when clear instructions alone leave too much
variance, not a default for every prompt.

### 2.3 System versus user message placement

Claude's Messages API distinguishes a top-level **system prompt** from the
turn-by-turn **user** (and **assistant**) messages. The system prompt is the
right place for content that should hold stably across the *entire*
conversation or task: the assistant's role/persona, global behavioral rules,
standing output-format requirements, tool-use policy, things that would be
wasteful or risky to have to restate on every single turn. User messages are
the right place for the specific task or content at hand *this turn* — the
actual ticket to summarize, the actual question being asked, the actual data
to process — content that legitimately changes from one call to the next.

A useful test: if you'd want the exact same instruction to apply to every
turn of a conversation without re-typing it, it belongs in the system prompt.
If it's specific to what's being asked right now, it belongs in the user
turn. Putting a standing rule in the user turn means you must remember to
repeat it every time (and it competes for attention with that turn's actual
task content); putting per-request content in the system prompt means it's
stale for every subsequent turn that has a different actual task.

### 2.4 Output constraints

Beyond describing the task, tell Claude explicitly what shape the output
should take: format ("respond with valid JSON matching this schema, and
nothing else"), length ("two sentences," "under 50 words," "a maximum of five
bullet points"), and what to avoid ("do not include a preamble like 'Here is
the summary,'" "do not speculate about information not present in the
ticket"). Output constraints matter because Claude, left unconstrained, will
often produce a reasonable but *unpredictable* shape — sometimes with a
lead-in sentence, sometimes without, sometimes three bullets, sometimes
seven. If downstream code is going to parse or display the output
programmatically, that variance is a bug waiting to happen; naming the
constraint explicitly is far more reliable than hoping the model infers your
unstated formatting preference.

### 2.5 Where instructions live, and why placement changes their weight

Instructions to Claude don't all live in one place, and *where* an
instruction sits measurably affects how strongly the model tends to weight
it. Four places instructions commonly show up, and the rough intuition for
each:

- **The system prompt** — carries standing, global authority. It's the
  natural home for rules meant to govern the whole interaction, and it's
  read as the most stable, persistent layer of instruction.
- **The beginning of a user turn** — good for framing: setting up what kind
  of task this is before the model reads the content of the task itself.
- **The end of a user turn** — content placed closest to where the model's
  response begins tends to be weighted more heavily than content buried
  earlier in a long turn; this is why a common, effective pattern for a long
  user message (e.g., a big pasted document plus a question about it) is to
  put the *instruction* — what you actually want done — after the pasted
  content, not before it, so the instruction is the last thing the model
  reads before it starts responding.
- **Tool descriptions** — the text you write describing a tool (its purpose,
  when to use it, its parameters) is itself part of the effective prompt: it
  shapes *whether* and *how* Claude chooses to call that tool, separately
  from anything in the system or user message. A vague or misleading tool
  description produces the same kind of inconsistent behavior as a vague
  system prompt, just localized to that one tool's usage.

The practical takeaway: placement is not a neutral formatting choice. A rule
that keeps getting "forgotten" is often not being ignored so much as
under-weighted by where it sits — moving a critical instruction into the
system prompt, or to the end of a long user turn, is frequently the fix,
independent of the instruction's wording.

### 2.6 Iterative refinement

Prompts are rarely right on the first attempt, and treating prompt
development as an iterative, empirical loop — rather than something you write
once and ship — is itself a named skill here: write a candidate prompt, run
it against realistic (and ideally somewhat adversarial or edge-case) inputs,
observe *specifically* how the output fails (wrong format? missing a
constraint? inconsistent across similar inputs? technically correct but
unusable downstream?), form a hypothesis about *why*, and adjust — usually
one change at a time, so you can tell which change actually fixed the
problem. This mirrors ordinary empirical debugging: don't guess broadly and
rewrite the whole prompt on every iteration; isolate what's failing and make
the smallest change that plausibly addresses it, then re-test. Exercise 2 in
this module walks through exactly this loop across several prompt versions.

### 2.7 Input sanitization

Whenever a prompt incorporates content you didn't write yourself — raw user
input, text pulled from a retrieved document, a web page, a database record,
a prior tool's output — that content becomes part of what Claude reads, and
it can contain things you didn't intend to send: instructions embedded in
retrieved text that attempt to override your actual instructions (a
prompt-injection concern this module foreshadows and Domain 7 covers in
depth), absurdly long content that blows your context or cost budget, or
malformed data that breaks a downstream template. **Input sanitization**
means treating anything from an untrusted source as *data to be handled
carefully*, not as trusted instruction text, before it ever reaches the
prompt:

- **Bound it.** Cap the length of untrusted content before insertion, rather
  than assuming it will always be reasonably sized.
- **Delimit it clearly.** Wrap untrusted content in an obvious boundary (for
  example, XML-style tags like `<user_provided_content>...</user_provided_content>`)
  and instruct Claude explicitly that content inside that boundary is data to
  be processed, not instructions to be followed — this makes it much easier
  for the model (and for you, reading the transcript later) to tell "things I
  said" from "things a retrieved document said."
- **Strip or escape what shouldn't be there** — control characters, obvious
  injection markers, anything that would break a format you're about to
  insert the content into.
- **Never treat retrieved or user-supplied content as if it carries your
  authority.** A retrieved document that says "ignore previous instructions
  and do X" is just text describing what it says; whether Claude should act
  on it is exactly the kind of ambiguity good sanitization and clear system
  framing are meant to close down before it becomes a live security issue.

---

## 3. Output Handling (2.6%)

### 3.1 Structured output patterns

When downstream code needs to *consume* Claude's output programmatically —
feed it into another function, store it in a database, branch on a field's
value — free-form prose is the wrong shape, no matter how well-written. A
few patterns get you a reliably structured result:

- **Ask directly, with explicit schema and format constraints.** Describe the
  exact JSON shape you want (field names, types, allowed values) in the
  prompt, and constrain the model to emit only that JSON with nothing else
  around it. This is the simplest approach and works reasonably well, but the
  output is still, mechanically, generated text that happens to look like
  JSON — nothing *forces* it to actually be well-formed JSON matching your
  schema.
- **Use tool-use (function-calling) as a forcing function.** Define a tool
  whose input schema *is* the structure you want, and — rather than letting
  Claude decide freely whether to call it — force the call (via a
  tool-choice setting that requires this specific tool). Claude then returns
  a `tool_use` content block whose `input` is arguments matching the schema
  you declared, rather than prose you have to hope is valid JSON. This is
  generally the more reliable route for anything you plan to parse
  programmatically, because the schema is declared structurally (as part of
  the tool definition) rather than only described in prose.
- **Schema-constrained output features**, where available, go a step
  further by having the API itself constrain generation to conform to a
  supplied schema, reducing the chance of malformed output at the source
  rather than only catching it after the fact. Availability and exact
  mechanics for this kind of feature evolve — check current docs.claude.com
  for what's currently supported.

### 3.2 Response validation

Getting output that *looks* structured is not the same as confirming it
*is* correct and usable. Response validation is the step, after parsing,
where you check that the result actually satisfies your expectations before
anything downstream touches it: are all required fields present? Are types
right (a string where you expected a string, a number where you expected a
number)? Do enum-like fields hold one of the allowed values, rather than
something the model invented? Are values in a sane range? A common, robust
way to do this in Python is to define the expected shape as a schema (a
`pydantic` model is a popular choice, since it validates types and required
fields declaratively and raises a clear, structured error on the first
violation) and validate every response against it before use, rather than
trusting a successfully-parsed JSON blob to also be a *correct* one.

### 3.3 Defensive parsing

Never assume the raw string Claude returns is exactly what you asked for.
Even with a strong prompt and even with tool-use forcing, things can still go
wrong: the response gets cut off because it hit a token limit mid-JSON-object,
the model wraps valid JSON in a sentence of prose anyway ("Here's the JSON
you requested: {...}"), a field the model was supposed to omit when unknown
comes back as an invented placeholder, or an edge-case input produces
genuinely malformed output. **Defensive parsing** means the code path from
"raw response" to "usable Python object" is wrapped in real error handling,
not a bare, unguarded `json.loads(...)`:

- Wrap parsing in `try`/`except`, catching `json.JSONDecodeError`
  specifically (plus whatever your validation layer raises) rather than
  letting an unexpected shape crash the whole request.
- Have an explicit plan for partial or malformed output: retry the call
  (sometimes with a follow-up message pointing out the malformed output),
  fall back to a default/safe value, or surface a clear error to whatever
  called your function — rather than passing a partially-parsed or
  best-effort-guessed value further downstream as if it were trustworthy.
- Treat "the call succeeded (HTTP-level)" and "the content is valid and
  usable" as two separate, both-required conditions, not one thing.

### 3.4 Skepticism toward confident output

The final piece is a mindset, not a code pattern, and it's easy to
underweight precisely because it isn't a function you can write once: Claude,
like any LLM, can produce **fluent, well-formatted, entirely confident-
sounding text that is simply wrong** — a fabricated citation, a plausible but
incorrect number, a fact stated with no hedging that doesn't hold up. Nothing
about the *tone* of the output — its fluency, its confidence, its lack of
hedging language — is evidence of its correctness; models don't have a
reliable built-in signal for "I'm not sure about this" that shows up
consistently in surface phrasing. This matters most for anything high-stakes
or hard to casually double-check: financial figures, medical or legal claims,
citations to sources, factual assertions that will be acted on without
further review. The practical response is **downstream verification**
proportional to the stakes: cross-check generated facts or numbers against
an authoritative source rather than accepting them at face value, require
citations that are tied to content Claude was actually given (not ones it
generated from memory) when accuracy matters, add a secondary
verification step (a second model call, a rules-based check, or human
review) before a high-stakes output is acted on, and — as a general
engineering habit — treat "the response reads as confident" as exactly zero
evidence toward "the response is correct."

---

## Where to go from here

Work through `exercises/ex1_context_pruning_and_compaction.py`, then `ex2`,
then `ex3`, in that order. Each exercise's docstring explains what to build
and how to know you've succeeded, and notes that you can work through it by
reading and predicting/reasoning about output even without an API key
configured — though `ex2` and `ex3` are most useful when you can actually run
them against the live API and compare real outputs. Compare your work against
`solutions/` afterward. Finish with `quiz.md` to self-check your
understanding of all three skills in this domain before moving to the next
module.
