"""
SOLUTION - Exercise 1: Tool Design and Error Handling
========================================================
Domain 8 (Tools and MCPs) - Skill: Tool Implementation (4.4%)

See exercises/ex1_tool_design_and_error_handling.py for the full task
description, including why this exercise now runs on the Claude Agent SDK
(free under a Team/Enterprise Claude.ai subscription via
`CLAUDE_CODE_OAUTH_TOKEN`) instead of the raw `anthropic` package. This file
is a worked reference implementation - if your approach differs in small
ways (different phrasing in descriptions, slightly different success
payload shape) that's fine, as long as: (1) tool descriptions are specific
and document every parameter, and (2) every tool handler never lets a
backend exception escape, always converting it into a structured
`is_error` tool result instead.

INSTALL: pip install claude-agent-sdk

SDK CURRENCY WARNING (repeated from the exercise, because it matters): the
Claude Agent SDK is actively evolving. Imports, the exact shape of the
`@tool` decorator, and message types below are correct as of this writing -
verify against https://code.claude.com before relying on this beyond the
exercise.
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


# ---------------------------------------------------------------------------
# MOCK BACKEND (unchanged from the exercise)
# ---------------------------------------------------------------------------

MOCK_INVENTORY = {
    "SKU-100": 42,   # widgets
    "SKU-200": 3,    # gadgets (low stock, good for testing insufficient-stock)
    "SKU-300": 0,    # gizmos (out of stock)
}

MOCK_ORDERS = {}
_next_order_id = 1000


class InventoryError(Exception):
    """Raised by the mock backend for any inventory/order problem."""


def backend_lookup_inventory(sku: str) -> int:
    if sku not in MOCK_INVENTORY:
        raise InventoryError(f"Unknown SKU '{sku}'. No such item in inventory.")
    return MOCK_INVENTORY[sku]


def backend_create_order(sku: str, quantity: int, customer_email: str) -> dict:
    global _next_order_id

    if sku not in MOCK_INVENTORY:
        raise InventoryError(f"Unknown SKU '{sku}'. No such item in inventory.")
    if quantity <= 0:
        raise InventoryError("Quantity must be a positive integer.")
    available = MOCK_INVENTORY[sku]
    if quantity > available:
        raise InventoryError(
            f"Insufficient stock for '{sku}': requested {quantity}, "
            f"only {available} available."
        )

    MOCK_INVENTORY[sku] -= quantity
    order_id = f"ORD-{_next_order_id}"
    _next_order_id += 1
    MOCK_ORDERS[order_id] = {
        "order_id": order_id,
        "sku": sku,
        "quantity": quantity,
        "customer_email": customer_email,
        "status": "confirmed",
    }
    return MOCK_ORDERS[order_id]


def backend_get_order_status(order_id: str) -> dict:
    if order_id not in MOCK_ORDERS:
        raise InventoryError(f"Unknown order id '{order_id}'.")
    return MOCK_ORDERS[order_id]


# ---------------------------------------------------------------------------
# PART A (SOLVED): TOOLS (schema + handler + error handling)
# ---------------------------------------------------------------------------

@tool(
    "lookup_inventory",
    (
        "Look up the current number of units in stock for a single SKU in "
        "the warehouse inventory system. Use this whenever the user asks "
        "how many units of an item are available, or before creating an "
        "order if you want to check stock first. This is read-only and has "
        "no side effects. Returns an error if the SKU does not exist."
    ),
    {"sku": str},
)
async def lookup_inventory(args: dict) -> dict:
    try:
        count = backend_lookup_inventory(args["sku"])
        payload = {"sku": args["sku"], "in_stock": count}
        return {"content": [{"type": "text", "text": json.dumps(payload)}]}
    except InventoryError as e:
        # The expected, "business logic" error case: bad SKU. Convert it
        # into a readable message with is_error=True instead of letting the
        # exception propagate (README.md 1.4) - this is the SDK MCP tool
        # result's equivalent of the raw Messages API's
        # {"type": "tool_result", "is_error": True, ...} block.
        return {"content": [{"type": "text", "text": f"Error: {e}"}], "is_error": True}
    except Exception as e:  # noqa: BLE001 - deliberate broad safety net
        # Defensive catch-all: even a bug in this handler (e.g. a missing
        # key in args) should become a structured error, not a crashed
        # process. Claude can at least tell the user something went wrong.
        return {
            "content": [{"type": "text", "text": f"Error: unexpected error: {e}"}],
            "is_error": True,
        }


@tool(
    "create_order",
    (
        "Place a new order for a given SKU and quantity, shipped to the "
        "given customer email. This DECREMENTS the item's stock count and "
        "cannot be undone by this tool set, so only call it once you have "
        "a specific SKU, a specific positive quantity, and a specific "
        "customer email confirmed - do not guess any of these three "
        "values. Fails with a structured error if the SKU does not exist "
        "or if the requested quantity exceeds current stock; in that case, "
        "report the problem to the user rather than retrying with the same "
        "arguments."
    ),
    {"sku": str, "quantity": int, "customer_email": str},
)
async def create_order(args: dict) -> dict:
    try:
        order = backend_create_order(
            sku=args["sku"],
            quantity=args["quantity"],
            customer_email=args["customer_email"],
        )
        return {"content": [{"type": "text", "text": json.dumps(order)}]}
    except InventoryError as e:
        return {"content": [{"type": "text", "text": f"Error: {e}"}], "is_error": True}
    except Exception as e:  # noqa: BLE001
        return {
            "content": [{"type": "text", "text": f"Error: unexpected error: {e}"}],
            "is_error": True,
        }


@tool(
    "get_order_status",
    (
        "Look up the status and details of a previously created order by "
        "its order id. Use this to answer questions like 'what's the "
        "status of my order' or to confirm an order was placed "
        "successfully. Read-only, no side effects. Returns an error if the "
        "order id is not found (e.g. it was never created, or was "
        "mistyped)."
    ),
    {"order_id": str},
)
async def get_order_status(args: dict) -> dict:
    try:
        order = backend_get_order_status(args["order_id"])
        return {"content": [{"type": "text", "text": json.dumps(order)}]}
    except InventoryError as e:
        return {"content": [{"type": "text", "text": f"Error: {e}"}], "is_error": True}
    except Exception as e:  # noqa: BLE001
        return {
            "content": [{"type": "text", "text": f"Error: unexpected error: {e}"}],
            "is_error": True,
        }


# ---------------------------------------------------------------------------
# PART B (SOLVED): SDK MCP SERVER + QUERY WIRING
# ---------------------------------------------------------------------------

warehouse_server = create_sdk_mcp_server(
    name="warehouse",
    version="1.0.0",
    tools=[lookup_inventory, create_order, get_order_status],
)

options = ClaudeAgentOptions(
    mcp_servers={"warehouse": warehouse_server},
    allowed_tools=[
        "mcp__warehouse__lookup_inventory",
        "mcp__warehouse__create_order",
        "mcp__warehouse__get_order_status",
    ],
)


async def run_agent(user_message: str) -> str:
    """Run one query against the warehouse tools and return Claude's final
    text answer. Notice there's no hand-rolled tool_use/tool_result loop
    here (contrast with the pre-rework version of this exercise) - query()
    dispatches every tool call internally and streams back everything that
    happened, including intermediate tool calls/results, as messages we
    simply observe."""
    final_text = ""
    async for message in query(prompt=user_message, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    final_text = block.text
    return final_text


# ---------------------------------------------------------------------------
# PART C: SCENARIOS
# ---------------------------------------------------------------------------

SCENARIOS = [
    "How many units of SKU-100 do we have in stock?",
    # EXPECTED: Claude calls lookup_inventory(sku="SKU-100"), gets back
    # {"sku": "SKU-100", "in_stock": 42}, and reports "42 units in stock"
    # in some phrasing. No error path.
    "Please order 50 units of SKU-200 for customer alice@example.com.",
    # EXPECTED: Claude calls create_order(sku="SKU-200", quantity=50,
    # customer_email="alice@example.com"). SKU-200 only has 3 units, so
    # backend_create_order raises InventoryError("Insufficient stock for
    # 'SKU-200': requested 50, only 3 available."). The create_order
    # handler catches it and returns {"content": [...], "is_error": True}.
    # Claude's final answer should explain that only 3 units are available
    # and ask whether to order 3 instead, or otherwise handle the shortfall
    # gracefully - NOT crash, and NOT falsely claim the order succeeded.
    "What's the status of order ORD-9999?",
    # EXPECTED: Claude calls get_order_status(order_id="ORD-9999"). This id
    # was never created (MOCK_ORDERS starts empty and only gets entries
    # from successful create_order calls), so backend_get_order_status
    # raises InventoryError("Unknown order id 'ORD-9999'."). Claude's final
    # answer should tell the user the order id wasn't found and perhaps
    # ask them to double check it, rather than fabricating order details.
]


async def main():
    for prompt in SCENARIOS:
        print(f"\n=== USER: {prompt} ===")
        answer = await run_agent(prompt)
        print("CLAUDE:", answer)

    print(
        "\n=== ANSWER ===\n"
        "For the insufficient-stock scenario, Claude's final answer (given "
        "the structured tool result with is_error=True and text like "
        "\"Error: Insufficient stock for 'SKU-200': requested 50, only 3 "
        "available.\") typically explains that only 3 units are in stock "
        "and offers to place an order for 3 instead, or asks the user how "
        "they'd like to proceed. This works because the error text and the "
        "is_error flag both made it into Claude's context as ordinary "
        "conversation data - Claude reasons over it exactly like it would "
        "any other tool result, whether that result came from a raw "
        "Messages API tool_result block or, as here, an SDK MCP tool "
        "result.\n\n"
        "If the create_order handler had NOT caught the InventoryError, "
        "the exception would have propagated up out of the SDK's internal "
        "dispatch and (depending on exactly where it surfaces) either "
        "crashed the query() run or shown up to Claude as an opaque "
        "failure with no useful detail - not the specific, readable "
        "message the try/except produces. Either way, the end user loses "
        "the graceful degradation: no explanation of *why* the order "
        "failed, no offer to adjust the quantity - just a broken "
        "interaction. Claude never gets a chance to react usefully, "
        "because from Claude's point of view the tool call didn't return "
        "the information it needed to reason about what went wrong."
    )


if __name__ == "__main__":
    asyncio.run(main())
