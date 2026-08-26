# Module 02 Quiz — Applications and Integration

**These are original practice questions written for this self-study course. They are NOT
real CCDV-F exam questions and are not reproduced or adapted from Anthropic's item bank.**
They're written in a similar scenario-based style to the exam blueprint's own illustrative
samples, to help you self-test across this domain's six skills before the real exam. Each
question states how many answers to select.

Work through all 12, then check your answers against the key at the bottom. Don't peek
early -- if you get one wrong, go back and re-read the relevant README section before
moving on.

---

**Q1.** A team is scoping a new internal tool: an assistant that drafts replies to
customer emails for a human agent to review and send. The business says "responses should
feel instant" and "we can't have it send anything without a human clicking send first."
Which TWO of the following are correctly classified as *infrastructure* (non-functional)
requirements, as opposed to functional requirements, for this system?

A. The system must never send an email automatically without explicit human approval.
B. The draft must be generated and shown to the agent within roughly 2 seconds of the
   request.
C. The system must produce a draft reply addressing the customer's original question.
D. The system must remain responsive under peak support-queue load without agents
   experiencing multi-second UI freezes.

*(Select TWO.)*

---

**Q2.** During the "operate" stage of a deployed Claude-powered feature's life cycle,
which ONE of the following is the most appropriate activity to be actively monitoring,
specifically because the system has an LLM as a core component (as opposed to a purely
deterministic system)?

A. Server CPU and memory utilization.
B. Output quality drift and rate of policy-violating responses in production traffic.
C. HTTP response status code distribution.
D. Database connection pool saturation.

*(Select ONE.)*

---

**Q3.** In the Messages API, where does the `system` prompt belong in a request?

A. As a message in the `messages` array with `"role": "system"`.
B. As a top-level `system` parameter, separate from the `messages` array.
C. As the first content block of the first user message.
D. It cannot be set per-request; it's configured once per API key.

*(Select ONE.)*

---

**Q4.** A developer is building a chat UI and wants the user to see Claude's answer
appear progressively rather than all at once. Which ONE statement about streaming is
correct?

A. Streaming reduces the total number of tokens billed for the response.
B. Streaming delivers the response via Server-Sent Events, improving perceived latency
   without changing total token cost.
C. Streaming is only available when extended thinking is disabled.
D. Streaming requires the batch API.

*(Select ONE.)*

---

**Q5.** A team sends a 6,000-token system prompt (a product FAQ document) on every
request to a high-traffic customer-facing chatbot that receives hundreds of requests per
minute, all sharing that exact same system prompt text. Which TWO of the following are
true about applying prompt caching here?

A. Caching is a good fit: the block is large, static, and reused across many requests
   within a short time window.
B. The first request after the cache is cold will show tokens under
   `cache_creation_input_tokens` rather than `cache_read_input_tokens`.
C. Caching provides no benefit unless extended thinking is also enabled.
D. Caching only works if every request also contains an identical user message, not just
   an identical system prompt.

*(Select TWO.)*

---

**Q6.** A company needs to classify 50,000 archived support tickets by category, purely
for an offline analytics dashboard that's rebuilt once a week. Nothing in the pipeline is
waiting synchronously on any individual classification. Which ONE approach best fits the
stated requirements?

A. A sequential loop of realtime `messages.create` calls, one ticket at a time.
B. The Message Batches API, submitting all 50,000 requests together.
C. A synchronous call inside the web server's request handler, triggered per page view.
D. Extended thinking with a large thinking budget on each ticket, to maximize accuracy
   regardless of cost or latency.

*(Select ONE.)*

---

**Q7.** A developer needs to make 200 independent Claude calls (each summarizing a
different short document) as part of a nightly job that must finish within about 10
minutes, well before the batch API's typical processing window would reliably complete.
Which ONE approach is the best fit, considering both the time constraint and standard
software engineering practice?

A. A sequential `for` loop using the synchronous client, one call at a time.
B. The Message Batches API.
C. `asyncio` with the async client and `asyncio.gather`, issuing calls concurrently
   (with reasonable concurrency limits to respect rate limits).
D. Extended thinking, to reduce the number of calls needed.

*(Select ONE.)*

---

**Q8.** Which TWO of the following are genuine risks of blurring the boundary between
system content and user content when constructing a prompt (e.g., concatenating untrusted
document text directly into the system prompt)?

A. It increases the system's vulnerability to prompt injection from content that should
   have been treated as untrusted.
B. It makes the request invalid JSON and the API call will fail outright.
C. It can make it harder to reason about and enforce which instructions are meant to be
   authoritative versus which content is just data to be processed.
D. It guarantees the response will exceed `max_tokens`.

*(Select TWO.)*

---

**Q9.** A team is building a multi-turn support chatbot. After a few dozen turns in a long
session, they notice requests getting slower and more expensive, with no corresponding
increase in answer quality. Which ONE practice most directly addresses this?

A. Switching from the sync client to the async client.
B. Applying session/conversation hygiene: trimming, summarizing, or capping the growth of
   message history sent on each request.
C. Enabling extended thinking so Claude reasons more carefully about long histories.
D. Switching the request from realtime to the batch API.

*(Select ONE.)*

---

**Q10.** A project's `settings.json` currently auto-allows Claude Code to run any `git
push` command without confirmation, including to the `main` branch of a shared repo, and
its `CLAUDE.md` has not been updated in over a year despite several major refactors since.
Which TWO of the following are reasonable configuration-management concerns to raise in a
review of this setup?

A. Auto-allowing unrestricted `git push` to a shared `main` branch removes a human
   checkpoint from a high-impact, hard-to-reverse action.
B. A stale `CLAUDE.md` risks actively misleading Claude with outdated project context
   and conventions.
C. `settings.json` and `CLAUDE.md` are interchangeable files serving the same purpose, so
   only one needs to be reviewed.
D. Neither file is version-controllable, so review is not meaningful.

*(Select TWO.)*

---

**Q11.** Why is pinning a specific, dated model version (rather than a "latest"-style
alias) generally recommended for a production Claude integration?

A. Dated versions are always cheaper per token than aliases.
B. It prevents an alias from silently pointing at a different underlying model at a time
   outside the team's control, which could change behavior, cost, or latency without a
   corresponding code change.
C. Aliases are deprecated faster than dated versions, so pinning avoids deprecation
   entirely.
D. It's required by the API -- aliases cannot be used in `model`.

*(Select ONE.)*

---

**Q12.** A support-ticket classifier needs its output consumed by a downstream database
insert, so it must reliably be valid, parseable data rather than free-form prose. Which
TWO practices best support good schema design for this structured-output use case?

A. Ask for a fixed, small set of fields with a constrained value set (e.g., an enum for
   `category`) rather than open-ended free text wherever the possible values are known in
   advance.
B. Decide up front how the system will handle a response that doesn't match the expected
   schema (e.g., detect and retry with the validation error shown back to Claude), rather
   than assuming every response will always validate.
C. Always instruct Claude to write a multi-paragraph explanation before any structured
   field, to maximize accuracy.
D. Avoid specifying a schema at all, since the model will infer the desired structure
   correctly from the field names in the surrounding prose.

*(Select TWO.)*

---

## Answer key and rationale

**Q1: B, D.** Latency ("feels instant," "responsive under peak load") is infrastructure
(non-functional) — it's about *how well* the system performs, not *what* it does. A and C
describe *what* the system must do (its behavior/output), which makes them functional
requirements, not infrastructure ones — a common mix-up worth watching for.

**Q2: B.** Traditional infra metrics (CPU, HTTP status codes, DB connections — A, C, D)
still matter, but they're not specific to having an LLM as a component. Output quality
drift and policy-violation rate are exactly the kind of thing that's *new* to monitor
because outputs are generative and non-deterministic, and is easy to under-invest in if a
team only carries over conventional ops monitoring.

**Q3: B.** `system` is a top-level parameter in the Messages API request, separate from
the `messages` array — not a `role: "system"` message (that's a pattern from some other
chat APIs, and a common point of confusion when switching to Claude's API).

**Q4: B.** Streaming changes *when* content is delivered (progressively, via SSE),
improving perceived latency for the user — it does not reduce total tokens/cost, and it
isn't gated on thinking being off or requiring the batch API (those are separate, unrelated
mechanisms).

**Q5: A, B.** This is close to an ideal caching scenario: large (6,000 tokens, comfortably
above minimum cacheable length), completely static, and hit very frequently (hundreds of
requests per minute keeps it well within the cache's short lifetime) — A is correct. B
describes the standard write/read pattern correctly: the first (cold) request creates the
cache and shows creation tokens, not read tokens. C and D describe made-up dependencies —
caching doesn't require extended thinking, and it works on the cached prefix itself
regardless of what varies afterward in the user message.

**Q6: B.** Nothing is waiting synchronously, the volume is large (50,000), and there's no
tight latency requirement (a weekly rebuild) — this is close to a textbook batch API use
case, including its cost discount at that volume. A would work but is slower and pricier
than necessary at this scale; C wrongly couples an offline batch job to live request
handling; D adds cost/latency for a task (categorization) that doesn't need heavy
reasoning, and doesn't itself solve the volume/urgency question.

**Q7: C.** The 10-minute deadline rules out the batch API's typical (much longer, less
predictable) completion window, ruling out B. A sequential loop (A) would leave most of
that available time unused while waiting on network I/O one call at a time. Extended
thinking (D) doesn't reduce call count and adds latency, working against the time
constraint. Concurrent async calls (C) let the 200 largely-I/O-bound calls overlap their
wait time, fitting both the deadline and the "independent calls" shape well.

**Q8: A, C.** Blurring system/user (or system/tool) content boundaries is a real security
and maintainability concern: it widens the prompt-injection attack surface (A) and makes
it harder to keep "authoritative instruction" cleanly separated from "data being
processed" (C). B and D describe consequences that don't actually follow from this
practice — it's a content-boundary/design problem, not a JSON-validity or token-limit
problem.

**Q9: B.** Growing latency/cost without a quality benefit across a long multi-turn session
is the classic signature of an unbounded, ever-growing message history being resent on
every call — the fix is deliberate session hygiene (trimming/summarizing/capping), not a
sync/async change (A, which addresses concurrency, not history size), extended thinking (C,
which adds cost, doesn't reduce it), or batch (D, which doesn't fit a live multi-turn
chatbot at all).

**Q10: A, B.** Auto-allowing unrestricted pushes to a shared `main` removes a meaningful
human checkpoint on an action that's high-impact and hard to reverse — a real permissions
design concern. A stale `CLAUDE.md` is a real risk too: it can actively steer Claude toward
outdated conventions or removed commands. C and D are both false statements about these
files — `settings.json` and `CLAUDE.md` serve distinct purposes (permissions/tool
config vs. project context/instructions) and both are ordinary text files that belong in,
and benefit from, version control and review.

**Q11: B.** The core reason is reproducibility and control: pinning avoids a
silent behavior/cost/latency shift from an alias moving underneath you at a time you
didn't choose. A and C assert made-up guarantees (pricing and deprecation timing aren't
tied to pinning in the way stated). D is false — aliases are a normal, supported value for
`model`; pinning a dated version is a choice, not the only option.

**Q12: A, B.** Constraining the output shape up front (fixed fields, enums where the value
set is known — A) and planning explicit handling for the case where output doesn't match
the schema (B) are the core structured-output design practices. C actively works against
reliable parsing by encouraging unstructured prose ahead of the structured data. D is a bad
practice — leaving structure to inference rather than an explicit schema/instruction
increases the odds of inconsistent or unparseable output, which is exactly the failure mode
this scenario needs to avoid.
