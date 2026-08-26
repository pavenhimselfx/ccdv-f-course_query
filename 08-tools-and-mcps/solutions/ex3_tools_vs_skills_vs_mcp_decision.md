# SOLUTION - Exercise 3: Built-in Tool vs. Custom Tool vs. Skill vs. MCP

Domain 8 (Tools and MCPs) — Skill: Agentic Customization (4.1%)

These are reference answers reflecting the decision framework in
README.md section 3.2. Scenario decisions like these have real judgment
calls in them — a differently-reasoned answer isn't automatically wrong if
it correctly applies the framework's questions to the scenario's actual
constraints. What matters most is the *reasoning path*, not just the label.

---

## Scenario 1 — shared CRM access across five internal apps

**Choice: MCP (server)**

**Justification:** Walking the framework in order: no built-in/hosted tool
covers a proprietary internal CRM, so step 1 is out immediately. This isn't
a "how to do a task" procedure question either (step 2) — it's a new
external system that needs to be *reached*, with real auth and query logic
behind it. The decisive question is step 4: this capability is explicitly
needed by **five separate applications**, and is explicitly **owned and
maintained by a platform team** rather than any single app team. That's
exactly the shape MCP is for — build the CRM integration once, as a
server, and every one of the five apps (plus any future sixth app) connects
to it as a client with zero re-implementation of auth or query logic.
Centralizing it also means the platform team can evolve the CRM
integration in one place without coordinating five separate deployments.

**Runner-up rejected:** A custom tool, re-implemented independently inside
each of the five applications. It's technically workable — nothing stops
five teams from each writing their own CRM client — but it directly
contradicts the "owned and maintained centrally, don't duplicate across
apps" constraint the scenario states explicitly: five copies of the same
auth/query logic is five times the maintenance burden and five chances for
the copies to drift out of sync with each other and with the CRM's actual
API.

---

## Scenario 2 — one app's currency formatting helper

**Choice: Custom tool** *(arguably not even needing model involvement at
all — see note below, but among the four options, custom tool is correct)*

**Justification:** No built-in/hosted tool formats arbitrary internal
display strings (step 1 out). It's not a multi-step procedure Claude needs
to follow using existing tools (step 2 out) — it's a small, self-contained
computation. Step 3 applies directly: this is bespoke logic, used by
exactly **one** application, with no reuse requirement stated or implied,
and it's simple enough that writing and owning it directly inside that
app's own code is by far the lowest-overhead correct choice — a couple of
lines of Python behind a tool schema, no server process, no protocol.

**Runner-up rejected:** MCP. Building and deploying a whole separate server
process for a single-application string-formatting helper is a clear case
of the "reach for MCP because it sounds official" failure mode called out
at the end of README.md section 3.3 — real overhead (a process to run, a
transport to configure, ongoing maintenance) for zero actual reuse benefit,
since nothing else will ever call it.

*(Side note beyond the four options: something this deterministic and
input-bounded might not need to be a model-facing tool at all — plain
Python formatting logic called directly by the app, with no LLM
involvement in the loop, could be simpler still. But if the app's design
does route this through Claude — e.g. Claude is composing a message that
includes a formatted amount — a custom tool is the right mechanism among
the four.)*

---

## Scenario 3 — the seven-step account-deletion checklist

**Choice: Skill**

**Justification:** Step 1 is out — no built-in tool encodes an internal
seven-step business checklist. Step 2 is the decisive question here and
it's answered directly by the scenario: this is explicitly a **procedure**
("always follow the same seven steps in the same order") and Claude
**already has the tools it needs** (account lookup, disputes lookup,
balance lookup) — nothing new needs to be *reached*. That's precisely the
"how to do something, not a new external capability" distinction that
separates a Skill from a tool or MCP server. Packaging the checklist as a
Skill lets Claude follow the same documented procedure consistently across
every account-deletion request, and lets the support team update the
procedure (e.g. add an eighth step) by editing instructions rather than
touching application code.

**Runner-up rejected:** A custom tool, e.g. one big `run_deletion_checklist()`
tool that internally does all seven steps. This would work mechanically,
but it collapses seven independently meaningful checks (each potentially
needing its own judgment call, like "does this count as an open dispute")
into one opaque black-box call, hiding exactly the step-by-step reasoning
a human reviewer would want to see and audit. A Skill that walks the
existing lookup tools through the seven steps keeps each step visible and
individually reasoned about, which matches how the support team actually
wants this handled.

---

## Scenario 4 — third-party SaaS product with a vendor-published MCP server

**Choice: MCP (server)** — specifically, connect to the **existing,
vendor-published** server rather than building one

**Justification:** Step 1 is out (no generic built-in tool reaches a
specific third-party product's private data). Step 4 applies directly and
is close to the clearest possible MCP case: an MCP server for this exact
system **already exists**, is **maintained by the vendor** (who has the
most context and the most incentive to keep it correct as their own API
evolves), and is designed to be reused by any compliant client. There is
no better-informed maintainer available than the vendor itself, and
connecting to their server means your application gets ongoing
compatibility updates for free as their product's API changes.

**Runner-up rejected:** A custom tool that calls the SaaS product's REST
API directly. This is possible and sometimes still reasonable (e.g. if you
need behavior the published MCP server doesn't expose), but as the default
choice here it means taking on maintenance of an integration against a
third-party API that the vendor is already maintaining a standardized,
protocol-compliant version of — duplicated effort with no upside when a
well-maintained MCP server for exactly this product already exists.

---

## Final reflection

The single highest-leverage question across all four scenarios is **"will
more than one application need this, and is it (or should it be)
independently maintained apart from any one of them?"** — Scenario 1 and
Scenario 4 answer "yes" (five apps sharing one CRM integration; a
vendor-maintained server serving any client) and land on MCP; Scenario 2
answers "no" (one app, no reuse) and lands on a plain custom tool.
Scenario 3 shows the question has to be asked *after* first checking
whether this is even a new capability to reach at all, versus a procedure
using tools Claude already has — that earlier check is what routes it to a
Skill instead of ever reaching the reuse question. So in practice: ask
"is this a new external capability, or a procedure using what I already
have?" first; if it's a new capability, ask the reuse/ownership question
second — that ordering is what would have caught "let's just build an MCP
server for this" as premature in Scenario 2, where the reuse question
never even gets a "yes."
