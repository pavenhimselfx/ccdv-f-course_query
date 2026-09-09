# Domain 6 Quiz — My Results (2026-09-09)

Score: 7/8. See `quiz.md` for the original questions and the course's own
answer key/rationale — this file is my personal answer log plus reasoning
for each question, including why the one miss was wrong.

| Q | My answer | Correct | Result |
|---|-----------|---------|--------|
| 1 | B | B | ✅ |
| 2 | A, B | A, B | ✅ |
| 3 | C | C | ✅ |
| 4 | B | B | ✅ |
| 5 | A, B | A, B | ✅ |
| 6 | B | B | ✅ |
| 7 | B, C | A, B | ❌ |
| 8 | B | B | ✅ |

---

**Q1 — Coding agent's suggestions degrade in the second half of a long
session, before any context-length error.** Answered B (context
drift/bloat) — correct. The scenario explicitly rules out A (overflow)
by stating this happens *before* any length error — quality degrades from
a long, cluttered transcript full of stale/low-value content, not from
content being dropped. C and D invent unrelated causes (throttling, a
model-version quirk) with nothing in the scenario supporting them. This is
exactly what
[ex1_context_pruning_and_compaction.py](exercises/ex1_context_pruning_and_compaction.py)
exists to prevent — pruning/compaction keep the transcript from becoming
the kind of clutter this question describes.

**Q2 — Comparing per-item truncation vs. periodic multi-turn
summarization.** Answered A, B — correct. (a) is pruning: a targeted,
per-item shrink that doesn't change entry count. (b) is compaction: a
periodic, wholesale collapse of a span of turns into one summary, which
DOES reduce entry count. C wrongly claims they're the same operation
(they're complementary, used together — exactly how ex1's
`run_managed_session` combines them every turn plus every 4th turn). D
wrongly claims compaction is lossless — `naive_summarize()` in ex1 was
deliberately, demonstrably lossy (keeps only turn/role/char-count, no
actual content).

**Q3 — Manager doing all research itself vs. dispatching isolated
subagents per question.** Answered C — correct. Subagent isolation keeps
each subagent's context minimal and on-topic (free of the other
questions' exploration/dead ends), and the manager's own context only
grows by each distilled result, not the full working transcript of all
three investigations. A is unsupported (cost tracks total work, not the
pattern itself); B overstates the benefit (isolation isn't a correctness
guarantee); D is false — the manager still has to synthesize the three
distilled answers into one report. This is Domain 1's manager/subagent
pattern applied as a context-engineering technique specifically.

**Q4 — Nearly-empty system prompt, full task instructions repeated every
user turn.** Answered B — correct. Standing, task-invariant rules (topic
scope, policy, length limit, fallback behavior) belong in the system
prompt precisely because they should hold on every turn — repeating them
per-turn is fragile (easy for a future developer to omit) and wastes the
user turn's content on boilerplate instead of the actual question. A
denies that placement matters at all (false); C and D misdiagnose the
problem as "too much system prompt" when the real issue is the system
prompt is nearly empty and missing exactly the content that belongs there.

**Q5 — Untrusted web content inserted into a prompt with no delimiters,
containing an embedded "SYSTEM OVERRIDE" injection attempt.** Answered A,
B — correct. Delimiting untrusted content clearly (and telling Claude it's
data, not instructions) plus bounding/treating it as untrusted input are
both direct input-sanitization responses to a prompt-injection risk. C is
irrelevant (more output room doesn't address untrusted instructions being
followed). D is actively counterproductive — moving attacker-influenced
content into the system prompt would give it MORE authority, the opposite
of the fix.

**Q6 — Prompted-JSON extraction vs. forced tool-use for a billing
pipeline with no human review.** Answered B — correct. Forcing a tool call
declares the schema structurally as part of the tool's `input_schema`,
enforced as part of how the model must respond — rather than merely
described in a prompt that free-text output may or may not actually
match. A understates Design 2's real structural advantage; C treats
latency as the relevant axis when reliability is what's being asked
about; D is the trap answer — schema-enforced structure still doesn't
guarantee the *values* are correct/sane, which is exactly what
[ex3_structured_output_validation.py](exercises/ex3_structured_output_validation.py)
demonstrated directly: `TICKET_TOOL` reliably produced the right field
names, but `validate_ticket_info()` was still a separate, necessary step
that caught real problems in the mock tests.

**Q7 — Defensive-parsing code with no error handling and no field
validation before a DB write.** Answered B, C. B is correct — no
validation that `status` is an allowed enum value or `amount` is numeric
before writing to the database, so a hallucinated/malformed value would
be written through unchecked. **C is wrong** — replacing `json.loads`
with `eval()` is a serious anti-pattern (never execute model output as
code), not a fix at all. Correct: **A** — there's no error handling around
`json.loads` itself; a `JSONDecodeError` from malformed or truncated
output (e.g. cut off at `max_tokens`) would crash unhandled rather than
being caught. I tested exactly this failure mode for real in ex3: the
`TRUNCATED_JSON_STRING` test case confirms `json.loads` raises
`JSONDecodeError` on cut-off output, and the exercise's own
`run_validation_tests()` treats catching that as a distinct, required
check from field-level validation — I had the right mental model in ex3
but picked the wrong option for the same concept here.

**Q8 — Claude states a confident, instant, wrong revenue figure from an
earlier document.** Answered B — correct. Fluency/confidence of phrasing
carries zero evidentiary weight toward correctness; for a high-stakes,
checkable numeric claim, the right response is verifying against the
source (or a secondary check) before treating it as fact. A directly
contradicts the principle being tested; C overreaches from one wrong
answer to "the model is broken"; D overcorrects into blanket distrust
rather than proportional, targeted verification.

---

## Pattern to remember

The one miss (Q7) is a variant of a trap seen before, but inverted: rather
than picking a confidently-wrong absolute claim, I picked a **fabricated
"fix"** (replace `json.loads` with `eval()`) that sounds like it addresses
robustness but is actually a well-known anti-pattern, while missing the
option that named the actual, boring gap (no error handling around
parsing). General tell for this exam: when an answer proposes a
*dramatic* technical change ("replace X with Y") to fix a *narrow*,
specific problem (a missing try/except), be suspicious — the real fix is
usually the narrow, boring one that directly targets the stated gap, not
a wholesale swap.

This also connects across domains: the *concept* tested here (catch
`JSONDecodeError` from malformed/truncated output) is something I
implemented and verified for real in
[ex3_structured_output_validation.py](exercises/ex3_structured_output_validation.py)'s
`TRUNCATED_JSON_STRING` test — I clearly understood the mechanism when
building it, but didn't map it back correctly when it appeared as a quiz
distractor. Worth remembering: recognizing a concept in code you wrote
doesn't automatically transfer to spotting the same concept dressed up in
a different quiz scenario — cross-check against what you actually built,
not just against a general impression of "this sounds familiar."
