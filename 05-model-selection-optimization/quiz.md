# Module 05 Quiz — Model Selection and Optimization

**This is original, independently-written practice content created for this unofficial
self-study course.** It is inspired by the publicly published CCDV-F exam blueprint
(version 1.0, effective July 2026) but is NOT sourced from, nor a reproduction of, any real
Anthropic exam item. Treat it as practice for the *style and topic coverage* of the domain,
not as a leaked or predicted question bank.

Each question tells you exactly how many answer options to select. Some questions have one
correct answer; others have two. Write your answers down before checking the answer key at
the bottom.

---

**Question 1.** A developer is estimating whether a 12,000-character English-language
support article will fit comfortably inside a prompt, before calling an exact
tokenizer/count-tokens endpoint. Using the ~4-characters-per-token rule of thumb described
in this module, which of the following is the best rough token estimate for that article?

*Select 1 answer.*

A. ~120 tokens
B. ~750 tokens
C. ~3,000 tokens
D. ~12,000 tokens
E. ~48,000 tokens

---

**Question 2.** A team notices that calling the Messages API twice with the exact same
model, the exact same messages, and `temperature=0` sometimes still produces two slightly
different responses. Which of the following statements correctly describe why this can
happen? *Select 2 answers.*

A. Response generation is fundamentally probabilistic sampling over a predicted token
   distribution, and `temperature=0` makes the model *more* consistently favor its
   highest-probability token rather than *guaranteeing* byte-for-byte identical output on
   every call.
B. `temperature=0` is documented to make output fully and permanently deterministic, so any
   observed difference must indicate the API key was invalid on one of the two calls.
C. Non-determinism at low temperature can still occur due to factors like ties in the
   probability distribution or backend-level variation, so tests that assert exact string
   equality against live model output are fragile even at `temperature=0`.
D. The `anthropic` Python SDK caches the first response locally and replays it, so a
   second identical call should always return exactly the same text.
E. Because both calls used `temperature=0`, any difference in output must mean the second
   call silently used a different, unpinned model version.

---

**Question 3.** A developer is building a feature that answers simple FAQ-style questions
with a single sentence, and latency is the top priority for this feature. Which model
"mode" choice best fits this task, given what this module covers about fast/default mode
vs. extended thinking?

*Select 1 answer.*

A. Enable extended thinking with the maximum available thinking budget, to maximize answer
   quality regardless of the task's simplicity.
B. Use fast/default mode (no extended thinking), since the task is simple and doesn't
   benefit much from an intermediate reasoning phase, and extended thinking would add
   latency and output-token cost with little quality benefit here.
C. Extended thinking must always be enabled for every production call, per API
   requirements.
D. Use `temperature=1.0` instead of choosing a thinking mode, since temperature and
   thinking mode are two names for the same setting.

---

**Question 4.** A developer needs Claude to extract structured fields from unusual,
inconsistently-formatted invoices into a specific JSON shape with nested fields, and
initial zero-shot testing produced inconsistent output structure across several sample
invoices, including some category confusion on ambiguous line items. Which prompting
technique from this module is the most appropriate next step to try, per the guidance in
this module?

*Select 1 answer.*

A. Switch to zero-shot but repeat the instruction sentence three times, since repeating
   instructions is equivalent to giving examples.
B. Move to multi-shot (few-shot) prompting with several worked examples that include the
   exact target JSON shape and at least one ambiguous/edge-case invoice, since output
   format and edge-case discrimination are exactly what additional worked examples help
   with.
C. Lower `temperature` to 0 and change nothing else, since prompting technique has no
   effect on output-format consistency.
D. Switch to a different transport (websockets instead of HTTP) to fix formatting
   inconsistency.

---

**Question 5.** Which of the following statements accurately describe the relationship
between the official `anthropic` Python SDK and Claude's underlying REST API, as covered in
this module? *Select 2 answers.*

A. Calling `client.messages.create(...)` in the Python SDK ultimately sends an HTTPS
   request (e.g., a POST to a `/v1/messages`-style endpoint) with your API key in a header
   and a JSON request body — the SDK is a convenience wrapper around that HTTP call.
B. Because the SDK exists, understanding raw HTTP request/response structure is never
   useful — SDK users should never need to consult the raw API reference.
C. If a feature isn't yet exposed by the installed SDK version, or you're debugging
   unexpected behavior the SDK abstracts away, you can drop to raw HTTP (e.g., via
   `requests` or `curl`) against the same underlying API.
D. The SDK version and the underlying API version are the exact same version number and
   always change together, so pinning one automatically pins the other.
E. Websockets are the only transport the official SDK uses internally, and a plain HTTP
   request/response call is not possible through the SDK.

---

**Question 6.** A team is designing a feature that needs a single persistent, bidirectional
connection so either the client or the server can push new data at any time without
re-issuing a fresh HTTP request each time, for a continuous low-latency interactive
experience. Per this module's coverage of technical fundamentals, which transport concept
best matches that requirement, as an alternative to typical request/response HTTP calls?

*Select 1 answer.*

A. Prompt caching
B. WebSockets
C. Multi-shot prompting
D. Extended thinking

---

**Question 7.** A product team is choosing a model tier for a brand-new feature: routing
100,000 short, simple support messages per day into one of four fixed categories, where
per-message latency and cost matter a great deal and the classification task itself is
well-defined and not particularly ambiguous. Based on the Opus/Sonnet/Haiku tradeoff
concepts in this module, which tier is the best starting-point fit for this specific
feature?

*Select 1 answer.*

A. Opus-class, because higher volume always justifies the most capable tier available.
B. Haiku-class, because the task is simple/well-defined and volume makes per-call
   latency and cost the dominant concern, which is exactly the profile this tier is
   optimized for.
C. Whichever tier has the largest context window, regardless of latency or cost, since
   context window size is the only relevant selection criterion.
D. It is impossible to choose without first enabling extended thinking on every candidate
   model.

---

**Question 8.** A team has a production feature calling Claude with a model identifier
pinned to a specific dated version string. A teammate proposes switching the code to use a
floating "latest" alias instead, arguing it will "auto-upgrade to the best model for free."
Which of the following are accurate cautions from this module's coverage of model
selection and tradeoffs regarding that proposal? *Select 2 answers.*

A. A new model version is not guaranteed to be strictly better at every behavior your
   application implicitly depends on — it can change instruction-following style,
   verbosity, formatting, or edge-case handling in ways that break a prompt tuned against
   the old version.
B. Pinning a specific version and deliberately re-testing (e.g., re-running an eval suite)
   before adopting a new version gives the team control over *when* behavior changes reach
   production, rather than being surprised by an automatic version change.
C. Floating "latest" aliases are required by Anthropic for all production traffic, so the
   teammate's proposal is simply how the API must be used.
D. This concern is purely theoretical and has no connection to configuration-management
   practices covered elsewhere in this course.
E. A newer model version is always a strictly better, drop-in replacement with no behavior
   differences from the version it replaces, so re-testing before adoption is unnecessary.

---

**Question 9.** A developer wants to build a running cost dashboard for a Claude-powered
feature. According to this module, which approach best matches the recommended pattern for
token usage tracking and cost modeling?

*Select 1 answer.*

A. Hardcode a single dollar figure per API call directly in application code, since all
   calls cost the same regardless of model or token count.
B. After each API response, read the token counts from the response's `usage` object (at
   minimum `input_tokens` and `output_tokens`), and compute cost using a per-model,
   per-token (or per-million-token) price lookup kept as configuration rather than inline
   literals — since price differs by model tier and by input vs. output tokens.
C. Estimate cost purely from the character length of the prompt string sent, and ignore the
   response entirely, since output tokens are not billed.
D. Skip tracking entirely, since Anthropic's console dashboard is the only permissible way
   to observe usage, per this module.

---

**Question 10.** A conversational agent resends the same large, unchanging system prompt
and a large fixed set of tool definitions on every single turn of a long multi-turn
tool-use session, plus a large reference document that stays constant across an entire
user session. Which of the following statements about applying prompt caching to this
scenario are accurate, per this module? *Select 2 answers.*

A. Marking the static system-prompt/tool-definition block as cacheable at one breakpoint,
   and separately marking the large reference document as cacheable at another breakpoint,
   is an example of using multiple cache breakpoints (cache checkpointing) so each static
   section can be reused independently.
B. Prompt caching helps most when a large static prefix is reused across many calls in a
   short window, which matches this scenario's repeatedly-resent system prompt, tool
   definitions, and reference document — without caching, that same static content would be
   billed again at full input-token price on every turn.
C. Prompt caching has no cost implications at all — cached and non-cached input tokens are
   always billed at exactly the identical rate, so there is no reason to use it beyond
   convenience.
D. Prompt caching is only usable for output tokens, never for input content like system
   prompts or documents.
E. A single request is limited to exactly one cache boundary for the entire prompt, so the
   system prompt and the reference document in this scenario could not be cached
   independently of each other.

---

## Answer key and rationale

**1. C — ~3,000 tokens.**
Using the ~4-characters-per-token rule of thumb: 12,000 characters / 4 ≈ 3,000 tokens. (A)
and (B) are both too low. (D) confuses character count with token count directly (treating
the ratio as 1:1). (E) is far too high. Remember this is a rough heuristic, not an exact
count — for a precision-sensitive case (e.g. right at a context-window boundary), use an
exact tokenizer/count-tokens call instead.

**2. A, C.**
(A) and (C) both correctly reflect that generation is sampling-based and that
`temperature=0` makes output *more* deterministic without making exact repetition an
absolute guarantee. (B) is wrong — the module explicitly says not to treat `temperature=0`
as a guarantee of identical output, and an invalid API key would cause an authentication
error, not a subtly different valid response. (D) is wrong — the SDK does not locally cache
and replay prior responses. (E) is an unsupported leap — a small output difference does not
imply a different model version was silently used.

**3. B.**
Fast/default mode fits a simple, low-latency-priority task well; extended thinking adds an
intermediate reasoning phase that costs extra latency and output tokens, which is not a
good trade for a task this simple. (A) contradicts the "match reasoning depth to task
difficulty" principle. (C) is factually wrong — extended thinking is not a mandatory
setting for every call. (D) incorrectly conflates temperature (a sampling parameter) with
thinking mode (a reasoning-process setting) — they are distinct concepts.

**4. B.**
Multi-shot/few-shot prompting, especially with examples covering the exact target format
and ambiguous edge cases, directly targets both problems observed (inconsistent structure,
edge-case confusion) per this module's prompting-technique guidance. (A) misunderstands
what an "example" is — repeating an instruction sentence is not the same as demonstrating
input→output pairs. (C) is wrong because prompting technique (example count/content) does
meaningfully affect format consistency, independent of temperature. (D) is a non sequitur —
transport choice (HTTP vs websockets) has nothing to do with output formatting.

**5. A, C.**
(A) correctly describes the SDK-wraps-REST relationship, and (C) correctly describes the
ability to drop to raw HTTP when needed — both stated directly in this module. (B) is wrong
— the module explicitly says understanding raw HTTP can be valuable even when using the
SDK, not that it's never useful. (D) is wrong — SDK version and API version can and do
evolve somewhat independently; they are not the same version number by definition. (E) is
wrong — HTTP request/response (with optional streaming) is the SDK's normal/default
transport; websockets are described as an alternative for certain real-time contexts, not
the SDK's only mode.

**6. B — WebSockets.**
WebSockets provide a persistent, bidirectional connection matching the described
requirement. (A) Prompt caching is a cost-optimization technique, unrelated to transport.
(C) Multi-shot prompting is a prompting technique, not a transport. (D) Extended thinking is
a reasoning mode, not a transport.

**7. B — Haiku-class.**
High volume, low task complexity, and latency/cost sensitivity is exactly the profile this
module maps to the fastest/cheapest tier. (A) is the opposite of the cost/latency-aware
tradeoff this domain teaches — volume alone does not justify the most expensive tier when
the task is simple. (C) ignores latency/cost entirely, which contradicts the scenario's
stated priorities. (D) is a non sequitur — tier selection does not require enabling
extended thinking first.

**8. A, B.**
(A) and (B) directly reflect the module's cautions about breaking behavior changes across
releases and the value of deliberate, tested version adoption before moving production
traffic to a new version. (C) is factually wrong — using a "latest" alias is not an
Anthropic requirement; pinning a specific version is a normal and often preferable choice.
(D) is wrong — the module explicitly ties this concern to Configuration Management
practices covered elsewhere in the course. (E) is wrong and is exactly the risky assumption
the teammate's proposal rests on — the module explicitly warns that a new version is not
guaranteed to be a behavior-neutral drop-in replacement, which is precisely why re-testing
before adoption matters.

**9. B.**
Reading `usage.input_tokens` / `usage.output_tokens` per call and modeling cost from a
per-model, per-token-type price configuration is exactly the pattern this module
recommends. (A) is wrong because per-token pricing varies by model tier and by input vs.
output token type — a single flat number is not accurate. (C) is wrong because output
tokens are billed and should not be ignored, and character-length estimates are a rough
substitute for actual token counts, not a replacement for reading real usage data. (D) is
wrong — the module explicitly recommends application-level usage tracking (e.g., logging
the `usage` object) in addition to whatever the console shows.

**10. A, B.**
(A) correctly describes cache checkpointing/multiple breakpoints. (B) correctly describes
when caching pays off and what happens without it (full-price re-billing of the same static
content every turn). (C) is wrong — cached tokens are billed differently (typically a
reduced rate for cache reads, with some premium for the initial cache write), that
difference is the entire point of the feature. (D) is wrong — prompt caching applies to
input content (system prompts, documents, tool definitions), not output tokens. (E) is
wrong — the module explicitly describes support for multiple cache breakpoints in a single
request, contradicting the "exactly one boundary" claim.
