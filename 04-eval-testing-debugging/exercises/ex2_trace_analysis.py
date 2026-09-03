"""
ex2_trace_analysis.py — CCDV-F course, Module 04 (Eval, Testing, and Debugging)

GOAL
----
Practice reading a multi-step agent trace to find WHERE a failure was introduced, and
practice the specific skill of deciding whether the root cause is an INTEGRATION-LAYER
bug (something wrong in the surrounding code: schema, data plumbing, response handling)
or a genuine MODEL-OUTPUT issue (the model reasoned/responded incorrectly given correct,
complete inputs).

This exercise needs NO API key and makes NO network calls -- it is a pure reading and
reasoning exercise. The "trace" below is a pre-written, deliberately-buggy transcript of
an agent that was asked to look up a customer's order status and reply to them. Read it
turn by turn, then fill in the analysis at the bottom.

HOW TO WORK THROUGH THIS
-------------------------
1. Run this script (`python ex2_trace_analysis.py`) -- it just pretty-prints the trace
   turn by turn so you can read it in order.
2. Read every turn carefully, including the exact tool_use arguments and exact
   tool_result contents -- the bug is subtle and lives in a specific field.
3. Fill in ANALYSIS below: which step introduced the failure, is it an integration-layer
   bug or a model-output issue, and why -- walking through the diagnostic checklist.
4. Compare against solutions/ex2_trace_analysis.py once you've formed your own answer.
   Don't peek first -- the value of this exercise is in doing the diagnostic walk
   yourself.
"""

import json

# ---------------------------------------------------------------------------
# The trace: a sequence of turns for one agent run.
#
# Scenario: a support agent app lets Claude look up a customer's order via a
# `get_order_status` tool, then reply to the customer. The customer asked about
# order #A-4471. The final reply the customer received was WRONG -- it described a
# different order. Your job is to find out why.
# ---------------------------------------------------------------------------
TRACE = [
    {
        "turn": 1,
        "role": "user",
        "content": "Hi, can you tell me the status of my order #A-4471? I need to know if it's shipped yet.",
    },
    {
        "turn": 2,
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "Sure, let me look that up for you.",
            },
            {
                "type": "tool_use",
                "id": "toolu_01",
                "name": "get_order_status",
                # Note the exact order ID used here vs. what the customer asked about.
                "input": {"order_id": "A-4417"},
            },
        ],
    },
    {
        "turn": 3,
        "role": "tool_result",
        "tool_use_id": "toolu_01",
        "content": json.dumps(
            {
                "order_id": "A-4417",
                "status": "delivered",
                "delivered_on": "2026-08-19",
                "items": ["Wireless Mouse"],
            }
        ),
    },
    {
        "turn": 4,
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": (
                    "Good news! Order #A-4471 has already been delivered on "
                    "2026-08-19. It included: Wireless Mouse. Let me know if you "
                    "need anything else!"
                ),
            }
        ],
    },
]

# What the customer's ACTUAL order #A-4471 looked like in the backend at the time of
# this conversation (ground truth, for your reference -- the agent never saw this
# directly, only whatever the tool returned for whatever order_id it was called with):
GROUND_TRUTH_BACKEND = {
    "A-4471": {"status": "in_transit", "expected_delivery": "2026-08-28", "items": ["USB-C Hub"]},
    "A-4417": {"status": "delivered", "delivered_on": "2026-08-19", "items": ["Wireless Mouse"]},
}


def print_trace() -> None:
    print("=" * 70)
    print("AGENT TRACE — customer order status lookup")
    print("=" * 70)
    for turn in TRACE:
        print(f"\n[Turn {turn['turn']}] role={turn['role']}")
        if turn["role"] == "assistant" and isinstance(turn["content"], list):
            for block in turn["content"]:
                if block["type"] == "text":
                    print(f"  text: {block['text']}")
                elif block["type"] == "tool_use":
                    print(f"  tool_use: {block['name']}(id={block['id']})")
                    print(f"    input: {json.dumps(block['input'])}")
        elif turn["role"] == "tool_result":
            print(f"  tool_result (for {turn['tool_use_id']}): {turn['content']}")
        else:
            print(f"  content: {turn['content']}")

    print("\n" + "=" * 70)
    print("Ground truth backend state (for your reference only -- the agent never")
    print("sees this dict directly, only whatever get_order_status(order_id) returns):")
    print(json.dumps(GROUND_TRUTH_BACKEND, indent=2))
    print("=" * 70)


# ---------------------------------------------------------------------------
# ANALYSIS -- fill this in yourself before checking the solution.
# ---------------------------------------------------------------------------
"""
ANALYSIS (fill in each blank with your own answer)

Diagnostic checklist to work through, in order (see README.md section 3.1 for the full
explanation of each question):

  1. What did the FINAL (wrong) output depend on? Trace it back.
     Your answer:
       Turn 4's text depends directly on turn 3's tool_result (status "delivered",
       delivered_on "2026-08-19", items ["Wireless Mouse"]) -- which in turn depends
       on turn 2's tool_use call, which supplied order_id "A-4417".

  2. Replay the exact request/arguments actually sent at the point of failure. Was the
     input the model acted on correct and complete?
     Your answer:
       No. The tool_use call in turn 2 sent {"order_id": "A-4417"}. The customer asked
       about "#A-4471" in turn 1. "A-4417" is a digit transposition of "A-4471" (the
       last two digits, 7 and 1, are swapped) -- a different, but validly-formatted,
       order ID that happens to exist in the backend.

  3. Was the tool_use call's argument value actually justified by the conversation so
     far, or does it look invented / different from what the user said?
     Your answer:
       It does not match what the user said. Nothing in turn 1 mentions "A-4417" --
       the user typed "A-4471" explicitly. This looks like a transcription slip by the
       model when copying the order ID out of the user's message into the tool call
       arguments, not a value derived from any other legitimate source.

  4. Was the tool_result correctly relayed back into the conversation (i.e., does it
     match what the tool call actually asked for)?
     Your answer:
       Yes. Given the (wrong) order_id "A-4417" that was actually requested, the
       tool_result correctly matches GROUND_TRUTH_BACKEND for "A-4417" (delivered,
       2026-08-19, Wireless Mouse). The tool and the plumbing around it did exactly
       what they were asked to do -- they answered the wrong question faithfully, but
       they answered the question they were actually given correctly.

  5. Given steps 1-4: which numbered TURN introduced the failure? Quote the exact
     field/value that is wrong.
     Your answer:
       Turn: 2
       Field/value: tool_use.input.order_id = "A-4417" (should have been "A-4471")

  6. Is this an INTEGRATION-LAYER bug or a MODEL-OUTPUT issue? Justify your answer using
     the diagnostic questions above -- don't just assert it.
     Your answer:
       MODEL-OUTPUT issue. The tool schema, the tool's own logic, and the
       tool_result-to-conversation plumbing are all working correctly (step 4) -- there
       is no integration bug to point to anywhere in the surrounding code. The failure
       is that the model itself generated an incorrect argument value (step 2/3): it
       transposed two digits when copying the order ID from the user's message into the
       tool call, and then compounded that error in turn 4 by asserting the customer's
       original, correctly-remembered order number ("#A-4471") while actually reporting
       a different order's data -- i.e., it never cross-checked that the tool_result's
       own order_id field ("A-4417") matched the number it was about to tell the
       customer. Both lapses are things the model generated, not something broken in
       the code that carried its output around.

  7. What is the one-line fix, and where does it belong (prompt/instructions, tool
     schema, application code, or "this is a real model limitation, add a guardrail")?
     Your answer:
       This is a real model limitation -- add a guardrail in application code, since a
       transposed-but-still-valid ID can't be caught by tighter prompt wording alone
       (the model already "knows" the right ID conceptually; it just mistyped it) or by
       a stricter tool schema (a regex like `A-\\d{4}` still matches "A-4417" just
       fine). Concretely: after receiving each tool_result, deterministically assert
       that tool_result["order_id"] equals the order_id that was actually sent in the
       matching tool_use call (a same-turn consistency check, cheap and fully
       reliable), AND separately verify the order number the model is about to state in
       its reply matches the order_id it just looked up before letting that reply go to
       the customer. Neither check requires trusting the model to get it right --
       they're deterministic string comparisons in the code that owns the tool loop.
"""


if __name__ == "__main__":
    print_trace()
    print(
        "\nNow fill in the ANALYSIS block in this file's source, then compare against "
        "solutions/ex2_trace_analysis.py."
    )
