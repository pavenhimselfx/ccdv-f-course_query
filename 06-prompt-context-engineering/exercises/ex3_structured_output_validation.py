"""
ex3_structured_output_validation.py — CCDV-F Module 06, Exercise 3

Skill: Output Handling (2.6%)

WHAT YOU'RE BUILDING
---------------------
A pipeline that asks Claude to extract structured data from a support ticket
using tool-use as a forcing function (README section 3.1), then validates
and defensively parses the result (sections 3.2 and 3.3) — and, critically,
you'll deliberately feed the validation layer BAD mock data (missing field,
wrong type, invalid enum value, truncated JSON) to prove it actually catches
problems rather than trusting output blindly. That last part is section 3.4
made concrete: don't just build the happy path and assume it's robust —
verify it rejects what it should reject.

Target schema (what a "ticket_info" tool call's input should look like):
    {
        "customer_name": str,               # required
        "issue_category": str,              # required, one of ALLOWED_CATEGORIES
        "urgency": str,                      # required, one of "low"/"medium"/"high"
        "requested_action": str,             # required (use "" if none stated)
    }

WHAT TO IMPLEMENT
-------------------
  1. TICKET_TOOL: a tool definition (dict) whose input_schema matches the
     schema above, to pass to client.messages.create(tools=[...]).
  2. extract_structured_output(client, ticket_text): call Claude with
     tool_choice forcing a call to TICKET_TOOL, and return the raw dict
     from the tool_use block's `.input` (do NOT validate here — that's a
     separate step, on purpose, so you can test validation independently).
  3. validate_ticket_info(data): defensively check `data` against the
     schema and return a clean, validated dict — or raise a ValueError with
     a clear, specific message if anything is wrong.
  4. A set of test cases (already partly written below) that feed
     validate_ticket_info() deliberately broken mock dicts and confirm each
     one is REJECTED, plus one valid mock that should be ACCEPTED.

You may implement validate_ticket_info() with plain manual checks, or with
`pydantic` if you have it installed (`pip install pydantic`) — both are
legitimate approaches and the solution file shows the manual version with a
pydantic alternative in a comment. The exam cares about the CONCEPT
(validate before use, fail loudly and specifically on bad shape), not which
particular library you use.

NO API KEY REQUIRED for parts 3 and 4 (validation logic and the malformed-
input tests are pure Python, no network calls). Part 2 (extract_structured_
output) needs a key to actually call Claude; if you don't have one, you can
still write the tool schema and the function body, and reason about what a
`tool_use` block would look like, then check against the solution.

HOW TO KNOW YOU'VE SUCCEEDED
------------------------------
Running this file prints a PASS/FAIL line for each test case in
run_validation_tests() — every deliberately-broken case should FAIL to
validate (validate_ticket_info raises), and the one valid case should PASS.
If an API key is set, it will also run a live extraction and validate that
real result too.

Run it with:
    python ex3_structured_output_validation.py
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
# Part 1: Tool definition (the schema, declared structurally).
# ---------------------------------------------------------------------------

# TODO: Define TICKET_TOOL as a dict with keys "name", "description", and
# "input_schema" (a JSON-schema-shaped dict: type "object", "properties" for
# each of the four fields above with their types, an "enum" list for
# issue_category and urgency, and "required" listing all four field names).
TICKET_TOOL = None  # TODO: replace with your tool definition


# ---------------------------------------------------------------------------
# Part 2: Extraction via forced tool-use.
# ---------------------------------------------------------------------------

def extract_structured_output(client, ticket_text: str) -> dict:
    """
    TODO: Call client.messages.create(...) with:
      - tools=[TICKET_TOOL]
      - tool_choice forcing TICKET_TOOL specifically (check current
        docs.claude.com syntax — as of this writing it's a dict like
        {"type": "tool", "name": "ticket_info"})
      - a user message containing ticket_text and an instruction to extract
        the ticket info

    Then find the tool_use content block in the response (a response can
    contain multiple content blocks; find the one with type == "tool_use")
    and return its `.input` dict directly, UNVALIDATED — validation is a
    deliberately separate step (see validate_ticket_info below), so the two
    concerns (getting structured output vs. confirming it's correct) stay
    independently testable.

    Raise a RuntimeError with a clear message if no tool_use block is found
    at all (defensive parsing: don't assume the model always complies).
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Part 3: Defensive validation.
# ---------------------------------------------------------------------------

def validate_ticket_info(data: dict) -> dict:
    """
    TODO: Validate `data` against the target schema. Must check:
      - `data` is actually a dict (not None, not a string, etc.)
      - All four required keys are present: customer_name, issue_category,
        urgency, requested_action
      - customer_name and requested_action are strings (requested_action
        may be an empty string, but must be a string, not None or missing)
      - issue_category is a string AND is one of ALLOWED_CATEGORIES
      - urgency is a string AND is one of ALLOWED_URGENCY

    On ANY violation, raise ValueError with a message specific enough to
    debug from (name which field, and what was wrong with it) — e.g.:
        raise ValueError(f"issue_category {data.get('issue_category')!r} "
                          f"is not one of {sorted(ALLOWED_CATEGORIES)}")

    If everything checks out, return a clean dict with exactly the four
    expected keys (defensive parsing also means not silently passing
    through extra/unexpected keys the model might have added).

    OPTIONAL alternative: implement this with a `pydantic.BaseModel`
    instead of manual checks (define a model with the four fields, using
    Literal[...] for issue_category/urgency, and call
    TicketInfo.model_validate(data) inside a try/except that re-raises as
    ValueError with the pydantic error's message). Either approach is fine.
    """
    raise NotImplementedError


# ---------------------------------------------------------------------------
# Part 4: Prove the validator actually catches bad input.
# This part is already structured for you — fill in validate_ticket_info
# above and these tests should pass as-is.
# ---------------------------------------------------------------------------

MOCK_RESPONSES = {
    "valid": {
        "customer_name": "Jordan K.",
        "issue_category": "technical",
        "urgency": "high",
        "requested_action": "fix the login crash",
    },
    "missing_field": {
        # missing "urgency" entirely -- simulates the model omitting a
        # required field
        "customer_name": "Jordan K.",
        "issue_category": "technical",
        "requested_action": "fix the login crash",
    },
    "wrong_type": {
        # urgency is a number instead of a string -- simulates a
        # malformed/unexpected type
        "customer_name": "Jordan K.",
        "issue_category": "technical",
        "urgency": 3,
        "requested_action": "fix the login crash",
    },
    "invalid_enum": {
        # issue_category is not one of the allowed values -- simulates the
        # model inventing a category that wasn't in the schema
        "customer_name": "Jordan K.",
        "issue_category": "urgent_please_help",
        "urgency": "high",
        "requested_action": "fix the login crash",
    },
    "wrong_container_type": {
        # not even a dict -- simulates a totally malformed / truncated
        # response that a naive `data["urgency"]` would crash ugly on
        "customer_name": None,
    },
}
# This mock simulates a raw string response that got truncated mid-JSON
# (e.g. the model hit max_tokens) -- used to test the json.loads() path
# separately from validate_ticket_info, since it's not even parseable yet.
TRUNCATED_JSON_STRING = '{"customer_name": "Jordan K.", "issue_category": "tech'


def run_validation_tests() -> bool:
    """Already implemented. Returns True iff every test behaved as expected."""
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
        except NotImplementedError:
            print("  validate_ticket_info is not implemented yet -- skipping tests.")
            return False

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
    if not tests_ok:
        print("Fix validate_ticket_info() until every case above shows PASS.")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or anthropic is None:
        print("\nANTHROPIC_API_KEY not set (or `anthropic` not installed) -- "
              "skipping the live extraction call. You can still complete this "
              "exercise via the mock-data tests above.")
        sys.exit(0 if tests_ok else 1)

    if TICKET_TOOL is None:
        print("\nTICKET_TOOL is not defined yet -- skipping the live extraction call.")
        sys.exit(0 if tests_ok else 1)

    print("\n--- live extraction against a real ticket ---")
    client = anthropic.Anthropic(api_key=api_key)
    try:
        raw = extract_structured_output(client, SAMPLE_TICKET)
        print(f"Raw tool input from Claude: {raw}")
        validated = validate_ticket_info(raw)
        print(f"Validated: {validated}")
    except NotImplementedError:
        print("extract_structured_output is not implemented yet.")
    except (RuntimeError, ValueError) as e:
        print(f"Extraction/validation failed: {e}")


if __name__ == "__main__":
    main()
