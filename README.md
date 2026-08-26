# Claude Certified Developer – Foundations: Hands-On Study Course

An unofficial, self-built study course covering the full exam blueprint for the **Claude Certified Developer – Foundations** certification (exam code `CCDV-F`, blueprint version 1.0, effective July 2026). It is not produced or endorsed by Anthropic, does not reproduce real exam questions, and does not guarantee a passing result — per the exam guide itself, there is no single required course and no resource guarantees a pass. Treat this as a structured way to combine reading with hands-on practice, and always cross-check fast-moving specifics (model names, pricing, SDK method signatures, CLI flags) against the current docs at **docs.claude.com** and pricing at **anthropic.com/pricing**, since the platform evolves quickly and this content was written against the author's best knowledge, not live documentation.

## Exam basics (from the official exam guide)

| | |
|---|---|
| Credential | Claude Certified Developer – Foundations |
| Exam code | CCDV-F |
| Items | 53 (multiple-choice and multiple-response; each item states how many responses to select) |
| Time limit | 120 minutes |
| Delivery | Proctored — online or Pearson VUE test center |
| Passing score | Scaled score of 720, on a 100–1,000 scale |
| Exam fee | $125 USD |
| Validity | 12 months from the date the credential is awarded |
| Recommended background | 1–5 years software engineering experience, 6+ months hands-on with Claude or a comparable LLM system, proficiency in Python and/or TypeScript, fluency with REST APIs and CLI tools |

There are no mandatory prerequisites — the credential is awarded on exam performance alone. The recommended background above is exactly what this course assumes and builds on.

## How this course is organized

Each numbered folder is one exam domain, weighted to match the official blueprint. Inside every domain folder you'll find the same four pieces:

- **`README.md`** — the concepts for that domain, written as study material, mapped explicitly to each blueprint skill and its weight.
- **`exercises/`** — hands-on exercises with TODOs. Most are runnable Python scripts against the real `anthropic` SDK; a few (requirements analysis, config file design, tool-vs-MCP decisions) are written/design exercises since that's what the underlying skill actually tests.
- **`solutions/`** — fully worked reference versions of every exercise, with comments explaining the reasoning, not just the code.
- **`quiz.md`** — original, exam-style practice questions (scenario-based, each stating how many responses to select) with a full answer key and rationale, in the same spirit as the sample questions in Section 8 of the official exam guide. These are illustrative practice questions the author wrote to mirror the blueprint — not real exam items.

| Domain | Weight | Folder | Exercises |
|---|---|---|---|
| 0 — Environment setup | — | `00-setup/` | 1 (get an API key, install SDK, verify) |
| 1 — Agents and Workflows | 14.7% | `01-agents-and-workflows/` | 3 |
| 2 — Applications and Integration | 33.1% | `02-applications-and-integration/` | 6 |
| 3 — Claude Code | 3.1% | `03-claude-code/` | 2 |
| 4 — Eval, Testing, and Debugging | 2.6% | `04-eval-testing-debugging/` | 2 |
| 5 — Model Selection and Optimization | 16.8% | `05-model-selection-optimization/` | 4 |
| 6 — Prompt and Context Engineering | 11.0% | `06-prompt-context-engineering/` | 3 |
| 7 — Security and Safety | 8.1% | `07-security-safety/` | 3 |
| 8 — Tools and MCPs | 10.6% | `08-tools-and-mcps/` | 3 |
| Practice exam | 100% | `09-practice-exam/` | 1 full mixed exam |

Domain 2 and Domain 5 carry the most exam weight (almost half the exam between them) and get proportionally more exercises. Domains 3 and 4 are small, focused domains with lighter but still complete coverage.

## Do you actually need a metered API key?

Not entirely, if you have a paid Claude.ai subscription (Pro, Max, Team, or Enterprise) —
Knowit's Team/Enterprise seat qualifies. Claude Code and the Claude Agent SDK can
authenticate directly against that subscription (via `claude setup-token`), at no marginal
cost beyond what Knowit already pays. **Domain 3 (all of it), Domain 1 (`ex1`, `ex3`), and
Domain 8 (all of it) are already built this way** — they run on the Claude Agent SDK or
Claude Code under subscription auth, no metered key needed. What's left genuinely needs a
metered key from `platform.claude.com`, because those exercises are deliberately teaching
raw Messages-API-level mechanics (streaming, vision, prompt caching, the batch API, real
token/cost measurement, Domain 1's `ex2` hand-rolled tool-use loop) that no subscription
product exposes — realistic total cost for all of that together is well under a dollar if
you use the cheapest model tier and set a spend cap. **`00-setup/README.md` has the full
breakdown, including a table of exactly which exercises need which path** — read it before
doing anything else.

## Recommended order

1. **Start with `00-setup/`.** Follow that folder's `README.md` — it covers both the free
   subscription path and the metered API key path, and which exercises in this course need
   which. Several exercises genuinely need a live call; the rest can still be read and
   reasoned through without one, but you'll get much more out of actually running things.
2. **Work through the domains roughly in blueprint order (1 → 8)**, but feel free to reorder — Domain 5 (Model Selection) and Domain 6 (Prompt/Context Engineering) are useful earlier since later domains lean on those concepts. For each domain: read the `README.md` first, do the exercises (attempt before peeking at `solutions/`), then take the domain `quiz.md` and review every rationale, right or wrong answer.
3. **Finish with `09-practice-exam/`** — a single 53-item mixed practice exam weighted the same way as the real blueprint, timed to 120 minutes, to rehearse the actual exam experience before you schedule it.

## Suggested self-paced schedule

A reasonable pace for someone working through this alongside a job is roughly 2–3 weeks, evenings/weekends. Adjust freely — there's no fixed timeline requirement for the real exam.

- **Days 1–2:** `00-setup/`, Domain 1 (Agents and Workflows), Domain 5 (Model Selection and Optimization) — these are foundational to everything after.
- **Days 3–6:** Domain 2 (Applications and Integration) — it's a third of the exam, budget real time here.
- **Days 7–8:** Domain 6 (Prompt and Context Engineering).
- **Days 9–10:** Domain 8 (Tools and MCPs).
- **Day 11:** Domain 3 (Claude Code) and Domain 4 (Eval, Testing, Debugging) — both small, can be combined in one session.
- **Day 12:** Domain 7 (Security and Safety).
- **Day 13:** Re-take every domain `quiz.md` cold (no notes), and re-read the `README.md` for any domain where you missed more than one question.
- **Day 14 (or whenever you feel ready):** `09-practice-exam/`, timed. Review every wrong answer before scheduling the real exam.

## What "hands-on" means when you don't have a key yet

Every exercise docstring/instructions file says explicitly whether it needs a live API call. Where it does, you can still: read the exercise, write the code, and predict what the output should be — then come back and actually run it once `00-setup/` is done. Don't skip the API-based exercises entirely; a large share of the real exam (Domain 2 alone is 33.1%) is about API mechanics that are much easier to internalize by actually seeing request/response shapes than by reading about them.

## Registration, scoring, and exam-day policy (quick reference)

This course covers exam *content*. For the logistics — registering through the Anthropic Partner Academy and Pearson VUE, ID requirements, accommodations, the retake policy (14/30/90-day waiting periods, up to four attempts in a rolling 12 months), rules of conduct during the exam, and the confidentiality agreement — refer back to Sections 9–15 of the official exam guide PDF you already have. Nothing in this course substitutes for reading that document in full before scheduling.

## A note on integrity

The quizzes and practice exam here are original questions written to match the *style and cognitive level* described in the official guide's sample questions — they are not real exam items and were not derived from any confidential exam content. Studying with them is fair practice; if you ever come across a resource claiming to be actual leaked exam questions, avoid it — using such material violates the exam's confidentiality agreement (Section 13) and puts your credential at risk.

Good luck.
