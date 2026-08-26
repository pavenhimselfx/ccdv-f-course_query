# Solution 1 — Requirements to Architecture

This is a reference answer for `exercises/ex1_requirements_to_architecture.md`. There's no
single correct answer to a requirements-writing exercise -- judge your own answer against
the "how to know you succeeded" checklist in the exercise file, and use this as one
reasonable example, not a strict rubric.

## Task 1 — Functional requirements

1. An agent can submit a free-text question about company policy and receive a text
   answer, sourced from the internal policy PDF.
2. The tool answers only using content from the policy document -- it must not fabricate
   a policy that doesn't appear in the source document.
3. If the document doesn't contain information relevant to the question, the tool says so
   explicitly rather than guessing or answering from general knowledge.
4. Every answer is scoped to the tenant tier of the customer the agent is currently
   helping -- an agent helping a mid-market customer never sees enterprise-tier-only
   policy content in the answer (or vice versa).
5. The agent can see which section/passage of the policy document an answer was drawn
   from (a citation or excerpt), so they can verify it before repeating it to a customer.
6. The tool is usable mid-conversation, i.e. an agent can ask a question, get an answer,
   and immediately ask a follow-up without restarting.

## Task 2 — Infrastructure requirements

1. End-to-end response latency (question submitted to answer fully visible) must be under
   5 seconds for the common case.
2. The system must guarantee that no single request's context ever contains policy
   content from more than one tenant tier at once -- this needs to be true structurally
   (at the level of what's constructed into the prompt), not just requested via
   instruction.
3. Expected volume: on the order of a support team's concurrent agent count (tens of
   concurrent users, not thousands) -- sized enough to inform whether realtime,
   non-batch calls are appropriate (they are, at this volume).
4. Cost should scale sub-linearly with query volume where possible, given the same policy
   document content is queried repeatedly across many questions and many agents.
5. Data-handling and logging decisions must be made with SOC 2 in mind now: minimize
   retention of full question/answer content beyond what's operationally necessary, and
   keep an auditable record of what document version/content informed a given answer.
6. The system should degrade gracefully on API errors/rate limits -- an agent should see
   a clear "try again" state, not a silent failure or a stale/incorrect answer presented
   as current.

## Task 3 — Solution sketch

**Realtime + streaming, not batch.** The 5-second, mid-conversation requirement rules out
batch entirely -- batch is for workloads where nothing is waiting synchronously, and here
an agent is actively waiting on an answer to relay to a customer. Streaming is worth using
specifically because it makes the *perceived* latency lower: the agent sees the first
words of the answer well under a second in, even if the full answer takes a couple of
seconds to finish generating, which meaningfully helps against a hard 5-second ceiling.

**Don't send the whole 200-page document on every call.** Sending the entire document as
context on every question is both slow (more input tokens to process) and it's the wrong
shape for the tenant-isolation requirement -- if the whole document (all tiers mixed
together) is in every prompt, isolation depends entirely on the model choosing not to
mention the wrong tier's content, which is not a structural guarantee. Instead: split the
document into a shared/common section plus tier-specific sections at ingestion time, and
at request time construct the prompt from only (a) the shared section and (b) the specific
tier section matching the requesting agent's current customer -- never both tiers'
sections in the same request. A retrieval step (even simple keyword or embedding-based
retrieval over pre-split sections) narrows this further to just the passages relevant to
the question, which also helps latency.

**Caching does help, but only on the shared/common portion.** The shared policy content
(and, within a given tier, that tier's own section) is static and reused across many
questions from many agents throughout the day -- that's exactly the profile where prompt
caching pays off: mark the shared block and the per-tier block with `cache_control`, and
frequent agent traffic within the cache's lifetime turns most of that context into cheap,
fast cache reads instead of full input processing on every call. What must *not* happen is
caching a prefix that mixes both tiers' content together "for convenience" -- that would
reintroduce the leakage risk this whole design is trying to avoid, so the per-tier
boundary has to be respected in the caching structure too, not just the plain-text
prompt-construction structure.

**Tenant isolation, concretely:** enforce it at the *retrieval/prompt-construction* layer,
before anything reaches Claude -- the code path that assembles a request must look up the
requesting agent's active customer's tier first, and only pull document sections tagged
for that tier (plus shared sections). This makes isolation a property of what data is
technically reachable per request, not a behavior Claude is merely asked to maintain via
instruction -- an instruction alone is not a reliable enforcement mechanism for a hard
"never leak" requirement.

**SOC 2 readiness and SDLC stage:** this belongs in the **design** stage now, not deferred
to "operate" later. Concretely: design the logging/retention approach (e.g., log which
document section IDs informed an answer, not necessarily the full raw answer text
long-term), and document the data flow (what's sent to Claude, where it's stored, who can
access logs) while the system is being designed, so that pursuing SOC 2 later is a
certification/audit exercise against an already-reasonable design, rather than a rebuild.
Revisiting this again explicitly at the **maintain** stage (as retention/audit
requirements firm up ahead of the actual SOC 2 push) is also reasonable to call out.
