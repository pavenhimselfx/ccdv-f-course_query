"""
SOLUTION — ex3_structured_output_validation.py — CCDV-F Module 06

Reference implementation with inline explanations. Compare against your own
attempt in exercises/ex3_structured_output_validation.py after a genuine
attempt of your own. See that file's docstring for full exercise context.
"""

import json
import os
import sys

try:
    import anthropic
except ImportError:
    anthropic = None


MODEL = "claude-sonnet-4-5"  # verify current model name/availability at docs.claude.com

ALLOWED_CATEGORIES = {"billing", "technical", "feature_request", "account", "other"}
ALLOWED_URGENCY = {"low", "medium", "high"}

SAMPLE_TICKET = """
Subject: App crashes on login
Hi, every time I try to log in on my Android phone the app just closes.
This started after the last update. I use this app for work every day so
this is pretty urgent, please help ASAP.
- Jordan K.
"""


# ---------------------------------------------------------------------------
# Part 1: Tool definition. Declaring the schema STRUCTURALLY here (rather
# than only describing it in prose) is what makes tool-use a stronger
# forcing function than "please output JSON like this" -- the shape is part
# of the API call itself, not just a hopeful instruction.
# ---------------------------------------------------------------------------

TICKET_TOOL = {
    "name": "ticket_info",
    "description": "Record structured information extracted from a customer support ticket.",
    "input_schema": {
        "type": "object",
        "properties": {
            "customer_name": {
                "type": "string",
                "description": "The customer's name as it appears in the ticket, or 'unknown' if not stated.",
            },
            "issue_category": {
                "type": "string",
                "enum": sorted(ALLOWED_CATEGORIES),
                "description": "The best-fit category for this ticket's issue.",
            },
            "urgency": {
                "type": "string",
                "enum": sorted(ALLOWED_URGENCY),
                "description": "How urgent the customer's issue appears to be.",
            },
            "requested_action": {
                "type": "string",
                "description": "What the customer is asking to have done, or '' if nothing specific was requested.",
            },
        },
        "required": ["customer_name", "issue_category", "urgency", "requested_action"],
    },
}


# ---------------------------------------------------------------------------
# Part 2: Extraction via forced tool-use.
# ---------------------------------------------------------------------------

def extract_structured_output(client, ticket_text: str) -> dict:
    """
    tool_choice={"type": "tool", "name": "ticket_info"} FORCES Claude to
    call this specific tool rather than leaving it free to respond with
    plain text instead (the default tool_choice, "auto", would let the
    model choose not to call any tool at all -- wrong behavior here, since
    we always want structured output back). Verify this exact tool_choice
    syntax against current docs.claude.com; it has been stable but SDKs do
    evolve.
    """
    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        tools=[TICKET_TOOL],
        tool_choice={"type": "tool", "name": "ticket_info"},
        messages=[
            {
                "role": "user",
                "content": f"Extract structured ticket info from this support ticket:\n\n{ticket_text}",
            }
        ],
    )

    # Defensive: don't assume content[0] is the tool_use block. Scan for it
    # explicitly, and fail loudly and specifically if it's missing, rather
    # than letting an IndexError or AttributeError surface somewhere else
    # with a confusing message.
    for block in response.content:
        if block.type == "tool_use":
            return block.input

    raise RuntimeError(
        f"No tool_use block found in Claude's response (stop_reason="
        f"{response.stop_reason!r}) -- expected a forced 'ticket_info' call."
    )


# ---------------------------------------------------------------------------
# Part 3: Defensive validation (manual version).
#
# OPTIONAL PYDANTIC ALTERNATIVE (equally valid -- shown here as reference):
#
#     from pydantic import BaseModel, ValidationError
#     from typing import Literal
#
#     class TicketInfo(BaseModel):
#         customer_name: str
#         issue_category: Literal["billing", "technical", "feature_request",
#                                  "account", "other"]
#         urgency: Literal["low", "medium", "high"]
#         requested_action: str
#
#     def validate_ticket_info(data: dict) -> dict:
#         try:
#             return TicketInfo.model_validate(data).model_dump()
#         except ValidationError as e:
#             raise ValueError(str(e)) from e
#
# Both approaches implement the same principle: check the shape explicitly
# before trusting it, and fail with a specific, debuggable message. The
# manual version below has zero extra dependencies, which is why it's the
# primary implementation in this solution file.
# ---------------------------------------------------------------------------

def validate_ticket_info(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError(f"expected a dict, got {type(data).__name__}: {data!r}")

    required_fields = ["customer_name", "issue_category", "urgency", "requested_action"]
    for field in required_fields:
        if field not in data:
            raise ValueError(f"missing required field {field!r} in {data!r}")

    customer_name = data["customer_name"]
    if not isinstance(customer_name, str):
        raise ValueError(f"customer_name must be a string, got {type(customer_name).__name__}: {customer_name!r}")

    requested_action = data["requested_action"]
    if not isinstance(requested_action, str):
        raise ValueError(f"requested_action must be a string, got {type(requested_action).__name__}: {requested_action!r}")

    issue_category = data["issue_category"]
    if not isinstance(issue_category, str) or issue_category not in ALLOWED_CATEGORIES:
        raise ValueError(f"issue_category {issue_category!r} is not one of {sorted(ALLOWED_CATEGORIES)}")

    urgency = data["urgency"]
    if not isinstance(urgency, str) or urgency not in ALLOWED_URGENCY:
        raise ValueError(f"urgency {urgency!r} is not one of {sorted(ALLOWED_URGENCY)}")

    # Return exactly the expected keys -- don't pass through any extra keys
    # the model might have added, and don't rely on dict ordering/equality
    # elsewhere in the pipeline depending on what's present.
    return {
        "customer_name": customer_name,
        "issue_category": issue_category,
        "urgency": urgency,
        "requested_action": requested_action,
    }


# ---------------------------------------------------------------------------
# Part 4: Prove the validator catches bad input.
# ---------------------------------------------------------------------------

MOCK_RESPONSES = {
    "valid": {
        "customer_name": "Jordan K.",
        "issue_category": "technical",
        "urgency": "high",
        "requested_action": "fix the login crash",
    },
    "missing_field": {
        "customer_name": "Jordan K.",
        "issue_category": "technical",
        "requested_action": "fix the login crash",
    },
    "wrong_type": {
        "customer_name": "Jordan K.",
        "issue_category": "technical",
        "urgency": 3,
        "requested_action": "fix the login crash",
    },
    "invalid_enum": {
        "customer_name": "Jordan K.",
        "issue_category": "urgent_please_help",
        "urgency": "high",
        "requested_action": "fix the login crash",
    },
    "wrong_container_type": {
        "customer_name": None,
    },
}
TRUNCATED_JSON_STRING = '{"customer_name": "Jordan K.", "issue_category": "tech'


def run_validation_tests() -> bool:
    all_passed = True

    print("--- validate_ticket_info() tests ---")
    for name, mock in MOCK_RESPONSES.items():
        should_be_valid = (name == "valid")
        try:
            result = validate_ticket_info(mock)
            passed = should_be_valid
            outcome = f"ACCEPTED -> {result}"
        except ValueError as e:
            passed = not should_be_valid
            outcome = f"REJECTED ({e})"

        status = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"  [{status}] case={name!r}: {outcome}")

    print("\n--- defensive json.loads() test (truncated response) ---")
    try:
        json.loads(TRUNCATED_JSON_STRING)
        print("  [FAIL] truncated JSON parsed without error -- that shouldn't happen")
        all_passed = False
    except json.JSONDecodeError as e:
        print(f"  [PASS] truncated JSON correctly raised json.JSONDecodeError: {e}")

    return all_passed


def main() -> None:
    tests_ok = run_validation_tests()
    print(f"\nAll validation tests passed: {tests_ok}")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or anthropic is None:
        print("\nANTHROPIC_API_KEY not set (or `anthropic` not installed) -- "
              "skipping the live extraction call.")
        sys.exit(0 if tests_ok else 1)

    print("\n--- live extraction against a real ticket ---")
    client = anthropic.Anthropic(api_key=api_key)
    try:
        raw = extract_structured_output(client, SAMPLE_TICKET)
        print(f"Raw tool input from Claude: {raw}")
        validated = validate_ticket_info(raw)
        print(f"Validated: {validated}")
    except (RuntimeError, ValueError) as e:
        # This is the same defensive-parsing posture as the mock tests
        # above, now exercised against a REAL model response: even with
        # forced tool-use, we still validate before trusting the result,
        # and we still catch and report failures instead of crashing.
        print(f"Extraction/validation failed: {e}")


if __name__ == "__main__":
    main()
