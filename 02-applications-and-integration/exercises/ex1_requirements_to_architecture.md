# Exercise 1 — Requirements to Architecture (written exercise)

**Skills covered:** Understanding Requirements, Systems Life Cycle, Claude API Mechanics
(applied at a design level)

No API key needed for this one — it's a written/reasoning exercise. Grab a blank doc or
just edit this file in place.

## The scenario

Read this short business scenario, then complete the three tasks below.

> A mid-size B2B software company runs a support team that fields questions from customers
> across ~40 different client organizations ("tenants"). Support agents currently search a
> 200-page internal policy PDF by hand to answer procedural questions ("what's our refund
> policy for enterprise plan cancellations mid-term?", "what's the SLA credit process for a
> P1 outage?"). This takes agents several minutes per question and answers are sometimes
> inconsistent between agents.
>
> The team wants an internal tool where an agent types a question and gets a fast,
> accurate answer sourced from the policy document. Critical constraint: some of the
> policy document's content differs by tenant tier (e.g., enterprise vs. mid-market
> contracts have different SLA terms), and the tool must **never** let an answer intended
> for one tenant's context leak into an answer for a different tenant. Agents need
> responses in under 5 seconds to keep using it during live chats. The company has no
> hard compliance mandate today but expects to pursue SOC 2 within the next year, so
> data-handling choices made now should not paint them into a corner later.

## Task 1 — Functional requirements

Write 5-8 functional requirements: what must the system do, described in terms a support
team lead (non-engineer) could read and verify. Cover at minimum: input, output, the
tenant-isolation behavior, and what the tool should do when the policy document doesn't
answer a question (should it guess, or say so?).

*(Write your answers here.)*

1.
2.
3.

## Task 2 — Infrastructure (non-functional) requirements

Write 5-8 infrastructure requirements. Cover at minimum: latency, cost/volume
expectations, tenant-data isolation as an *infrastructure* concern (not just a functional
behavior — think about where/how data is stored and accessed), and forward-compatibility
with an eventual SOC 2 push.

*(Write your answers here.)*

1.
2.
3.

## Task 3 — Solution sketch

In a few short paragraphs (or bullet points), sketch a solution and justify it by pointing
back to specific requirements from Tasks 1 and 2. Answer at least these questions:

- Would you use a realtime call, streaming, batch, or some combination? Why, given the
  5-second requirement?
- How would you get the 200-page policy document's content into context for a given
  question — send the whole document on every call, or something else? Would prompt
  caching matter here, and why?
- How would you technically enforce that a question from a mid-market agent never surfaces
  enterprise-tier-only policy content (and vice versa)? Think about this at the level of
  what goes into the prompt/context per request, not just "we'll tell Claude not to mix
  them up."
- Which SDLC stage(s) (plan/design/build/test/deploy/operate/maintain) would you expect
  the SOC-2-readiness concern to actually get addressed in, and what would you do at that
  stage?

*(Write your answer here.)*

## How to know you succeeded

There's no single correct answer, but a strong response should:

- Keep functional and infrastructure requirements clearly separated (a common mistake is
  writing "must be fast" as a functional requirement — that's infrastructure).
- Explicitly name the tenant-isolation mechanism at the architecture level (e.g., "never
  concatenate more than one tenant's policy excerpts into a single prompt" / "scope
  retrieval to the requesting agent's tenant before constructing the prompt") rather than
  relying on an instruction to Claude alone to prevent leakage.
- Justify the streaming vs. batch vs. realtime choice using the 5-second latency
  requirement specifically, not just asserted without reference to a requirement.
- Note that caching pays off here only if the *same* static content (e.g., a per-tier
  excerpt or the shared portion of the policy doc) is reused across many requests — if
  you'd cache the whole 200-page document with per-tenant content mixed in, that's a red
  flag worth catching yourself on.
- Connect the SOC 2 mention to a concrete forward-looking choice (e.g., logging/retention
  decisions made now, or documenting data flow) rather than ignoring it because it's "not
  required yet."

Check your answer against `solutions/sol1_requirements_to_architecture.md` when done.
