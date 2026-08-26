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

**Your choice:** ______________________

**Justification (3–5 sentences):**

**Runner-up rejected, and why:**

---

## Scenario 2

A single internal reporting app needs to convert a raw dollar amount plus a
currency code into a formatted display string (e.g. `1234.5, "USD"` →
`"$1,234.50"`), using a small, fixed set of formatting rules specific to
this one app's UI conventions. No other application needs this, and it
will never be more complex than string formatting based on a lookup table
of currency symbols and decimal conventions.

**Your choice:** ______________________

**Justification (3–5 sentences):**

**Runner-up rejected, and why:**

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

**Your choice:** ______________________

**Justification (3–5 sentences):**

**Runner-up rejected, and why:**

---

## Scenario 4

You want to let Claude search and read pages from a popular, widely-used
project-management SaaS product that your team relies on. That SaaS
product's vendor already publishes and maintains an official MCP server for
their product, kept up to date as their own API evolves, that any
MCP-compliant client can connect to.

**Your choice:** ______________________

**Justification (3–5 sentences):**

**Runner-up rejected, and why:**

---

## Final reflection (2–3 sentences)

Across these four scenarios, what's the single question from the decision
framework that did the most work in separating the right answer from the
runner-up? Put differently: what's the one question you'd ask first, before
any of the others, if someone on your team proposed "let's just build an
MCP server for this" and you suspected that might be overkill?
