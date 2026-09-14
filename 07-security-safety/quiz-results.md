# Domain 7 Quiz — My Results (2026-09-14)

Score: 8/8. See `quiz.md` for the original questions and the course's own
answer key/rationale — this file is my personal answer log plus reasoning
for each question.

| Q | My answer | Correct | Result |
|---|-----------|---------|--------|
| 1 | B | B | ✅ |
| 2 | B, C | B, C | ✅ |
| 3 | B | B | ✅ |
| 4 | B | B | ✅ |
| 5 | A, C | A, C | ✅ |
| 6 | C | C | ✅ |
| 7 | A, B, D | A, B, D | ✅ |
| 8 | A, C | A, C | ✅ |

---

**Q1 — Hidden instruction buried in a fetched support email, telling the
agent to forward account data externally.** Answered B (prompt injection)
— correct. The attack arrives via untrusted third-party content the model
merely processes (the email), not from the direct user of the chat
interface — that's the defining line between injection and jailbreak. A
misattributes it as a jailbreak; C and D invent unrelated attack
categories with nothing in the scenario supporting them. This is the
exact scenario
[ex1_prompt_injection_defense.py](exercises/ex1_prompt_injection_defense.py)
builds a real defense against — a fetched page containing a fake "SYSTEM
OVERRIDE" instruction, structurally identical to this quiz scenario's
buried email instruction.

**Q2 — Effective mitigations for Q1's attack.** Answered B, C — correct.
Least-privilege tool scoping (B) bounds damage even if the injected
instruction partially succeeds — an allowlisted-recipients-only forward
tool makes the injected forwarding instruction a no-op regardless of
whether the model "believes" it. Explicit delimiting + telling the model
fetched content is data, not commands (C), is the other core mitigation —
exactly what ex1's `SYSTEM_PROMPT` and `<fetched_content>` tags implement,
verified for real against a live model. A is the trap: relying on a
single system-prompt defense alone is explicitly the weakest layer, not a
sufficient one. D (more `max_tokens`) has no relationship to injection
defense at all.

**Q3 — A user directly asks the model to role-play as "DAN" with no
restrictions to bypass payment verification.** Answered B (jailbreak) —
correct. The direct user is speaking to the model themselves, trying to
get the model itself to step outside its safety training via role-play
framing — no third-party untrusted content is involved, which is exactly
what rules out A (injection). C and D invent conclusions (layering
already failed; an auth failure) with no support in the scenario as
described.

**Q4 — System-prompt wording is the ONLY defense; no classifier, no
tool-permission boundary, no human review.** Answered B (guardrail
layering / defense in depth) — correct. This is a textbook single point
of failure with none of the other independent layers present. A (privacy
by design) concerns personal-data handling, not jailbreak resistance; C
(IAM) concerns identity/permission mapping; D (least privilege) concerns
scoping access specifically, not the broader absence of multiple
independent defense layers.

**Q5 — Using Claude Hooks as a safety mechanism for an unrestricted
delete_file tool.** Answered A, C — correct. Both describe the same real
mechanism from the right angle: a deterministic, pre-execution check
against a fixed policy (an allowlisted/normalized directory), independent
of the model's own confidence. B is the exact anti-pattern the module
warns against (trusting the model's own judgment as the primary
safeguard for a destructive action) — precisely the anti-pattern
[ex2_guardrail_hook.py](exercises/ex2_guardrail_hook.py) exists to
replace with `guardrail_hook()`. D doesn't add any policy-based check; it
just breaks the tool's functionality.

**Q6 — Strongest reason a pre-tool-use hook is an effective guardrail.**
Answered C — correct. A hook's value is that it's deterministic and
external to the model's own reasoning, so it evaluates a proposed action
identically regardless of *why* the model proposed it — mistake,
misunderstanding, or a successful upstream injection. I verified this
concretely in ex2:
`guardrail_hook()` blocked both a `..`-traversal path AND a
sibling-directory trap (`/workspace/project-evil`) the same way, with zero
dependency on how the call was framed. A treats speed as the relevant
property (it isn't); B overstates hooks as a replacement for
least-privilege scoping rather than a complement to it; D invents a
retraining behavior hooks don't have.

**Q7 — Reviewing a hardcoded API key in a PR, pick 3 real problems.**
Answered A, B, D — correct. A hardcoded key is permanently recoverable
from version control history the moment it's committed (A); nothing
indicates per-environment scoping, so the same key could span
dev/staging/prod (B); and even though this one line doesn't itself log
the key, hardcoding it removes any structural barrier to it being logged
or exposed elsewhere later (D). C and E are both fabricated SDK claims —
passing `api_key` to the `Anthropic()` constructor is normal, correct,
documented usage; the problem is the literal value, not the constructor
argument. This maps directly onto the mistakes I catalogued in
[ex3_secrets_and_key_hygiene.py](exercises/ex3_secrets_and_key_hygiene.py)'s
`bad_get_client()` teardown.

**Q8 — An authenticated but low-privilege intern's request exposed
another department's confidential data.** Answered A, C — correct. This
is an authorization failure specifically (A): authentication worked
(the system correctly knew who the intern was), but nothing checked
whether that identity's role permitted the specific tool/data access —
which is exactly what "missing access-level verification / RBAC in front
of the sensitive tool" (C) describes as the concrete fix. B is wrong
(nothing about the system being unreachable — if anything it was too
reachable); D reaches for an unsupported injection explanation when an
authorization gap fully explains the incident on its own.

---

## Pattern to remember

No misses this time, but the eight questions collectively reinforce the
same distinctions the three exercises were built to make concrete rather
than abstract:

- **Injection vs. jailbreak** turns on *where the attacking content comes
  from* (third-party data the model processes, vs. the direct user
  themselves) — Q1 and Q3 are mirror-image tests of exactly this line.
- **A single defense layer, however well-worded, is explicitly the wrong
  answer whenever it appears as an option** (Q2's option A, Q4's whole
  premise) — the module's actual position is layering, not "find the one
  good instruction."
- **A hook's entire value proposition is independence from the model's
  reasoning** (Q5, Q6) — not speed, not replacing other layers, not
  retraining anything. This is the same property that made ex2's
  `guardrail_hook()` block the sibling-directory trap regardless of how
  confidently a model might have argued the deletion was safe.
- **Authorization and authentication are different failures with different
  fixes** (Q8) — knowing *who* someone is (authentication) doesn't imply
  the system checked *what they're allowed to do* (authorization/RBAC),
  and confusing the two is an easy way to misdiagnose an access-control
  incident.

Every one of these distinctions had a concrete, tested counterpart in
ex1-ex3, not just a README paragraph — which is likely why this quiz went
cleanly: the reasoning wasn't recalled from memory, it was re-derived from
having built and broken each mechanism directly.
