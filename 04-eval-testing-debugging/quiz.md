# Module 04 Quiz — Eval, Testing, and Debugging

**This is original practice content written for this unofficial, independently-built
self-study course.** It is inspired by the CCDV-F exam blueprint's Domain 4 ("Eval,
Testing, and Debugging," 2.6%) but is not written or endorsed by Anthropic, and none of
these questions reproduce real exam items. Use it to check your understanding, not as a
prediction of exact exam content.

Each question states how many answers to select. Work through all six before checking the
answer key at the bottom.

---

### Question 1 (Select 1)

Your application calls the Messages API and receives an HTTP 429 response with a
`rate_limit_error` type and no `retry-after` header. Your logs show this same account has
been receiving 429s continuously for the last 20 minutes, and your team confirms the
account is currently over its monthly spend cap.

What is the most appropriate handling for this specific situation?

A. Retry immediately in a tight loop until a request succeeds — 429s are always transient.
B. Apply exponential backoff with jitter and keep retrying indefinitely; the missing
   `retry-after` header just means the SDK's default backoff schedule should be used instead.
C. Recognize that a spend-cap-driven 429 will not resolve itself through retrying, stop
   automatic retries for this failure, and surface it for the spend cap to be
   raised/reset rather than continuing to consume request budget on retries.
D. Treat this identically to a `500 api_error` and fall back to a different, smaller model.

---

### Question 2 (Select 2)

Which TWO of the following are appropriate uses of "validate and re-prompt" as a recovery
strategy?

A. The model returns a JSON object missing a required field your schema expects.
B. The API returns a `401 authentication_error` because the configured API key was revoked.
C. The model's response is well-formed JSON but the value in one field doesn't match any
   of the enum values your downstream code accepts.
D. The API returns a `413 request_too_large` because an embedded base64 image pushed the
   request body over the endpoint's size limit.

---

### Question 3 (Select 1)

An agent trace shows: (1) the user asks for the total spent on "Project Falcon" last
quarter; (2) the assistant calls a `query_budget` tool with `project="Project Falcon",
quarter="Q2"`; (3) the tool returns Q2 totals for Project Falcon; (4) the assistant
replies with the Q2 total, describing it as "last quarter's spend." At the time of the
conversation, "last quarter" was actually Q1. Nothing in the conversation ever mentioned
which calendar quarter "last quarter" maps to.

What is the most likely origin of this failure, and where does the strongest fix belong?

A. Integration-layer bug — the tool implementation must have a bug in how it computes
   quarter totals; fix the `query_budget` function.
B. Model-output issue — the model resolved a relative time reference ("last quarter")
   without any information establishing the current date, so it guessed; the fix belongs
   in the application layer, by supplying the current date (or an already-resolved
   quarter) in context rather than relying on the model to infer it.
C. Integration-layer bug — the tool's schema is missing a required parameter, and this is
   purely a schema-design defect.
D. Not resolvable — relative date references can never be handled reliably by an LLM
   application, so this feature should be removed entirely.

---

### Question 4 (Select 1)

You are debugging a failing agent run and want to determine whether a wrong tool-call
argument was caused by your integration code or by the model itself. Which single check
gives you the strongest evidence toward an integration-layer explanation, as opposed to a
model-output explanation?

A. Re-running the exact same turn with the exact same (correct) input reproduces the
   wrong argument again.
B. Comparing the literal request payload actually sent to the API for that turn against
   what you intended to send, and finding they differ — e.g., a prior turn's tool result
   was dropped or corrupted before being sent back to the model.
C. The tool call's argument value doesn't appear anywhere in the visible conversation
   history.
D. The model's text explanation of its own reasoning, read on its own, sounds confident.

---

### Question 5 (Select 1)

A production application wraps every Claude API call in a retry loop with exponential
backoff and a generous 8-attempt budget, applied uniformly to every exception type the
SDK can raise, including `authentication_error` and `permission_error`. Under sustained
`529 overloaded_error` conditions lasting several minutes, the application's own request
queue grows without bound and its worker pool becomes saturated, even though the
downstream API is not the direct cause of the queue growth.

Which change most directly addresses the described operational failure?

A. Increase the retry budget from 8 to 20 attempts so requests eventually succeed once
   the overload clears.
B. Remove retries entirely for every exception type, so all failures return to the caller
   immediately.
C. Differentiate retry logic by exception type (no retries for `authentication_error` /
   `permission_error`), and add a circuit breaker that stops issuing new calls to the API
   for a cooldown period once failures cross a threshold, rather than letting every
   inbound request independently retry against an already-overloaded dependency.
D. Switch to a larger, more capable model, since 529s indicate the requested model
   specifically is overloaded.

---

### Question 6 (Select 1)

A model call succeeds (HTTP 200) and returns a `tool_use` block calling a `send_email`
tool with a `recipient` argument. The recipient address in the tool call does not match
any address that appeared anywhere in the conversation, the tool's parameter description,
or any system prompt content. No exception was raised by the SDK anywhere in this turn.

How should this failure be classified and handled?

A. This cannot be a real failure since no exception was raised — the SDK would have
   raised an error if something were wrong with the response.
B. This is an application-level, model-output issue (a hallucinated tool argument) that
   the SDK will never surface as an exception; it must be caught by application-level
   validation of tool arguments (e.g., checking the recipient against a known-good
   allowlist) before the tool is executed, not by any try/except around the API call.
C. This is an API-level `invalid_request_error` and should be handled with the same
   retry-then-fail-fast logic as a 400 response.
D. This should be treated as a rate-limit condition and retried with backoff, since
   unexpected tool arguments are usually caused by request throttling.

---

## Answer key and rationale

**Q1 — C.**
The scenario describes an *account-level spend cap*, not a transient capacity blip. The
README calls this out specifically: a spend-cap-driven 429 has no `retry-after` and "will
keep failing until access resumes" — mechanically retrying (A, B) wastes request budget
and latency for no benefit, since the condition won't clear on its own timescale. D is
wrong because falling back to a different model doesn't address a spend cap, which applies
at the account level regardless of which model is called; the correct response is to stop
retrying and treat this as a fail-fast condition requiring human/billing action.

**Q2 — A and C.**
"Validate and re-prompt" is the recovery pattern for *application-level, structurally-
inspectable output problems*: a JSON response that's missing a field (A) or that violates
an enum constraint your code enforces (C) are both things you can detect by inspecting the
model's own output and then ask the model to correct. B and D are API-level, HTTP-status
errors — no model output was even produced to validate; B needs a fail-fast credential
fix, and D needs the request payload reduced in size, neither of which "re-prompting the
model to fix its output" addresses.

**Q3 — B.**
The tool was called correctly and returned correct data for the parameters it was given
(ruling out A). The actual defect is that "last quarter" is ambiguous without knowing the
current date, and nothing in the trace establishes that — so the model filled the gap with
an assumption (Q2) that happened to be wrong. Per the diagnostic checklist, when the exact
input the model had was incomplete (missing the information needed to resolve "last
quarter" unambiguously), that is attributable to the integration layer's job of supplying
sufficient context — but the fix is not a schema change (C is too narrow/incorrect: this
isn't a "required parameter" issue, since the assistant filled in a specific quarter value
just fine) — it's supplying necessary grounding information (current date) in context
rather than assuming the model can access wall-clock time on its own. D overstates the
problem — this is a fixable context-completeness issue, not a category of task that's
unsolvable.

**Q4 — B.**
Directly comparing the literal, actually-sent request payload against what should have
been sent — and finding a concrete discrepancy (a dropped/corrupted prior tool result) —
is direct, verifiable evidence of a bug in your own code's data handling. A is actually
evidence pointing toward a *model*-output explanation (per the README's tie-breaker: same
correct input, same wrong output, reproducibly, suggests the model itself, not one-off
data corruption). C is ambiguous on its own — an argument not appearing in visible history
could be a hallucination OR could mean the context was assembled incorrectly; it needs the
payload check to disambiguate, which is exactly what B provides directly. D is not
evidence of anything — a model's stated confidence in its own reasoning is not a reliable
signal of correctness.

**Q5 — C.**
The description matches the textbook cascading-failure scenario the README addresses with
circuit breakers: uniform retries across every exception type (including non-transient
ones like `authentication_error`) waste budget, and — more importantly — under sustained
529s, every inbound request independently retrying against an already-struggling
dependency is exactly what grows the application's own queue and saturates its workers. A
makes the described problem worse (more retries against something already overloaded). B
overcorrects — you'd also lose legitimate recovery from genuinely transient errors. D
misunderstands 529: it signals the API is overloaded generally, not that a specific model
is the wrong choice; switching models doesn't address queue growth in the calling
application.

**Q6 — B.**
This is the central "application-level vs. API-level" distinction the domain tests: the
HTTP call succeeded, so no SDK exception fires — from the transport's point of view,
nothing went wrong. A hallucinated tool argument is invisible to the SDK's error handling
entirely and must be caught by your own validation logic before you act on it (here,
before actually sending an email). A is the classic trap answer — "no exception means no
problem" is precisely the false assumption this module warns against. C and D
mischaracterize what happened: there is no invalid_request_error and no rate-limit
condition here at all; the request/response cycle was entirely successful at the API
level, which is exactly why this failure mode needs its own, separate detection logic.
