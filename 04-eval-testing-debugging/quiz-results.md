# Domain 4 Quiz — My Results (2026-09-02)

Score: 6/6. See `quiz.md` for the original questions and the course's own
answer key/rationale — this file is my personal answer log plus reasoning
for each question.

| Q | My answer | Correct | Result |
|---|-----------|---------|--------|
| 1 | C | C | ✅ |
| 2 | A, C | A, C | ✅ |
| 3 | B | B | ✅ |
| 4 | B | B | ✅ |
| 5 | C | C | ✅ |
| 6 | B | B | ✅ |

---

**Q1 — 429 with no retry-after, 20 minutes of continuous 429s, account
confirmed over its monthly spend cap.** Answered C — correct. This is an
account-level spend cap, not a transient capacity blip — it has no
retry-after because it isn't going to clear on any request-level timescale.
Mechanically retrying (A, B) just wastes request budget and latency for a
condition that only resolves when a human raises/resets the cap. Falling
back to a smaller model (D) doesn't help either, since the spend cap
applies at the account level regardless of which model is called. The
right move is to stop automatic retries and surface this for human/billing
action — a fail-fast condition, not a retryable one, even though 429 is
"usually" the textbook retryable status code. Same underlying lesson as
[../04-eval-testing-debugging/exercises/ex1_error_handling.py](exercises/ex1_error_handling.py):
the exception *type* alone doesn't tell you the recovery strategy — the
actual cause behind it does.

**Q2 — "Validate and re-prompt," pick 2 appropriate uses.** Answered A, C
— correct. A missing required field (A) and a value that doesn't match an
accepted enum (C) are both *structurally-inspectable output problems* — I
can detect them by examining the model's own output, then ask the model to
fix it. A revoked API key (B) and an oversized request body (D) are both
HTTP-status-level failures where no model output was even produced yet —
there's nothing to "validate," and re-prompting the model can't fix a
credential or a payload-size problem. This is the same category boundary
as ex1's dispatcher: match the recovery mechanism to what actually broke,
not to "the model said something."

**Q3 — "Last quarter" resolved to the wrong calendar quarter; tool
returned correct data for the quarter it was actually asked about.**
Answered B — correct. The tool executed faithfully for the parameters it
was given (ruling out A) — this is structurally identical to my own ex2
trace analysis: when the tool_result correctly matches what was actually
requested, the tool/plumbing isn't the culprit. The real gap is that
nothing in the conversation ever established the current date, so "last
quarter" was ambiguous and the model filled the gap with an assumption
that happened to be wrong. The fix is supplying grounding information
(current date) in context, not a schema change (C is too narrow — the
model filled in a specific quarter just fine; there's no missing
parameter) and not giving up on the feature entirely (D overstates a
fixable context-completeness problem as an unsolvable category).

**Q4 — Strongest single check pointing toward an INTEGRATION-layer
explanation (vs. model-output) for a wrong tool-call argument.** Answered
B — correct. Directly diffing the literal request payload actually sent
against what should have been sent, and finding a concrete discrepancy
(e.g. a dropped/corrupted prior tool result), is direct, verifiable
evidence of a bug in your own code's data handling. A is actually evidence
pointing the *other* way — same correct input reproducibly causing the
same wrong output points at the model, not one-off data corruption. C is
ambiguous by itself (could be hallucination OR bad context assembly — it's
exactly the kind of question the payload diff in B is needed to resolve).
D isn't evidence of anything at all; a model sounding confident says
nothing about whether it's right.

**Q5 — Uniform 8-attempt retries on every exception type (including
auth/permission errors), causing unbounded queue growth under sustained
529s.** Answered C — correct. This is the textbook cascading-failure
pattern: retrying non-transient errors (auth/permission) wastes budget for
no possible benefit, and more importantly, every inbound request
independently retrying against an already-overloaded dependency is exactly
what grows the app's own queue and saturates its workers. The fix needs
two parts together: stop retrying exception types that can never
self-resolve, and add a circuit breaker so the app stops hammering an
already-struggling dependency during sustained overload. Raising the retry
budget (A) makes the described problem worse; removing all retries (B)
overcorrects and loses legitimate recovery from genuinely transient
errors; switching models (D) misreads what a 529 means (API-wide overload
signal, not "this specific model is a bad choice").

**Q6 — HTTP 200 success, but the returned tool_use argument (an email
recipient) doesn't appear anywhere in the conversation, tool description,
or system prompt. No SDK exception anywhere.** Answered B — correct. This
is the central application-level vs. API-level distinction this domain
tests: the HTTP call succeeded, so no SDK exception fires — from the
transport's point of view nothing went wrong. A hallucinated tool argument
is invisible to the SDK's error handling entirely; it has to be caught by
application-level validation of the tool's arguments (e.g. checking the
recipient against a known-good allowlist) before the tool actually runs.
A is the classic trap: "no exception means no problem" is precisely the
false assumption this module warns against. C and D both invent an error
condition that didn't actually occur (no invalid_request_error, no
rate-limit signal) — the request/response cycle was entirely successful,
which is exactly why this failure mode needs its own separate detection
layer rather than living inside a try/except around the API call.

---

## Pattern to remember

No misses this time, but the six questions collectively reinforce one
throughline that's now shown up in every quiz and every exercise in this
domain so far: **matching the response to the actual root cause, not to
the surface signal.** A 429 isn't automatically "retry" (Q1) — check
whether it's transient or a hard cap. A wrong output isn't automatically
"the model's fault" (Q3, Q4) — trace the dependency chain and diff the
actual payload before attributing blame. And the *absence* of an exception
isn't automatically "no failure" (Q6) — some failure modes are structurally
invisible to the SDK's own error handling and need their own detection
logic. This is the same instinct I used solving
[ex1_error_handling.py](exercises/ex1_error_handling.py) (different
recovery strategy per exception type, not one uniform try/except) and
[ex2_trace_analysis.py](exercises/ex2_trace_analysis.py) (walking the
dependency chain backward before deciding where the fault lives).
