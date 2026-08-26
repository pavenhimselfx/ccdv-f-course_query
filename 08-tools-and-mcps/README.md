# Domain 8: Tools and MCPs

**Exam weight: 10.6% of CCDV-F**

> **Cost note:** all three exercises in this domain can now be done at zero marginal cost.
> `ex1`'s tool-use exercise runs on the **Claude Agent SDK** (`claude_agent_sdk`), which
> authenticates against a Claude.ai Pro/Max/Team/Enterprise subscription via
> `CLAUDE_CODE_OAUTH_TOKEN` instead of a metered Console API key — see `00-setup/README.md`
> section 1 for the setup (`claude setup-token`, then export the token) if you haven't done
> it yet. `ex2`'s MCP server never needed an Anthropic key to write or run in the first
> place (it's a standalone stdio process), and `ex2b_test_with_claude_code.md` now documents
> testing it for free by connecting it to Claude Code under that same subscription, instead
> of writing a raw-API Python test client. `ex3` (the tools-vs-skills-vs-MCP decision
> exercise) needs no calls at all — it's pure written reasoning. See `00-setup/README.md`
> section 3 for the full per-exercise table across the whole course.

This is an unofficial, independently-built self-study module preparing you for the
"Claude Certified Developer – Foundations" (CCDV-F) exam, blueprint version 1.0
(effective July 2026). It is not published or endorsed by Anthropic. Everything in
this module — explanations, exercises, and practice questions — is original
content written to teach the public blueprint's skills, not a reproduction of any
real exam item.

The blueprint breaks this domain into three skills:

| Skill | Weight |
|---|---|
| Tool Implementation | 4.4% |
| MCP Server Development | 2.1% |
| Agentic Customization | 4.1% |

Read this file in order — each section builds on the last. Then work through
`exercises/` in order (`ex1` → `ex2` → `ex2b` → `ex3`), where `ex2b` is a
short guide to testing your `ex2` MCP server via Claude Code rather than a
separate exercise script. Check your work against `solutions/` only after
you've made a genuine attempt. Finish with `quiz.md`.

A note on currency: tool-use APIs, the MCP specification, and the Python SDKs
for both move quickly. This module was written against the author's knowledge
as of early-to-mid 2026. Treat concrete method names, exact JSON field names,
and SDK import paths here as "roughly right, verify before you ship." The
canonical, current sources are [docs.claude.com](https://docs.claude.com) and
[modelcontextprotocol.io](https://modelcontextprotocol.io). The concepts and
decision criteria in this module age far more slowly than the API surface —
that's where most of the exam-relevant substance lives, and where this module
puts most of its weight.

---

## 1. Tool Implementation (4.4%)

### 1.1 The mechanics: tool use and function calling

"Tool use" (Anthropic's term) and "function calling" (the more generic
industry term) describe the same mechanism: you tell Claude what actions are
available, Claude decides whether and how to invoke one, your code actually
performs the action, and you hand the result back to Claude so it can
continue reasoning. Claude itself never executes anything — it only ever
*requests* that something be executed and *reads* what came back. Every side
effect happens in code you control.

Concretely, the cycle looks like this on the Messages API:

1. **You define tools** as a list of JSON Schema objects passed in the
   `tools` parameter of `client.messages.create(...)`. Each tool has a
   `name`, a `description`, and an `input_schema` (a JSON Schema describing
   the parameters Claude must supply).
2. **Claude decides to call a tool.** Instead of (or alongside) ordinary
   text, the response's `content` list contains a `tool_use` block: a
   `type: "tool_use"`, a unique `id`, the tool's `name`, and an `input`
   object that already validates against the schema you gave it. The
   response's `stop_reason` is `"tool_use"` when Claude is waiting on a tool
   result before it can continue.
3. **Your code executes the tool.** You look up `block.name`, call the
   matching Python function with `**block.input`, and get back some result
   (a string, or anything JSON-serializable).
4. **You return a `tool_result`.** You send a new message with
   `role: "user"` whose content is a `tool_result` block: `type:
   "tool_result"`, `tool_use_id` matching the `id` from step 2, and
   `content` holding whatever you want Claude to see (plus optionally
   `is_error: true` — more on that in 1.4).
5. **Claude continues.** With the tool result in context, Claude either
   calls another tool (repeat from step 2) or produces a final text answer
   (`stop_reason: "end_turn"`).

A minimal tool definition:

```python
GET_WEATHER_TOOL = {
    "name": "get_weather",
    "description": (
        "Get the current weather for a city. Use this whenever the user "
        "asks about current conditions, temperature, or forecast for a "
        "named location. Do not use it for historical weather questions."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name, e.g. 'Austin' or 'Nairobi'.",
            },
            "unit": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "Temperature unit. Defaults to celsius.",
            },
        },
        "required": ["city"],
    },
}
```

Nothing about this schema is Claude-specific magic: it is plain JSON Schema.
Claude's contribution is *deciding when the schema applies to the
conversation* and *filling in valid arguments* — the actual execution is
100% your responsibility.

### 1.2 Configuring tools for external system interaction

Most useful tools wrap something outside the model entirely: a database
query, an internal REST API, a third-party service, a filesystem, a shell.
When a tool's Python implementation talks to an external system, treat it
like any other piece of production integration code, because from the
system's point of view, that's exactly what it is — the fact that an LLM
decided to call it changes nothing about the plumbing:

- **Authentication** — store credentials (API keys, OAuth tokens, service
  account secrets) outside your prompt and outside any value the model can
  see or influence; read them from environment variables or a secrets
  manager inside the tool's implementation, never embed them in the tool
  description or accept them as a tool *argument* from Claude.
- **Network calls** — real HTTP calls to real services can be slow or
  simply fail. Set explicit timeouts (a hanging tool call blocks the whole
  agentic loop) and decide up front what a failed call returns: raising an
  uncaught exception is almost always wrong (see 1.4).
- **Rate limits and retries** — external systems throttle you the same way
  regardless of who's calling; wrap flaky calls in bounded retry logic
  (with backoff) inside the tool, not by hoping Claude retries correctly on
  its own.
- **Least privilege** — if the tool wraps a scoped API key or a database
  role, scope it to the minimum the tool actually needs. An agent that can
  call `read_customer_record` should not be handed credentials that also
  permit `DROP TABLE`.
- **Idempotency for anything that mutates state** — an agent may call a
  tool more than once for the same logical action (its own retry, a
  misjudged repeat). Where the underlying system supports it, design
  mutating tools (e.g. `create_order`) to accept or generate an idempotency
  key so a duplicate call doesn't duplicate the side effect.

### 1.3 Writing tool descriptions

This is the single highest-leverage skill in this section, and it is
frequently underrated by developers coming from traditional API design.
When you write a REST endpoint, a human reads the docs once and then calls
it correctly forever. When you write a tool for Claude, **the description
and parameter docs are the *only* information the model has, every single
time, for deciding whether to call the tool at all and how to fill in its
arguments.** There is no separate onboarding step. A vague or ambiguous
description doesn't just make the tool harder to discover — it directly
causes wrong tool selection (calling the wrong tool, or the right tool at
the wrong moment) and malformed or nonsensical arguments.

Good tool descriptions:

- **State what the tool does, in plain terms**, not what it's named after.
  `"search_docs"` as a name plus `"Searches documentation."` as a
  description is nearly useless — say *what* documentation, in *what*
  format the query should be, and what comes back.
- **State when to use it (and, if it matters, when not to).** "Use this to
  look up a customer's order history by email or order ID. Do not use this
  for questions about products that haven't been ordered yet" resolves
  ambiguity the model would otherwise have to guess at.
- **Document every parameter individually**, including format, units,
  valid ranges, and defaults. "amount" is worse than "amount: the payment
  amount in whole US cents (e.g. 500 = $5.00)" — a model that isn't told
  the unit will guess, and it may guess wrong exactly when it matters most.
- **Use `enum` wherever the valid values are a fixed, known set.** This
  prunes an entire class of invalid-argument failures before they can
  happen, rather than relying on the description to explain the constraint
  in prose.
- **Say what happens on failure, briefly, if it's surprising.** If
  `get_order` returns an empty result rather than an error when no order
  matches, a one-line note prevents Claude from mishandling the empty case.

Tool descriptions are prompt-engineering artifacts. Treat them with the same
rigor you'd give a system prompt: write a draft, run realistic queries
against it, look at what gets called and with what arguments, and revise
descriptions that produced wrong or hesitant tool choices.

### 1.4 Error handling inside tools

A tool's Python implementation will eventually fail: the downstream API is
down, the input didn't correspond to real data, a permission check failed.
**The tool call must not crash the agentic loop.** Concretely: wrap the
tool's execution in a `try`/`except` in your dispatch code, and when it
fails, return a `tool_result` describing the failure as structured data
instead of letting an exception propagate and killing the whole run.

```python
try:
    result = execute_tool(name, tool_input)
    tool_result_block = {
        "type": "tool_result",
        "tool_use_id": block.id,
        "content": json.dumps(result),
    }
except InventoryError as e:
    tool_result_block = {
        "type": "tool_result",
        "tool_use_id": block.id,
        "content": json.dumps({"error": str(e), "error_type": "not_found"}),
        "is_error": True,
    }
```

Why this matters: Claude only knows what's in the transcript. If the tool
call simply vanishes because your code threw and the process died, Claude
never gets a chance to react. If instead you return a clear, structured
error, Claude can do what a competent engineer would do with that same
error message — apologize and ask a clarifying question, try a corrected
argument (e.g. re-attempt with a different ID after a "not found"), fall
back to a different tool, or explain to the end user what went wrong. The
`is_error: true` flag is a signal to Claude that this `tool_result`
represents a failure rather than a normal successful payload, which helps
it weight the content accordingly — but the structured, readable error
*content* is what actually lets it act sensibly, regardless of whether you
set that flag. Never let error handling silently swallow the failure and
return a fabricated success either — an inaccurate "it worked" result is
worse than a visible error, because Claude (and the end user) will proceed
as if the action actually happened.

### 1.5 Tool usage patterns

**Agentic harness dispatch.** The `while stop_reason == "tool_use"` loop
described in 1.1 — call the API, inspect the response for `tool_use`
blocks, execute them, append `tool_result`s, call again — is sometimes
called the "agentic harness" or just "the loop." You can hand-write this
loop yourself against the raw Messages API (useful for understanding it,
and sometimes necessary for full control), or you can use a harness that's
already built: the Claude Agent SDK, or Claude Code itself, both implement
this dispatch loop for you, along with concerns like context management,
permission checks, and turn limits. Understanding the loop by hand is what
lets you reason correctly about what a harness is doing on your behalf.

**Client-side vs. server-side (hosted) tools.** Not every tool executes in
your process:

- A **client-side tool** is one *you* define and *you* execute — the
  pattern in every example above. Claude only ever sees the schema and the
  result; the code that runs when the tool is "called" lives entirely in
  your application.
- A **server-side (hosted) tool** is one Anthropic's infrastructure both
  defines and executes on your behalf — for example a hosted web search or
  code execution tool. You typically just enable it (sometimes with
  configuration), Claude requests it the same way, but the actual
  execution happens on Anthropic's side, and the result is inserted back
  into the conversation without a manual `tool_result` round-trip through
  your code.

  The tradeoff: hosted tools cost you no implementation or maintenance
  effort and are kept up to date by Anthropic, but you don't control their
  internals, can't point them at private/internal systems, and are subject
  to whatever behavior and limits Anthropic ships. Client-side tools are
  more work but are the only option for anything that touches your own
  data, your own auth, or bespoke internal logic.

**Approval patterns.** Some tool calls are safe to run automatically
(read-only lookups); others are consequential enough (sending an email,
deleting a record, spending money, running arbitrary shell commands) that
you want a checkpoint before execution. Common approaches, often combined:

- **Human-in-the-loop confirmation** — surface the pending tool call (name
  + arguments) to a person and require an explicit approve/deny before your
  dispatch code actually executes it. This is the pattern behind
  interactive coding-agent UIs that ask "Allow this command?" before
  running a shell tool.
- **Programmatic policy / allow-deny rules** — a rules layer in your
  dispatch code that auto-approves some calls (e.g. anything matching
  `get_*`), auto-denies others outright (e.g. anything touching a
  production credentials table), and only escalates the remainder to a
  human. This scales better than all-manual approval once tool volume
  grows.
- **Scoped/staged execution** — e.g. a "dry run" mode where a mutating tool
  reports what it *would* do without doing it, so a human or a second
  automated check can review the plan before a second, real invocation
  performs it.

Design the approval boundary around the tool's *consequences* (Can it be
undone? Does it cost money or spend a resource? Does it affect someone
other than the current user?), not around how technically hard the tool was
to write.

### 1.6 Tool set construction best practices

Giving Claude access to *more* tools is not free — a larger, sloppier tool
set makes correct selection *harder*, not easier, because every tool
description adds to what the model must disambiguate between at decision
time. Practical guidelines:

- **Keep the tool set small and focused** on what the current task actually
  needs. A general-purpose agent with fifty barely-differentiated tools
  will pick wrong more often than a narrowly-scoped agent with five
  well-chosen ones. If an application serves multiple very different
  jobs, consider scoping down which tools are available per request/session
  rather than exposing everything everywhere.
- **Avoid overlapping tools.** Two tools that do nearly the same thing
  (`search_users` and `find_users`, or `get_order` and `fetch_order_by_id`)
  force Claude to guess at a distinction that may not even meaningfully
  exist, and different runs may pick differently. Merge them, or make the
  difference sharp and explicit in both names and descriptions if they
  truly must coexist (e.g. `get_order_by_id` vs. `search_orders_by_customer`
  is a real, describable distinction; two near-synonyms are not).
- **Name tools clearly and consistently.** Prefer explicit, verb-first,
  unambiguous names (`create_support_ticket`, not `handle_ticket` or
  `ticket_action`). A consistent naming convention across a tool set (e.g.
  always `verb_noun`) reduces the model's uncertainty about what a new,
  unfamiliar tool name probably does.
- **Push complexity into fewer, well-designed parameters** rather than
  proliferating many similar tools that differ only by a fixed argument
  (e.g. one `get_report(period: "daily"|"weekly"|"monthly")` beats three
  separate `get_daily_report` / `get_weekly_report` / `get_monthly_report`
  tools).
- **Periodically review actual tool-call transcripts** for wrong-tool or
  malformed-argument calls — this is the most reliable signal that a
  description is unclear or that two tools are overlapping in practice, not
  just in theory.

---

## 2. MCP Server Development (2.1%)

### 2.1 What MCP is

The **Model Context Protocol (MCP)** is an open protocol, introduced by
Anthropic and since adopted more broadly, that standardizes how
applications expose tools, data, and prompt templates to LLM-powered
applications. Before MCP, every integration between an LLM app and an
external system (a database, a SaaS product, an internal service) tended to
be bespoke, hand-wired glue code specific to that one pairing. MCP defines a
common client-server contract so that **any** MCP-compliant server can be
plugged into **any** MCP-compliant client with no custom integration code —
conceptually similar to what a common driver interface does for databases,
or what USB did for peripherals: write the server once, and every
compliant client (Claude Desktop, Claude Code, a custom application built
on the Claude Agent SDK or another MCP client library) can use it without
per-application glue.

MCP messages are exchanged as JSON-RPC 2.0 over one of a small number of
supported transports (2.4). The protocol defines three primitive kinds of
things a server can expose to a client, covered next.

### 2.2 Server authoring: resources, tools, and prompts

An MCP server declares some combination of three primitive capabilities:

- **Resources** — readable, addressable data or context, each identified by
  a URI (e.g. `file:///project/notes.md`, or a custom scheme like
  `inventory://items/42`). Resources are the MCP analog of a GET request:
  the client asks to read one, and the server returns its content. They're
  the right shape for "context Claude should be able to look at" — a file,
  a database record, a log excerpt — as opposed to an action.
- **Tools** — callable actions, each with a name, a description, and a JSON
  Schema for its inputs, extremely similar in shape to the tool
  definitions from Section 1. The key difference from a plain client-side
  tool (1.5) is *where the implementation lives*: an MCP tool's logic runs
  inside the MCP server process, not inside your host application's code,
  and the MCP client (the host app) forwards Claude's tool-use request to
  the server and relays the result back.
- **Prompts** — reusable prompt templates the server exposes, optionally
  parameterized, that a client can surface to a user or inject into a
  conversation (e.g. a `/summarize-pr` prompt template a Git-hosting MCP
  server might expose, so any client connected to it gains that
  ready-made prompt without reimplementing it).

A minimal server (using the common high-level Python SDK pattern) might
register one tool and one resource:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo-server")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers and return the sum."""
    return a + b

@mcp.resource("config://app-version")
def app_version() -> str:
    """The running application's version string."""
    return "1.4.2"

if __name__ == "__main__":
    mcp.run()  # defaults to stdio transport
```

Exact class names, decorator names, and import paths shift as the SDK
matures — check the current
[MCP Python SDK](https://modelcontextprotocol.io) documentation before
writing production code. The *shape* of the pattern — a server object,
declarative registration of tools/resources/prompts via decorators or
explicit registration calls, and a `run()` entrypoint — is the durable,
exam-relevant part.

### 2.3 Deployment and integration with Claude applications

An MCP server is only useful once something is connected to it as a
**client**. In this relationship, the LLM-powered application (Claude
Desktop, Claude Code, a custom app built on the Claude Agent SDK, or any
other MCP-compliant application) plays the client role, and your server
plays the server role — the same client/server vocabulary as any other
networked system, just with an LLM application on the client end.
Integration typically means:

- **Registering the server with a client's configuration** — e.g. Claude
  Desktop and Claude Code both read a configuration file (or a CLI/UI flow)
  that lists MCP servers to connect to at startup, along with how to launch
  or reach each one.
- **Local, process-based deployment** — the client launches your server as
  a local subprocess (often via a command like `python server.py` or
  `npx some-mcp-server`) and talks to it over stdio (2.4). This is the
  simplest deployment: no networking, no auth beyond OS process
  boundaries, easy to develop and debug locally.
- **Remote deployment** — the server runs as a standalone network service
  (e.g. behind HTTPS, potentially with OAuth-based authorization) and any
  number of clients connect to it over the network instead of spawning it
  as a subprocess. This is the right shape when the same server needs to
  serve many users or many different client applications without each of
  them running their own local copy, and it's discussed further as a
  driver for choosing MCP at all in Section 3.

### 2.4 Communication patterns

MCP defines transport-level options for how the JSON-RPC messages between
client and server actually move:

- **stdio (standard input/output)** — the client spawns the server as a
  child process and communication happens over that process's stdin/stdout
  pipes. This is the default, simplest pattern for **local** servers: no
  network configuration, no ports, no auth beyond "you can run this binary
  on this machine." It's the natural fit for a server that wraps local
  resources (files on disk, a local tool, a local database) and for
  development/testing.
- **HTTP-based transports (e.g. Streamable HTTP)** — the server runs as an
  addressable network service and the client connects to it over HTTP,
  allowing the server to run on different hardware from the client,
  potentially serving many clients concurrently, with standard HTTP-layer
  concerns (authentication/authorization, TLS, load balancing) applying.
  This is the right choice for a server that must be reachable by multiple
  separate client applications or deployed independently of any one of
  them.

In both cases, the **client/server relationship is fixed regardless of
transport**: the LLM application always acts as the MCP *client*, initiating
requests (list tools, call a tool, read a resource, get a prompt); your
server always *responds*. Choosing a transport is a deployment decision
(where does this run, who can reach it, does it need to survive independent
of any one client), not a change to the protocol semantics above it.

---

## 3. Agentic Customization (4.1%)

### 3.1 Four ways to extend what Claude can do

By this point in the module you've seen the individual pieces — client-side
tools, hosted/server-side tools, MCP servers. This skill is about choosing
*correctly* among four extension mechanisms, because picking the wrong one
for a given job produces real costs: unnecessary maintenance burden,
duplicated logic across applications, or an overbuilt integration for a
need that a five-line function would have solved.

| Mechanism | Where logic lives / runs | Control | Best fit |
|---|---|---|---|
| **Built-in tool** | Anthropic's infrastructure (hosted) | None over internals; you enable/configure | A well-known, generic capability (e.g. web search, code execution) that doesn't need to touch your private systems |
| **Custom tool** | Your own application code | Full | Bespoke logic tied to your app's own data, auth, or internal systems; used by this one application |
| **Skill** | A packaged instruction/procedure set Claude loads and follows | You author the procedure; Claude executes it using tools it already has | A repeatable "how to do X" playbook/process — house style, a multi-step checklist, a domain procedure — more about *method* than about reaching a new external system |
| **MCP server** | A separate server process/service, possibly reused by many clients | Full over the server; standardized interface to any client | A capability that must be reusable and independently maintained across multiple different Claude applications, or that already has an existing MCP server published for it |

### 3.2 The decision framework, worked through

Ask, in roughly this order:

1. **Does a built-in/hosted tool already do this?** If Anthropic already
   ships a hosted tool for the generic capability you need (e.g. general
   web search, running arbitrary code in a sandbox) and you don't need it
   to touch anything private, enabling the built-in tool is almost always
   less work and less to maintain than building your own version. Give
   this up only when you need behavior, data access, or control the hosted
   version doesn't offer.

2. **Is this "how to accomplish a task" rather than "reach a new system"?**
   If what you actually need to give Claude is a repeatable *procedure* —
   a checklist for handling a certain ticket category, a house style for
   drafting a document type, a multi-step debugging playbook — and Claude
   already has (or can be given) the tools that procedure calls for, a
   **Skill** is usually the right shape. Skills package "how to do
   something" as instructions Claude follows, not a new capability to
   reach an external system. Building a full custom tool or MCP server for
   what's really just a documented procedure is over-engineering.

3. **Is this bespoke logic used by exactly one application, tightly coupled
   to that application's own code/data/auth?** A **custom (client-side)
   tool** is the right fit: define it in your app, execute it in your app,
   full control, no protocol or server-deployment overhead. Most
   internal-only integrations — a one-off calculation, a call into your
   own internal API that only this one agent needs — belong here. Don't
   reach for MCP just because it's the more "official"-sounding option; if
   nothing else will ever reuse this integration, an MCP server adds a
   process to run, a transport to configure, and a maintenance surface for
   zero actual reuse benefit.

4. **Does this capability need to be reusable and independently maintained
   across multiple different Claude applications** (several internal
   agents, a desktop app and a CLI and a custom backend, etc.), **or does
   an MCP server already exist for the system you need to reach** (a
   published/third-party MCP server for a popular SaaS product, a
   database, a dev tool)? Then **MCP** is the right fit: build (or reuse)
   one server, and every compliant client — including future ones you
   haven't written yet — can connect to it with no bespoke glue. This is
   also the right call when a platform/infra team, rather than any single
   application team, owns and evolves the capability.

### 3.3 Worked scenarios

- *"We need Claude to be able to look up live public stock prices for any
  ticker a user mentions."* If a hosted/built-in tool already covers
  general web lookup and that's good enough fidelity, use it. If you need
  a specific, reliable data feed, a small **custom tool** wrapping that
  API is enough — this is single-application, single-purpose logic.

- *"Five different internal Claude-powered apps (a support bot, an internal
  analytics assistant, a Slack bot, and two others) all need to look up
  and update records in our internal customer database, and a platform
  team owns that integration."* This is the textbook case for an **MCP
  server**: one server, maintained centrally, reused by every consuming
  application without each team re-implementing the same auth and query
  logic.

- *"Every time someone opens a new-hire onboarding ticket, we want Claude
  to follow the same seven-step review checklist our team already uses,
  using tools it already has access to."* This is a **Skill** — you're not
  adding a new external capability, you're packaging a reusable procedure
  for Claude to follow.

- *"We want Claude to be able to execute short Python snippets for
  calculations during a conversation, and we don't need it to touch our
  own infrastructure to do it."* A **built-in/hosted** code-execution tool,
  if one is available and sufficient, is the lowest-effort correct choice
  — you're not gaining anything by hand-building a sandboxed executor
  yourself for a generic, non-proprietary need.

The common failure mode worth internalizing for the exam: reaching for MCP
by default because it sounds like "the proper way," when the actual
requirement is single-application, non-reused, bespoke logic that a plain
custom tool would serve with far less overhead — and the mirror-image
mistake, hand-building a bespoke integration inside one app when the same
capability is (or should be) needed by several applications and would be
better served, and better maintained, as one shared MCP server.

---

Continue to `exercises/` when you're ready to apply this. Work `ex1` → `ex2`
→ `ex2b` → `ex3` in order, then `quiz.md`.
