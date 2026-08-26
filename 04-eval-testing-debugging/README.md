# Module 04 — Eval, Testing, and Debugging

**Blueprint domain:** Domain 4, "Eval, Testing, and Debugging" — 2.6% of the CCDV-F exam.
> **Cost note:** `ex2` (trace analysis) works entirely offline against a pre-written mock
> trace — no live calls needed. `ex1` (error handling) needs at least one real API call to
> observe genuine exception behavior, so it needs a metered Console API key — see
> `00-setup/README.md` section 3.

**Skill covered:** Debugging and Error Handling — error type identification, recovery
strategy selection, trace analysis to identify failure modes, and problem origin isolation
between the integration layer and model output.

This is an unofficial, independently-built self-study module inspired by the published
CCDV-F exam blueprint. It is not written or endorsed by Anthropic, and no practice question
in this module reproduces a real exam item.

A note on weight before you start: 2.6% is one of the smallest domains on the blueprint —
you will not see many questions on it. But don't skip it. Every other domain in this course
assumes you can keep an application running when something goes wrong, and "something went
wrong" is the normal condition of a production LLM integration, not the exception. A
developer who can't tell a rate limit from a malformed-output bug from their own mishandled
response object will misdiagnose real incidents constantly, exam or no exam. Treat this
module as small but load-bearing.

---

## 1. Two very different kinds of "error"

When something goes wrong in a Claude application, the first and most important question is:
**where did it go wrong?** Broadly, failures split into two categories that need completely
different handling.

### 1.1 API-level errors

These are errors the Claude API itself returns to you, as an HTTP status code plus a
structured error body, before your application ever gets to reason about "what did the
model say." The official Python SDK raises a typed exception for each one. As of this
writing, the current error types documented at
[docs.claude.com](https://docs.claude.com) (API reference → Errors) are:

| HTTP status | Error type            | Meaning                                                              |
|-------------|------------------------|-----------------------------------------------------------------------|
| 400         | `invalid_request_error` | Malformed request — bad JSON, invalid parameter, or (notably) a request whose prompt + expected output exceeds the model's context window |
| 401         | `authentication_error`  | Missing, malformed, revoked, or expired API key                      |
| 402         | `billing_error`         | Billing/payment problem on the account                                |
| 403         | `permission_error`      | Key is valid but lacks permission for this resource/model             |
| 404         | `not_found_error`       | Referenced resource (e.g. a batch or file ID) doesn't exist           |
| 409         | `conflict_error`        | Resource conflict, e.g. concurrent modification                       |
| 413         | `request_too_large`     | Request body exceeds the endpoint's maximum size                      |
| 429         | `rate_limit_error`      | You've exceeded a rate limit, spend cap, or usage-tier limit          |
| 500         | `api_error`             | Unexpected error on Anthropic's side                                  |
| 504         | `timeout_error`         | The request timed out                                                 |
| 529         | `overloaded_error`      | The API is temporarily overloaded across all customers                |

The Python SDK maps these onto exception classes deriving from `anthropic.APIError`, roughly:
`AuthenticationError`, `PermissionDeniedError`, `NotFoundError`, `RateLimitError`, and a base
`APIStatusError` (carrying `.status_code` and `.message`) for status-coded HTTP failures,
plus `APIConnectionError` / `APITimeoutError` for problems that never even got a response
from the server (DNS failure, TLS failure, dropped connection, client-side timeout). Exact
class names and hierarchy are an SDK implementation detail and *do* shift between SDK
versions — treat the names above as "current as of this writing, verify against
`docs.claude.com` and the installed `anthropic` package's changelog before an exam or before
writing production code."

A few of these deserve special mention because they're easy to conflate:

- **`invalid_request_error` covers two very different root causes.** Most of the time it
  means you sent something structurally wrong (a bad parameter, an unclosed tool schema).
  But it is *also* what a context-length-exceeded condition looks like: there is no separate
  "context too long" error type — it surfaces as a 400 `invalid_request_error` whose message
  says the prompt is too long for the model. You have to read the message text, not just the
  status code, to tell "my JSON is malformed" apart from "my conversation history grew past
  the context window."
- **`rate_limit_error` (429) and `overloaded_error` (529) are both "try again," but for
  different reasons and on different timescales.** A 429 means *you personally* have used up
  a quota (requests/minute, tokens/minute, or a spend cap) — backing off and retrying your
  own request is the right move, and a spend-cap 429 may have no `retry-after` header and
  will keep failing until the cap resets, so blind retrying can spin forever. A 529 means the
  service as a whole is overloaded — every customer is seeing it, and it often makes sense to
  additionally reduce what you're asking for (smaller model, fewer tokens, deferred work)
  rather than just hammering retries.
- **`request_too_large` (413) vs. context-length exceeded.** 413 is about the raw size of the
  HTTP request body (e.g. huge base64 image payloads) against the endpoint's byte limit,
  which is a different ceiling from the model's token-based context window.

### 1.2 Application-level / model-behavior issues

These are not API errors at all — the HTTP call *succeeded*, you got a well-formed
`200 OK` response back, and the problem is in what the model actually produced (or in what
your code did with it). No exception fires for these; you have to detect them yourself. Common
examples:

- **Malformed structured output** — you asked for JSON (or a specific tool-call schema) and
  got text that doesn't parse, or parses but is missing a required field.
- **Refusals** — the model declines to do what was asked, often for safety reasons, and
  returns explanatory text instead of the expected output shape.
- **Hallucinated tool arguments** — the model calls a real tool correctly by name, but
  invents a parameter value (a file path, an ID, a date) that was never present in the
  conversation.
- **Incomplete tool loops** — in an agentic flow, the model stops before finishing the task:
  it emits a final text answer when it should have made another tool call, or it loops
  calling the same tool without making progress, or it runs past a reasonable step budget.
- **Silently wrong answers** — the model gives a plausible, well-formatted, on-schema answer
  that is simply incorrect given the inputs. This is the hardest category, because nothing
  about the response *looks* broken.

The key mental shift: API-level errors are things the platform tells you about explicitly.
Application-level issues are things you have to check for, because from the transport's
point of view, everything worked.

---

## 2. Recovery strategies

Different failure categories call for different recovery strategies. Picking the wrong one
is itself a common bug (e.g., retrying a 400 `invalid_request_error` five times in a row
does nothing but burn latency — the request was wrong on attempt one and will be wrong on
attempt five).

### 2.1 Retry with exponential backoff and jitter

The right response to a **transient, likely-to-succeed-if-retried** failure:
`rate_limit_error` (429), `overloaded_error` (529), `api_error` (500), `timeout_error` (504),
and connection-level errors (`APIConnectionError`). The pattern:

1. Wait a base delay, then retry.
2. If it fails again, double (or otherwise scale up) the delay — "exponential" backoff — up
   to a capped maximum, and stop after a bounded number of attempts.
3. Add **jitter** — a small random offset added to each delay — so that if many clients (or
   many concurrent requests from your own process) hit the failure at the same moment, they
   don't all retry in lockstep and re-create the exact spike that caused the failure.
4. Honor a `retry-after` header when the response provides one instead of guessing.

The official SDKs already do a bounded version of this automatically (a small number of
retries on connection errors, 429s, and 5xxs, respecting `retry-after`). That default is a
safety net, not a substitute for application-level judgment — you may want a longer retry
budget for a low-priority background job, or a much shorter one (or none) for a
latency-sensitive user-facing request.

**Do not retry** 400/401/402/403/404/409/413 — these are not transient. Retrying an
`authentication_error` a hundred times with the same bad key produces a hundred identical
failures, not eventual success. Fail fast on these and surface the problem (bad
credentials, bad request shape, missing resource) instead.

### 2.2 Fallback: smaller/different model or reduced scope

When retries are exhausted, or when a 529 overload is severe/prolonged, a resilient
application can degrade gracefully instead of failing outright:

- Fall back to a smaller or different model that may have separate capacity.
- Reduce the scope of the request — shorter output (`max_tokens`), a trimmed prompt, or a
  simplified task — to get *something* useful back rather than nothing.
- Serve a cached or default response for non-critical paths.

This is a product decision as much as an engineering one: a degraded-but-present answer is
often better UX than a hard failure, but only if the caller can tell the answer came from a
fallback path (don't silently swap in a much weaker model without any signal).

### 2.3 Validate and re-prompt on malformed output

For application-level issues — bad JSON, a missing required field, a schema violation — the
standard pattern is: **validate the response programmatically, and if it fails validation,
send it back to the model with a description of what was wrong and ask it to correct it**,
rather than treating it as an unrecoverable error. This works because the model is often
capable of producing the right output — it just didn't this time — and showing it the
specific validation failure is usually enough to fix it on the next turn. Bound this loop
(e.g., 2–3 correction attempts) so a persistently uncooperative model doesn't retry forever;
if it still fails after the budget, fail the request explicitly rather than accepting
last-attempt garbage.

Refusals need a related but distinct check: don't just check "did I get a response," check
"is the response the *shape* I expect." A refusal is a perfectly valid, successful API
response that is nonetheless not what your application needs — treat it as an
application-level condition to detect and handle (retry with rephrased instructions,
escalate to a human, or return a clear error to the end user), not as something the SDK will
ever raise for you.

### 2.4 Circuit breakers for cascading failure

A circuit breaker stops calling a dependency once it has failed enough times recently, and
short-circuits new calls to an immediate failure (or fallback) for a cooldown period, instead
of letting every incoming request queue up retries against a service that's already down.
This matters for two reasons:

- It protects *your* system: if every inbound request independently retries 3 times with
  backoff against a downed API, your own request queues and worker pools back up, and you can
  tip yourself into an outage even after the upstream API recovers.
- It protects the *upstream* system: a swarm of retrying clients is exactly what turns a
  brief overload into a prolonged one — this is the same lockstep-retry problem jitter solves
  at the single-request level, applied at the fleet level.

A circuit breaker is the right tool once you have persistent, cross-request failures (the
API has been returning 529s for the last two minutes); backoff-with-jitter is the right tool
for a single request's retry loop. Production systems typically use both together.

### Quick-reference: which strategy for which failure

| Failure                                            | Strategy                                      |
|-----------------------------------------------------|------------------------------------------------|
| 429 rate limit / 529 overloaded / 500 / connection drop | Retry with exponential backoff + jitter; consider fallback if prolonged |
| 401 / 403 / 404 / 400 (bad request shape)           | Fail fast, surface a clear error — retrying won't help |
| 400 (context length exceeded specifically)          | Reduce input (truncate/summarize history), don't blindly retry the same oversized request |
| Malformed structured output / schema violation      | Validate, re-prompt with the specific validation error, bounded attempts |
| Refusal                                              | Detect via content inspection; rephrase, escalate, or surface to the user — not an exception path |
| Hallucinated tool argument                           | Validate tool-call arguments against known-good values *before* executing the tool; reject and re-prompt if invalid |
| Sustained/repeated upstream failures                | Circuit breaker to stop hammering a down dependency |

---

## 3. Trace analysis: reading a multi-step transcript to find where it broke

An agentic Claude application produces a **trace**: an ordered sequence of turns — user
message, assistant message (possibly containing one or more `tool_use` blocks), tool
result(s) fed back in, more assistant reasoning, and so on, until a final answer. When the
final answer is wrong, the trace is your primary debugging artifact. The skill being tested
here is reading that trace turn by turn to find the **first** point where things went off the
rails — not the point where the wrongness became visible (often the final answer), but where
it was introduced.

A practical method:

1. **Start from the final (wrong) output and work backward.** What does the final answer
   depend on? Trace that dependency back through the tool results and assistant turns that
   produced it.
2. **Check each tool call's arguments against the context available at that point in the
   conversation.** Were the arguments the model passed actually justified by what had been
   said/returned so far, or did the model invent/assume a value?
3. **Check each tool result against what the tool call asked for.** Does the returned data
   actually answer the call, or is it an error, an empty result, or data for the wrong
   entity — and if so, did the assistant's next turn notice that, or did it proceed as if the
   result were good?
4. **Identify the first turn where a wrong assumption, a wrong argument, or a misread result
   appears.** Everything downstream of that turn is usually a consistent (even
   "reasonable-looking") continuation of an already-broken state. Fixing only the symptom at
   the end without finding this point means the same bug reappears on the next similar input.

### 3.1 Integration layer vs. model output: how to tell them apart

This is the specific diagnostic skill the blueprint calls out, and it's the crux of this
domain. Once you've localized the failure to a particular step in the trace, you still have
to decide: **is this a bug in code I control (the integration layer), or is this the model
reasoning/responding incorrectly given correct inputs (model output)?** These require
opposite fixes — patching a schema versus adjusting a prompt or accepting a model limitation
— so misattributing one as the other wastes time and can leave the real bug in place.

**Integration-layer failure** — the bug is in your code, the tool implementation, the schema
definition, or how you assembled the request. Signs:

- The tool schema you gave the model doesn't match what the tool implementation actually
  expects or returns (wrong field name, wrong type, an enum value the tool doesn't handle).
- The model's tool call was reasonable and well-formed, but your tool-execution code mishandled
  it — wrong parameter mapping, an off-by-one, a bug in the handler itself.
- The tool result was truncated, mis-serialized, or the wrong payload was fed back into the
  `tool_result` block (e.g., stale data, a copy-paste of the previous turn's result).
- The conversation history sent to the model was incomplete or malformed — a prior turn's
  content got dropped, mis-ordered, or a `tool_use`/`tool_result` pairing was broken.
- The final response was parsed/extracted incorrectly by your code even though the model's
  raw output was fine.

**Model-output failure** — your code and data pipeline are correct; the model was given
correct, complete information and still reasoned or responded incorrectly. Signs:

- The tool call arguments are internally consistent with the schema and are *wrong only in
  the sense that the model invented a value* not present anywhere in the correct, complete
  context it was given (a genuine hallucination, not a data-plumbing bug).
- Given the (verified-correct) tool results, the model drew an unsupported conclusion, missed
  a piece of the provided data, or contradicted information that was plainly present in
  context.
- The model stopped its tool loop prematurely, or looped unproductively, despite having
  everything it needed to know it wasn't done.

**Diagnostic questions to work through, in order:**

1. **Replay the exact request that was sent.** Log (or reconstruct) the literal API request
   payload for the turn in question — not what you *intended* to send, what was *actually*
   sent. Does it contain the correct, complete data the model needed? If the data going in
   was already wrong or missing, the model cannot be at fault for what came out — that's an
   integration-layer bug, full stop.
2. **If the input was correct, check the tool schema against the tool's real behavior.** Does
   the parameter the model got "wrong" even exist as documented in the schema you provided?
   Would a careful human, given only the schema and the conversation so far, have produced a
   different, correct call? If the schema itself invites the mistake (ambiguous field
   description, misleading enum name), that's an integration-layer issue (a schema/prompt
   design problem), even though it manifests as a "bad" model output.
3. **Check whether the tool result was correctly captured and relayed.** Pull the raw tool
   response your code received, and compare it to the `tool_result` content block actually
   sent back to the model on the next turn. If they differ, that's an integration bug
   regardless of anything the model did afterward.
4. **Only once 1–3 are confirmed clean, attribute it to the model.** If the exact input was
   correct, the schema was unambiguous, and the tool result was faithfully relayed, and the
   model still produced a wrong argument, a wrong conclusion, or an incomplete loop — that is
   a genuine model-output issue. The fix now lives in prompt/instructions (be more explicit,
   add an example, add a validation step the model itself is asked to perform) or in
   accepting a known limitation and adding an external guardrail (e.g., validate tool
   arguments in code before executing them, regardless of how well-prompted the model is).
5. **A useful tie-breaker: is the failure reproducible with the same corrected input?** Re-run
   the same turn with a manually verified-correct, complete input. If the model now succeeds,
   the original failure was very likely caused by bad input reaching the model (integration
   layer). If the model fails again on demonstrably correct input, it's a model-output issue.

A common trap: it's tempting to default to "the model got it wrong" because that's the least
work to conclude — but in practice a large share of real-world "the model is hallucinating"
reports turn out, on inspection of the actual request payload, to be the integration layer
feeding the model incomplete, stale, or malformed context. Always check step 1 before
concluding anything about the model's reasoning.

---

## 4. Check the current docs

Error type names, exception class hierarchies, default retry counts, and status codes are
API/SDK surface area that changes over time. Before an exam attempt or before writing
production error-handling code, check the current reference at
[docs.claude.com](https://docs.claude.com) (API reference → Errors, and the SDK's own
release notes) rather than trusting this README's table as permanently current — it reflects
what was documented as of when this module was written.
