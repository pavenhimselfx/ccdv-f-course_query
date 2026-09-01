# Domain 2 Quiz — My Results (2026-09-01)

Score: 10/12. See `quiz.md` for the original questions and the course's own
answer key/rationale — this file is my personal answer log plus reasoning
for each question, including why the two misses were wrong.

| Q | My answer | Correct | Result |
|---|-----------|---------|--------|
| 1 | A, D | B, D | ❌ |
| 2 | A | B | ❌ |
| 3 | B | B | ✅ |
| 4 | B | B | ✅ |
| 5 | A, B | A, B | ✅ |
| 6 | B | B | ✅ |
| 7 | C | C | ✅ |
| 8 | A, C | A, C | ✅ |
| 9 | B | B | ✅ |
| 10 | A, B | A, B | ✅ |
| 11 | B | B | ✅ |
| 12 | A, B | A, B | ✅ |

---

**Q1 — Email-draft assistant, functional vs. infrastructure requirements.**
Answered A, D. D is correct; A is not. A ("must never send an email
automatically without explicit human approval") sounds like a
safety/governance concern, but it describes *what the system does* — a
behavioral gate on an action — which makes it functional, not
infrastructure. D ("remain responsive under peak load without multi-second
UI freezes") is purely about performance characteristics, which is exactly
what infrastructure requirements are. Correct set: B and D — the two
statements that are only about speed/responsiveness, not behavior.

**Q2 — What's worth monitoring at the "operate" stage specifically because
the system has an LLM component?** Answered A (server CPU/memory) — wrong.
Correct: B, output quality drift and policy-violation rate. CPU/memory,
HTTP status codes, and DB connection saturation are all standard ops
metrics relevant to *any* deployed system, LLM or not — they don't answer
"what's different here." Quality drift is the thing that's genuinely new
and easy to under-invest in: a generative component can silently get worse
or start producing policy-violating output while every conventional infra
metric still looks perfectly healthy.

**Q3 — Where does the `system` prompt go in a Messages API request?**
Answered B — correct. It's a top-level `system` parameter, separate from
the `messages` array — not a `role: "system"` message the way some other
chat APIs do it. A common point of confusion when coming from a different
provider's API shape.

**Q4 — What does streaming actually do?** Answered B — correct. Streaming
changes *when* content is delivered (progressively, via Server-Sent
Events), improving perceived latency — it does not reduce total tokens
billed, and isn't gated on extended thinking or tied to the batch API.

**Q5 — Prompt caching fit: 6,000-token static system prompt, hundreds of
requests/minute, all identical.** Answered A, B — correct. This is close to
an ideal caching scenario: large enough to clear the minimum cacheable
length, completely static, and hit frequently enough to stay well within
the cache's short lifetime (A). The first (cold) request creates the cache
and shows tokens under `cache_creation_input_tokens`, not
`cache_read_input_tokens` — the standard write-then-read pattern (B).
Caching has no dependency on extended thinking, and works on the cached
prefix itself regardless of what varies in the user message afterward.

**Q6 — 50,000 archived tickets, offline weekly dashboard, nothing waiting
synchronously.** Answered B (Batch API) — correct. Large volume, no tight
latency requirement, nothing synchronously blocked on any individual
result — a textbook batch use case, including the cost discount at that
scale. A sequential loop would work but is needlessly slow/pricier; a
synchronous per-page-view call wrongly couples an offline job to live
request handling; heavy extended-thinking budget adds cost/latency without
addressing volume or urgency at all.

**Q7 — 200 independent calls, nightly job, ~10-minute deadline (shorter
than batch's typical window).** Answered C (asyncio + gather) — correct.
The hard 10-minute deadline rules out batch's much longer, less predictable
completion window. A sequential loop would leave most of the available time
sitting idle waiting on network I/O one call at a time. Extended thinking
doesn't reduce call count and adds latency, working against the deadline.
Concurrent async calls let the largely I/O-bound calls overlap their wait
time — this is exactly the shape I measured directly in ex5 (10.05s
sequential vs. 1.96s concurrent for 5 calls).

**Q8 — Risks of blurring system/user content boundaries in a prompt.**
Answered A, C — correct. Concatenating untrusted content directly into the
system prompt widens the prompt-injection attack surface (A) and makes it
harder to keep "authoritative instruction" cleanly separated from "data
being processed" (C). It doesn't produce invalid JSON or guarantee
exceeding `max_tokens` — those aren't real consequences of this practice.

**Q9 — Multi-turn chatbot getting slower/pricier after dozens of turns,
no quality gain.** Answered B (session hygiene: trim/summarize/cap history)
— correct. This is the classic signature of an unbounded, ever-growing
message history being resent in full on every call. Switching sync→async
addresses concurrency, not history size; extended thinking adds cost rather
than reducing it; batch doesn't fit a live multi-turn chat at all.

**Q10 — Reviewing a settings.json that auto-allows unrestricted `git push`
to shared `main`, plus a year-stale CLAUDE.md.** Answered A, B — correct.
Auto-allowing unrestricted pushes to a shared main branch removes a
meaningful human checkpoint from a high-impact, hard-to-reverse action (A).
A stale CLAUDE.md is a real risk too — it can actively steer Claude toward
outdated conventions or commands that no longer exist (B). The two false
options claimed settings.json and CLAUDE.md are interchangeable (they
serve distinct purposes: permissions/tool config vs. project context) and
that neither file is version-controllable (both are ordinary text files
that belong in git).

**Q11 — Why pin a dated model version instead of a "latest" alias?**
Answered B — correct. The core reason is reproducibility and control:
pinning prevents an alias from silently pointing at a different underlying
model at a time outside the team's control, which could shift behavior,
cost, or latency with no corresponding code change. Cost and deprecation
timing aren't actually tied to pinning the way the wrong options claimed,
and aliases are a normal supported value for `model` — pinning is a choice,
not a requirement.

**Q12 — Schema design for a ticket classifier feeding a downstream DB
insert.** Answered A, B — correct. Constraining the output shape up front
(fixed fields, enums where the value set is known — A) and deciding in
advance how to handle a response that doesn't match the schema, e.g.
detect-and-retry with the validation error shown back to Claude (B), are
the core structured-output practices. Asking for a multi-paragraph
explanation before the structured field actively works against reliable
parsing, and skipping a schema entirely and hoping the model infers
structure from prose increases the odds of inconsistent, unparseable
output — exactly the failure mode this scenario needs to avoid.

---

## Pattern to remember

Both misses (Q1, Q2) picked an answer that was a *real, legitimate concern
in general* but not the specific thing the question was isolating:

- Q1: A is a genuine safety/governance rule, but the question was asking
  functional vs. infrastructure specifically — and A describes behavior,
  not performance.
- Q2: CPU/memory is a genuine thing to monitor, but the question asked
  what's worth watching *because the system has an LLM component* — CPU/
  memory doesn't answer that; it's true of any deployed system.

General tell for this exam: read the qualifier in the question stem
carefully ("as opposed to functional," "specifically because it has an LLM
component") — a technically-true statement that ignores the qualifier is
still a wrong answer. This mirrors the same trap pattern from the Domain 1
quiz ([../01-agents-and-workflows/quiz-results.md](../01-agents-and-workflows/quiz-results.md)):
an answer that sounds sophisticated or generally correct but doesn't
address the specific mechanism/distinction the question is actually
testing.
