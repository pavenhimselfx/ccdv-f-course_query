# Exercise 3: Built-in Tool vs. Custom Tool vs. Skill vs. MCP — Decision Exercise

Domain 8 (Tools and MCPs) — Skill: Agentic Customization (4.1%)

## Instructions

For each scenario below, decide which ONE of the four mechanisms is the
**best-fit primary choice**:

- **Built-in tool** — pre-built and hosted by Anthropic, you just enable/configure it
- **Custom tool** — you define the schema and write the execution code, running in your own application
- **Skill** — a packaged, reusable instruction/procedure set Claude follows
- **MCP (server)** — a standalone server exposing tools/resources/prompts over the Model Context Protocol, reusable across multiple client applications

Write 3–5 sentences per scenario:

1. Name your choice.
2. Justify it using the decision framework from README.md section 3.2 (work
   through the "does a built-in tool cover this," "is this a procedure vs.
   a new external system," "single app vs. reused across apps" questions).
3. Name the runner-up option you rejected and say, specifically, why it's
   worse for *this* scenario (not worse in general — every one of these
   four mechanisms is the right answer in some scenario).

There is a reference answer in `solutions/ex3_tools_vs_skills_vs_mcp_decision.md`,
but these are judgment calls with real nuance — a well-reasoned answer that
differs from the solution in a minor way (e.g. you'd add a second
mechanism as a complement) is not automatically "wrong." What matters is
whether your reasoning correctly applies the framework's questions to the
scenario's actual constraints.

---

## Scenario 1

Your company runs five separate internal Claude-powered applications (a
support-ticket triage bot, an internal analytics assistant used by the data
team, a Slack-based Q&A bot, an onboarding assistant, and a sales-enablement
tool). All five need the ability to look up and update customer records in
the company's internal CRM. A platform/infrastructure team already owns the
CRM's authentication and query logic, and different application teams
building on top of the CRM should not each have to re-implement that
integration.

**Your choice:** MCP server

**Justification (3–5 sentences):** This is decision point 4 almost exactly
as written: the capability needs to be reusable and independently
maintained across five separate Claude applications, not owned by any one
of them. Building it once as an MCP server wrapping the CRM's
authentication and query logic lets the platform team own and evolve that
integration in one place, while each of the five app teams just connects
to it as a client — list tools, call a tool, done. That also matches who
actually owns the logic: the platform team, not any individual app team,
which is exactly the kind of centrally-owned, cross-application capability
MCP exists for.

**Runner-up rejected, and why:** Custom tool. It's technically capable of
doing the CRM lookup/update logic, but a custom tool lives inside one
application's own code — with five separate applications needing the same
integration, "custom tool" would mean either duplicating the CRM
auth/query logic five times (five copies to patch every time the CRM API
or auth scheme changes) or awkwardly trying to share a library across five
codebases that may not even share a language or deployment target. That's
exactly the duplicated-maintenance-burden failure mode the framework
warns MCP is meant to avoid.

---

## Scenario 2

A single internal reporting app needs to convert a raw dollar amount plus a
currency code into a formatted display string (e.g. `1234.5, "USD"` →
`"$1,234.50"`), using a small, fixed set of formatting rules specific to
this one app's UI conventions. No other application needs this, and it
will never be more complex than string formatting based on a lookup table
of currency symbols and decimal conventions.

**Your choice:** Custom tool

**Justification (3–5 sentences):** No built-in/hosted tool covers
app-specific currency formatting, so step 1 is a quick no. It's not a
Skill either: a Skill packages a *procedure* Claude follows using tools it
already has, but this is actual computation (a lookup table plus string
formatting) that needs to run and return a concrete result — there's
nothing for Claude to "reason through," just a deterministic function to
call. That leaves custom tool vs. MCP, and decision point 3 settles it:
this is bespoke logic, tightly coupled to one app's own UI conventions,
used by exactly one application. Define it in the app, execute it in the
app, done.

**Runner-up rejected, and why:** MCP server. Nothing here needs to be
reusable across applications or independently maintained — the scenario
says explicitly that no other application needs this and it will never
grow more complex. Standing up a server process, a transport, and a
maintenance surface for what's genuinely a five-line lookup-table function
is exactly the over-engineering the framework warns against: paying
protocol and deployment overhead for zero actual reuse benefit.

---

## Scenario 3

Your support team has a seven-step review checklist they follow whenever a
customer requests account deletion (verify identity, check for open
disputes, check for outstanding balance, confirm legal retention
requirements, etc.). They want Claude, when handling one of these requests
in the existing support app, to always follow the same seven steps in the
same order and produce a structured summary at the end. Claude already has
access to the tools it would need (an account lookup tool, a disputes
lookup tool, a balance lookup tool) — nothing new needs to be reached that
isn't already reachable.

**Your choice:** Skill

**Justification (3–5 sentences):** This is decision point 2's exact
framing: "how to accomplish a task" rather than "reach a new system." The
scenario is explicit that every tool Claude would need already exists and
is already reachable — nothing new to connect to. What's missing is the
*procedure*: always run the seven checks in the same order and produce a
structured summary. A Skill packages exactly that as instructions Claude
follows, using tools it already has, which is precisely the "house
style / documented procedure" case the framework describes.

**Runner-up rejected, and why:** Custom tool — specifically, a single
"run_deletion_checklist" tool that internally calls the three lookups
itself and returns a final summary. It's tempting because it would also
produce consistent output, but it's worse here: it would hide the
step-by-step reasoning inside opaque application code, removing the
visibility into which check found what that a support agent reviewing the
interaction would want, and it would be building a bespoke integration for
something that isn't actually a new capability to reach — it's a fixed
procedure over tools that already exist, which is exactly what a Skill is
for without the extra code to write and maintain.

---

## Scenario 4

You want to let Claude search and read pages from a popular, widely-used
project-management SaaS product that your team relies on. That SaaS
product's vendor already publishes and maintains an official MCP server for
their product, kept up to date as their own API evolves, that any
MCP-compliant client can connect to.

**Your choice:** MCP (server) — specifically, connect to the vendor's
existing published server rather than building a new one.

**Justification (3–5 sentences):** This is decision point 4's second
clause: an MCP server already exists for the system you need to reach. The
vendor publishes and maintains it themselves, kept in sync with their own
API as it evolves — connecting to it as a client gets the integration with
essentially zero build effort and, critically, zero ongoing maintenance
burden on your side, since the people who own the underlying API are the
ones keeping the server correct.

**Runner-up rejected, and why:** Custom tool. It could technically call the
SaaS product's API directly, but doing so means permanently owning a
wrapper against a third-party API you don't control — every time the
vendor changes their API, you're responsible for noticing and updating
your own tool, work the vendor is already doing for free via their
maintained MCP server. Reaching for a custom tool here duplicates
maintenance effort that a "does an MCP server already exist for this"
check would have avoided entirely.

---

## Final reflection (2–3 sentences)

Across these four scenarios, what's the single question from the decision
framework that did the most work in separating the right answer from the
runner-up? Put differently: what's the one question you'd ask first, before
any of the others, if someone on your team proposed "let's just build an
MCP server for this" and you suspected that might be overkill?

**ANSWER:** "Will more than one application actually need this, or does a
suitable MCP server already exist for the system we're trying to reach?" —
decision point 4. It's the question specifically scoped to catching an
MCP-overkill proposal: scenario 1 answers "yes, five apps" and correctly
lands on MCP; scenario 2 answers "no, one app, nothing to reuse" and that
alone rules MCP out regardless of how technically feasible it'd be;
scenario 4 answers "a server already exists" and MCP wins for a different
reason (avoiding duplicated maintenance, not enabling reuse). Scenario 3 is
the one case this question doesn't directly resolve — there the decisive
question is procedure-vs-new-system (decision point 2) — which is itself
the point: the reuse/existing-server question is the right *first* filter
specifically against MCP-overkill, not a universal one-question answer to
all four mechanisms at once.
