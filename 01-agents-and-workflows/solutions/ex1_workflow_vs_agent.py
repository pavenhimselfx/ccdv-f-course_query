"""
SOLUTION - Exercise 1: Workflow vs. Agent

Written against the `claude-agent-sdk` Python package (PyPI: `claude-agent-sdk`),
which authenticates against a Claude.ai subscription via CLAUDE_CODE_OAUTH_TOKEN
(see 00-setup/README.md section 1: `claude setup-token`) instead of a metered
ANTHROPIC_API_KEY - so this runs at zero marginal cost on a Team/Enterprise/
Pro/Max subscription. Assumptions worth flagging explicitly, to the best of
the author's knowledge as of when this was written:
  - `query(prompt=..., options=ClaudeAgentOptions(...))` is an async
    generator yielding message objects; text output arrives as
    `AssistantMessage` objects whose `.content` is a list of blocks, with
    `TextBlock` blocks carrying `.text`.
  - Custom tools are defined with the `@tool(name, description, schema)`
    decorator (schema: a dict of {param_name: python_type}) and exposed to
    Claude by wrapping them in `create_sdk_mcp_server(name=..., version=...,
    tools=[...])`, then listing that server under `ClaudeAgentOptions(
    mcp_servers={"<key>": server})`. The tool name Claude actually sees, and
    what you list in `allowed_tools`, is `mcp__<key>__<tool_name>`.
  - A `@tool`-decorated function returns
    `{"content": [{"type": "text", "text": "..."}]}`.
  - `ClaudeAgentOptions(permission_mode=...)` gates whether a requested tool
    call runs automatically or waits for approval; a non-interactive script
    needs a mode that doesn't block on a human, e.g. "acceptEdits".
If any of these have changed, code.claude.com's Agent SDK docs are
authoritative, not this file - this SDK moves fast.
"""

import asyncio
import json

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    TextBlock,
    create_sdk_mcp_server,
    query,
    tool,
)

SAMPLE_TEXTS = [
    {
        "id": "t1",
        "text": (
            "The app crashed twice today while I was checking out. Pretty "
            "annoying but I still like the product overall."
        ),
    },
    {
        "id": "t2",
        "text": (
            "I want every last bit of my data deleted from your systems "
            "immediately, and I'm going to talk to a lawyer about how you "
            "handled my last order."
        ),
    },
    {
        "id": "t3",
        "text": (
            "Great customer support call yesterday, the rep fixed my "
            "billing issue in five minutes."
        ),
    },
]


async def ask_claude(prompt: str, system_prompt: str | None = None) -> str:
    """One-shot helper: run query() to completion and return the final
    assistant text. No tools involved, so this is one round trip - the
    Agent-SDK equivalent of a single client.messages.create() call."""
    options = ClaudeAgentOptions(system_prompt=system_prompt) if system_prompt else ClaudeAgentOptions()
    chunks = []
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    chunks.append(block.text)
    return "".join(chunks).strip()


# ---------------------------------------------------------------------------
# PART A: WORKFLOW
# ---------------------------------------------------------------------------

async def extract_structured_data(text: str) -> dict:
    prompt = (
        "Extract structured data from this piece of customer feedback.\n\n"
        f"Feedback: {text}\n\n"
        'Respond with ONLY a valid JSON object of the form '
        '{"sentiment": "positive"|"negative"|"neutral", "topic": "<short topic, '
        'a few words>"}. No other text, no markdown code fences.'
    )
    raw = await ask_claude(prompt)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Deterministic fallback - this is exactly the kind of guaranteed
        # error handling a fixed workflow path gives you: if extraction
        # fails, we know precisely what happens next, every time.
        return {"sentiment": "unknown", "topic": "unknown", "parse_error": raw}


# Approach (a): pure Python keyword check - zero extra LLM calls, fully
# deterministic and auditable. This is the version implemented here; the
# exercise docstring's approach (b) - a second narrow yes/no query() call -
# is an equally valid workflow (still a fixed pipeline step) and is left as
# a variant worth trying.
_REVIEW_KEYWORDS = (
    "lawyer", "legal", "sue", "lawsuit", "attorney",
    "delete my data", "delete my account", "delete all my data",
    "unsafe", "safety", "dangerous", "hurt me", "injury",
)


def needs_human_review_workflow(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in _REVIEW_KEYWORDS)


async def run_workflow(samples: list[dict]) -> list[dict]:
    results = []
    for sample in samples:
        data = await extract_structured_data(sample["text"])
        data["id"] = sample["id"]
        data["needs_human_review"] = needs_human_review_workflow(sample["text"])
        results.append(data)
    return results


# ---------------------------------------------------------------------------
# PART B: AGENT
# ---------------------------------------------------------------------------

FLAGGED: list[dict] = []


@tool(
    "flag_for_review",
    (
        "Flag a piece of customer feedback for human review. Call this only "
        "for feedback that mentions safety concerns, legal threats, or a "
        "request to delete the user's account/data. Do not call it for "
        "routine complaints, praise, or neutral feedback."
    ),
    {"text_id": str, "reason": str},
)
async def flag_for_review(args):
    # In a real system this might write to a ticketing queue; here we just
    # record it (module-level FLAGGED list) so we can inspect what the
    # agent decided, entirely from its own tool-call choices.
    FLAGGED.append({"id": args["text_id"], "reason": args["reason"]})
    return {
        "content": [
            {
                "type": "text",
                "text": f"Flagged {args['text_id']} for human review: {args['reason']}",
            }
        ]
    }


async def run_agent(samples: list[dict]) -> str:
    texts_block = "\n".join(f"[{s['id']}] {s['text']}" for s in samples)
    user_prompt = (
        "Here are pieces of customer feedback:\n\n"
        f"{texts_block}\n\n"
        "For each one, decide whether it needs human review (safety "
        "concerns, legal threats, or a request to delete account/data). "
        "Call flag_for_review for each one that does - you may call it "
        "zero, one, or multiple times, however many texts actually warrant "
        "it. When you have considered every text, respond with a short "
        "final summary of what you flagged and why, and do not call any "
        "more tools."
    )

    review_server = create_sdk_mcp_server(
        name="review", version="1.0.0", tools=[flag_for_review]
    )
    options = ClaudeAgentOptions(
        mcp_servers={"review": review_server},
        allowed_tools=["mcp__review__flag_for_review"],
        # Non-interactive script - don't block waiting for a human to
        # approve each tool call. Verify the current permission-mode names
        # against code.claude.com; this one is correct as of writing.
        permission_mode="acceptEdits",
    )

    chunks = []
    async for message in query(prompt=user_prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    chunks.append(block.text)
    # Note everything above this line is the *entire* agent loop: no
    # stop_reason check, no manual tool_result construction, no retry loop.
    # The SDK ran Claude's decide -> call flag_for_review -> see result ->
    # decide again cycle internally, for as many iterations as Claude
    # actually needed (zero to three flag_for_review calls, in this case).
    return "".join(chunks).strip()


async def main():
    print("=== PART A: WORKFLOW ===")
    workflow_results = await run_workflow(SAMPLE_TEXTS)
    print(json.dumps(workflow_results, indent=2))
    # Expected shape: 3 results, always with a "needs_human_review" key.
    # t2 should come back True (legal threat + deletion request); t1 and t3
    # should come back False. This is deterministic given the keyword list.

    print("\n=== PART B: AGENT ===")
    summary = await run_agent(SAMPLE_TEXTS)
    print("Agent summary:", summary)
    print("Flagged by the agent:", json.dumps(FLAGGED, indent=2))
    # Expected: FLAGGED contains exactly one entry, for t2. Note FLAGGED is
    # built entirely from Claude's own tool-call decisions - the Python code
    # never told it which texts qualify, unlike Part A's keyword list.

    print(
        "\n=== ANSWER (reference discussion) ===\n"
        "For THIS task - three short, low-stakes texts and a narrow, "
        "well-defined flagging rule - the workflow (Part A) is the better "
        "production choice: it's cheaper (1 LLM call per text instead of a "
        "multi-turn tool loop), fully deterministic and auditable (you can "
        "point to the exact keyword list that triggered a flag), and easy "
        "to unit test without hitting the API at all. The agent's extra "
        "flexibility buys nothing here because the flagging rule is fully "
        "specifiable in advance.\n"
        "The agent (Part B) approach would earn its keep on a task where "
        "the review criteria are too open-ended or context-dependent to "
        "reduce to a keyword list or a single yes/no question - e.g. an "
        "agent triaging free-form support tickets that might ALSO need to "
        "look up the customer's account history via another tool before "
        "deciding, take a variable number of investigative steps per "
        "ticket, and decide on its own when it has enough information to "
        "stop. There, the step count and sequence genuinely can't be fixed "
        "in advance, which is exactly the condition under which an agent's "
        "model-controlled loop beats a fixed pipeline."
    )


if __name__ == "__main__":
    asyncio.run(main())
