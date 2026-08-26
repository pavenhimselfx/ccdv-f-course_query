# Domain 8 Quiz: Tools and MCPs

**This is original practice content**, written for this unofficial,
independently-built self-study course to exercise the CCDV-F blueprint's
Domain 8 skills (Tool Implementation, MCP Server Development, Agentic
Customization). It is not written or endorsed by Anthropic, and none of
these questions reproduce or paraphrase any real exam item — they are
original scenarios constructed to test the same underlying concepts the
public blueprint describes.

Each question states how many answers to select. Work through all 8, then
check yourself against the answer key at the bottom.

---

**1.** A developer defines a tool, and the API returns a response with
`stop_reason: "tool_use"` containing a `tool_use` content block. What is
the correct next step in the tool-use cycle?

Select **1**.

- A. The developer's code should treat this as an error and retry the API call with a shorter prompt.
- B. The developer's code should execute the corresponding function using the block's `input`, then send a new message containing a `tool_result` block referencing the `tool_use` block's `id`.
- C. Claude has already executed the tool internally; the developer's code just needs to display `block.input` to the end user.
- D. The developer's code should ignore the `tool_use` block and wait for a `stop_reason: "end_turn"` response instead.

---

**2.** A team ships a tool named `process_item` with the description
`"Processes an item."` and a single required string parameter named
`data`. In production, they observe Claude frequently calling this tool
with malformed or nonsensical values, or not calling it when it clearly
should have. What is the MOST LIKELY root cause, and the best first fix?

Select **1**.

- A. The model itself is not capable of reliable tool use; switch to manual, non-agentic code instead.
- B. The tool's description and parameter documentation are too vague for the model to infer when and how to call it correctly; rewrite the description to state specifically what the tool does, when to use it, and what format/content `data` should hold.
- C. The `input_schema` needs a `required` array, or tool calling will always be unreliable regardless of description quality.
- D. This is expected, unavoidable behavior for any tool with a single string parameter, and no description change will help.

---

**3.** A `create_invoice` tool's Python implementation raises an
uncaught `ConnectionError` because the downstream billing API timed out
mid-call. Which TWO of the following are both true and represent sound
practice for handling this?

Select **2**.

- A. The dispatch code should catch the exception and return a `tool_result` with structured error content (and typically `is_error: true`) describing the failure, rather than letting the exception propagate.
- B. Letting the exception propagate uncaught is preferable, because Claude will automatically detect the crashed process and retry the request on its own.
- C. Returning a fabricated "invoice created successfully" result to avoid showing an error is an acceptable workaround as long as the failure was transient.
- D. A well-designed mutating tool like `create_invoice` should support an idempotency mechanism (e.g. an idempotency key), since the caller (Claude, or the harness on Claude's behalf) may retry after a timeout and could otherwise create a duplicate invoice.

---

**4.** A team is building an agent that can (a) run a general web search
and (b) execute an internal `refund_customer(order_id, amount)` action
against their own billing system. Which ONE statement correctly
distinguishes how these two capabilities are most likely to be
implemented and governed?

Select **1**.

- A. Both should be implemented identically as client-side tools with identical approval requirements, since the mechanism for defining a tool is the same either way.
- B. The web search is a good candidate for a built-in/hosted tool executed by Anthropic's infrastructure, while `refund_customer` must be a custom client-side tool (it touches private, internal systems) and — because it's a consequential, hard-to-reverse mutating action — is a strong candidate for an approval checkpoint (human confirmation or a programmatic policy check) before execution.
- C. `refund_customer` should be implemented as a built-in/hosted tool so Anthropic's infrastructure can execute it directly against the company's billing system.
- D. Neither capability needs any error handling, since both are read-only from the model's perspective.

---

**5.** A production agent currently exposes twelve tools, including both
`get_user` and `fetch_user_by_id` (which do effectively the same lookup
with a very similar but not identical signature), and `search_orders` and
`find_orders` (also near-duplicates). The team notices Claude sometimes
picks the "wrong" one of each pair inconsistently across otherwise
similar requests. Which TWO actions best address the root cause, per tool
set construction best practices?

Select **2**.

- A. Merge each duplicate pair into a single tool (or make the distinction sharp and explicit in both name and description if they truly must remain separate), removing the ambiguity the model has to guess at.
- B. Add three more tools that also perform user lookups, so Claude has more options to choose from and can average out the inconsistency.
- C. Review actual tool-call transcripts to confirm which specific calls picked the "wrong" tool, using that evidence to guide which pair to merge or how to sharpen the distinction.
- D. Rename all twelve tools to short, generic single-word names (e.g. `user`, `orders`) so the model spends less time reading descriptions.

---

**6.** Which ONE statement correctly matches an MCP primitive to its
purpose?

Select **1**.

- A. A "resource" is a callable action with a JSON Schema of inputs that performs a side effect, like placing an order.
- B. A "tool" is read-only context data addressed by a URI, with no side effects and no caller-supplied parameters.
- C. A "prompt" is a reusable, possibly parameterized message/prompt template that an MCP server exposes for a connected client to surface or inject into a conversation.
- D. "Resources," "tools," and "prompts" are three different names for the same primitive, kept for backward compatibility with early protocol drafts.

---

**7.** A company is deciding how to deploy a new MCP server that wraps
access to an internal knowledge base. Which TWO statements about
deployment/transport choice and the client-server relationship are
correct?

Select **2**.

- A. If the server only ever needs to be used by one locally installed application on one machine (e.g. a single developer's local Claude Code setup), launching it as a local subprocess communicating over stdio is a reasonable, low-overhead choice.
- B. Stdio-based servers are limited to exposing at most one tool each; any server exposing more than one tool must use an HTTP-based transport instead.
- C. Regardless of which transport is chosen, the LLM-powered application (e.g. Claude Code, Claude Desktop, a custom app) always acts as the MCP client, and the knowledge-base server always acts as the MCP server responding to its requests.
- D. Choosing stdio versus an HTTP-based transport changes the fundamental protocol semantics of MCP (e.g. which primitives — resources, tools, prompts — the server is allowed to expose).

---

**8.** An internal platform team is evaluating a new requirement: "Claude
should be able to check the real-time status of a shipment by tracking
number, using our company's proprietary logistics system, and this
capability will be consumed by exactly one internal application with no
plans to share it elsewhere." Which mechanism best fits, and why?

Select **1**.

- A. A built-in/hosted tool, because shipment tracking is a common enough capability that Anthropic's infrastructure likely already implements a company-specific version of it.
- B. A Skill, because "check shipment status" is fundamentally a multi-step procedure rather than a new external system to reach.
- C. A custom (client-side) tool, because this is bespoke logic tied to a proprietary internal system, used by exactly one application with no stated reuse requirement — an MCP server would add process/deployment overhead with no corresponding reuse benefit.
- D. An MCP server, because any integration with an external system should always be built as an MCP server regardless of how many applications will use it.

---

## Answer key and rationale

**1. Answer: B.**
This is the core tool-use cycle from README.md section 1.1: Claude never
executes anything itself — it only requests execution via a `tool_use`
block. The developer's code must execute the corresponding function and
respond with a `tool_result` block whose `tool_use_id` matches the
`tool_use` block's `id`, so Claude can correlate the result with its
request. (A) misreads `tool_use` as an error state — it's normal,
expected output. (C) is backwards — Claude requests, your code executes.
(D) would stall the conversation forever, since `stop_reason` won't become
`"end_turn"` until a `tool_result` is supplied.

**2. Answer: B.**
This maps directly to README.md section 1.3: the model relies *entirely*
on the tool's description and parameter documentation to decide when and
how to call it — there is no separate onboarding step the way there is for
a human reading API docs once. A vague description like "Processes an
item" with an undocumented `data` field gives the model nothing to work
with, causing exactly the symptoms described (wrong/missed calls,
malformed arguments). (A) overstates the problem — tool use is generally
reliable when tools are well-specified. (C) is a real good practice but
doesn't address description vagueness, which is the stated symptom. (D)
is simply false; well-documented single-string-parameter tools work fine.

**3. Answer: A and D.**
(A) is the central error-handling practice from README.md section 1.4:
convert exceptions into structured `tool_result` content instead of
letting them crash the loop. (D) reflects the idempotency guidance from
section 1.2 — a timeout is exactly the scenario where a caller might retry
and accidentally double-create a mutating side effect, so idempotency
support is sound practice for tools like this. (B) is false — Claude has
no ability to "detect a crashed process," it only sees what's in the
transcript, and a crash means the conversation simply stops. (C) directly
contradicts the guidance that a fabricated success is worse than a visible
error, since downstream systems and the end user will act as though the
invoice was actually created.

**4. Answer: B.**
This is the client-side/server-side and approval-pattern distinction from
README.md sections 1.5. General web search is a generic capability well
suited to a hosted/built-in tool; `refund_customer` touches private
internal billing data and must be implemented and executed in the
company's own code (a custom tool) — and because it's consequential and
hard to reverse, it's a strong candidate for a human-in-the-loop or
policy-based approval checkpoint before it actually executes. (A) ignores
that consequence/reversibility, not implementation mechanics, should drive
approval requirements — a read-only search and a money-moving refund
shouldn't share the same approval bar just because both are "tools." (C)
is wrong and actually unsafe — hosted tools cannot reach a company's
private internal billing system. (D) is false; `refund_customer` is a
prime candidate for careful error handling given the consequences of a
silent failure or false success.

**5. Answer: A and C.**
This is the tool set construction guidance from README.md section 1.6:
merge or sharply differentiate overlapping tools (A), and use actual
transcripts of wrong-tool-choice calls as evidence for where the ambiguity
lives (C) — that's the recommended way to diagnose which pair to fix and
how. (B) does the opposite of what's needed — more overlapping tools make
selection strictly harder, not better on average. (D) also worsens the
problem: generic single-word names remove the disambiguating information
the model needs, rather than adding clarity.

**6. Answer: C.**
This matches the three MCP primitives from README.md section 2.2:
resources are readable, URI-addressed context/data (not actions); tools
are callable actions with a JSON Schema of inputs (not read-only,
argument-free data); prompts are reusable, possibly parameterized message
templates a server exposes to a connected client. (A) and (B) swap the
definitions of resource and tool. (D) is false — the three primitives are
deliberately distinct, serving different purposes (context vs. action vs.
template).

**7. Answer: A and C.**
(A) reflects the stdio guidance from README.md section 2.4 — stdio,
process-based launch is the simplest, lowest-overhead pattern for a
single local client/server pairing, with no networking or port
configuration required. (C) reflects the fixed client-server relationship
also from section 2.4: the LLM-powered application is always the MCP
client, and the server it connects to is always the MCP server responding
to its requests, regardless of which transport carries the messages. (B)
is false — transport choice is a deployment decision driven by reach and
topology (how many clients, on what machines), not a hard limit on how
many tools a stdio server may expose; a single local stdio server can
expose any number of tools, resources, and prompts. (D) is also false —
transport is a deployment-layer detail sitting underneath the protocol; it
does not change which primitives (resources, tools, prompts) a server is
permitted to expose or how clients address them.

**8. Answer: C.**
Working through the decision framework in README.md section 3.2: no
built-in tool covers a proprietary internal logistics system (rules out
A); this is a new external system to reach, not a procedure using tools
Claude already has (rules out B, which misapplies the Skill criterion to
a scenario that's clearly about reaching a new system, not following a
known procedure); and the scenario explicitly states single-application
use with no reuse requirement, which is exactly the profile for a custom
tool rather than the overhead of standing up and maintaining an MCP
server (rules out D, which also states an overly rigid rule the framework
explicitly warns against — MCP is not the default for every external
integration regardless of reuse).
