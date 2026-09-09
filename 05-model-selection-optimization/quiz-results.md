# Domain 5 Quiz — My Results (2026-09-09)

Score: 9/10. See `quiz.md` for the original questions and the course's own
answer key/rationale — this file is my personal answer log plus reasoning
for each question, including why the one miss was wrong.

| Q | My answer | Correct | Result |
|---|-----------|---------|--------|
| 1 | C | C | ✅ |
| 2 | A, C | A, C | ✅ |
| 3 | B | B | ✅ |
| 4 | B | B | ✅ |
| 5 | A, C | A, C | ✅ |
| 6 | B | B | ✅ |
| 7 | B | B | ✅ |
| 8 | A, B | A, B | ✅ |
| 9 | B | B | ✅ |
| 10 | B, D | A, B | ❌ |

---

**Q1 — Estimating tokens for a 12,000-character English article via the
~4 chars/token rule.** Answered C (~3,000 tokens) — correct. 12,000 / 4 =
3,000. A and B are too low, D wrongly treats the ratio as 1:1
(characters == tokens), E is far too high. This matches what I measured
directly in [ex1_tokens_and_sampling.py](exercises/ex1_tokens_and_sampling.py):
the heuristic is a rough floor, not exact — real usage undershot the
heuristic by ~1.2x-7.5x depending on content type, so even a "correct"
heuristic answer like this one should be treated as a ballpark, not a
number to trust at a context-window boundary.

**Q2 — Why identical calls at temperature=0 can still differ.** Answered
A, C — correct. Generation is fundamentally probabilistic sampling; low
temperature makes the model *more* consistently favor its top token
without guaranteeing byte-for-byte identical output (A). Ties in the
distribution or backend-level variation mean tests asserting exact string
equality against live output are fragile even at temperature=0 (C). B
wrongly claims temperature=0 is a hard determinism guarantee and invents
an unrelated auth-failure explanation; D invents local response caching
the SDK doesn't do; E is an unsupported leap from "output differs
slightly" to "a different model version must have been used." I saw this
exact behavior for real in ex1: three identical prompts at default
settings (no way to even lower temperature on that model) produced three
genuinely different responses.

**Q3 — Simple FAQ feature, latency is top priority: which mode?** Answered
B (fast/default mode) — correct. A simple, low-latency task doesn't
benefit from an intermediate reasoning phase, and extended thinking adds
latency and output-token cost for little quality gain here. A contradicts
matching reasoning depth to task difficulty; C is factually wrong (thinking
is not mandatory for every call); D conflates two distinct concepts
(temperature = sampling randomness, thinking mode = reasoning process) —
exactly the distinction [ex1](exercises/ex1_tokens_and_sampling.py)
demonstrated empirically (raising effort didn't behave like raising
temperature at all).

**Q4 — Inconsistent structured-extraction output on ambiguous invoices:
best next step.** Answered B (move to multi-shot with the exact target
JSON shape and an edge-case example) — correct. This directly targets both
observed problems: inconsistent structure and edge-case confusion. A
misunderstands what an "example" is (repeating an instruction isn't
demonstrating input→output pairs); C wrongly claims prompting technique
has no effect on format consistency; D is a non sequitur (transport choice
is unrelated to output formatting). This is the same lever
[ex2_prompting_techniques.py](exercises/ex2_prompting_techniques.py)
exercised directly, including the deliberate edge-case example in the
few-shot prompt.

**Q5 — SDK vs. REST API relationship.** Answered A, C — correct. The SDK
is a convenience wrapper sending real HTTPS requests with the API key in a
header and a JSON body (A), and you can drop to raw HTTP when a feature
isn't yet exposed by the installed SDK or you're debugging SDK-abstracted
behavior (C). B wrongly claims understanding raw HTTP is never useful; D
wrongly claims SDK version and API version are the same number and always
move together; E wrongly claims websockets are the SDK's only transport.

**Q6 — Persistent, bidirectional, push-anytime connection: which
transport?** Answered B (WebSockets) — correct. A is a cost-optimization
technique, C is a prompting technique, D is a reasoning mode — none are
transports.

**Q7 — Model tier for 100,000 simple, well-defined, latency/cost-sensitive
classifications/day.** Answered B (Haiku-class) — correct. Simple task +
high volume + latency/cost sensitivity is exactly Haiku's optimized
profile. A wrongly claims volume alone justifies the most expensive tier;
C ignores latency/cost entirely; D is a non sequitur. This is the same
conclusion [ex3](exercises/ex3_model_tier_comparison.py) and
[ex4](exercises/ex4_cost_tracking.py) reached with real numbers: Haiku
matched Opus's correctness on a genuine reasoning task at ~54% of the
latency, and the same trivial-task cost projected to volume showed a
real >$15,000/year gap between tiers for zero measured benefit.

**Q8 — Cautions against switching a pinned model version to a floating
"latest" alias.** Answered A, B — correct. A new version isn't guaranteed
to be strictly better at every behavior an application depends on (A), and
pinning + deliberate re-testing before adoption gives the team control
over *when* behavior changes reach production (B). C wrongly claims
floating aliases are an Anthropic requirement; D wrongly claims this is
unconnected to configuration-management practice; E is exactly the risky
assumption the scenario's teammate is making, which the module explicitly
warns against.

**Q9 — Recommended pattern for a running cost dashboard.** Answered B
(read `usage.input_tokens`/`output_tokens` per call, price via a
per-model/per-token-type config lookup) — correct. A wrongly assumes a
flat per-call cost; C wrongly ignores billed output tokens entirely; D
wrongly claims the console dashboard is the only permissible tracking
method. This is exactly what
[ex4_cost_tracking.py](exercises/ex4_cost_tracking.py) implements and unit
-tests: `estimate_cost()` keyed by model, `CostTracker` accumulating real
`usage` data, raising `KeyError` rather than silently returning `$0` for
an unpriced model.

**Q10 — Caching a large static system prompt, tool-definition set, and
reference document resent every turn.** Answered B, D. B is correct
(caching helps most on a large static prefix reused across many calls in a
short window; without it, that content is billed at full price every
turn). **D is wrong** — correct: **A**. D claims "prompt caching is only
usable for output tokens, never for input content like system prompts or
documents" — this is backwards. Caching applies specifically to **input**
content (system prompts, tool definitions, documents) to avoid re-billing
static content at full price repeatedly; output tokens aren't what gets
cached at all. A is the correct second answer: marking the system-prompt/
tool-definition block cacheable at one breakpoint and the reference
document at a separate breakpoint is precisely cache checkpointing
(multiple breakpoints), which the question's own scenario describes almost
verbatim (a system prompt + tool defs + a separate reference document, all
static but distinct).

---

## Pattern to remember

The one miss (Q10) is the same trap shape flagged in every prior domain's
quiz results
([01](../01-agents-and-workflows/quiz-results.md),
[02](../02-applications-and-integration/quiz-results.md),
[03](../03-claude-code/quiz-results.md)):
a confidently-worded, absolute-sounding statement that inverts which side
of a relationship something applies to. D didn't just get a detail wrong —
it stated the *opposite* of the real mechanism (caching is for input, not
output). The general tell: when an answer option makes a flat, sweeping
claim ("only usable for X, never Y," "always," "never," "purely
theoretical," "impossible without"), that's exactly where to slow down and
check whether it's actually the reverse of the true relationship, rather
than assume confident phrasing tracks with correctness.
