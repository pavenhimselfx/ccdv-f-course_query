"""
solutions/ex2_trace_analysis.py — CCDV-F course, Module 04 (Eval, Testing, and Debugging)

Reference analysis for exercises/ex2_trace_analysis.py. Read the exercise file and form
your own answer FIRST -- the value of this exercise is in doing the diagnostic walk
yourself, not in reading someone else's conclusion.

This file duplicates the same trace inline (rather than importing across the
exercises/solutions directory split, which would require extra packaging/sys.path setup
just to run a standalone script) so you can re-print it alongside the analysis. It's
identical to the trace in exercises/ex2_trace_analysis.py.
"""

import json

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
            {"type": "text", "text": "Sure, let me look that up for you."},
            {
                "type": "tool_use",
                "id": "toolu_01",
                "name": "get_order_status",
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
    print("=" * 70)


"""
ANALYSIS (reference answer)

  1. What did the FINAL (wrong) output depend on? Trace it back.

     The final assistant text (turn 4) is built entirely from the tool_result in
     turn 3, which in turn is entirely determined by the `order_id` argument the
     assistant chose in the tool_use call in turn 2. So the dependency chain is:
     turn 4 (final answer) <- turn 3 (tool_result) <- turn 2's tool_use `input.order_id`
     <- turn 1 (user's message). Walking backward, the first place to check is turn 2's
     argument value.

  2. Replay the exact request/arguments actually sent at the point of failure. Was the
     input the model acted on correct and complete?

     Turn 1, the actual user message, is unambiguous: "order #A-4471". That is the
     complete, correct input available to the model at the moment it made the tool
     call in turn 2. Nothing upstream of turn 2 was missing, truncated, or wrong.

  3. Was the tool_use call's argument value actually justified by the conversation so
     far, or does it look invented / different from what the user said?

     It does NOT match. The user said "A-4471"; the tool call in turn 2 used
     `"order_id": "A-4417"` -- the last two digits are transposed (71 -> 17). There is
     no other order number anywhere earlier in the conversation that could explain this
     value; it isn't a copy-paste of some other visible ID. Given a correct, complete
     input, the model produced an argument that doesn't match it.

  4. Was the tool_result correctly relayed back into the conversation (i.e., does it
     match what the tool call actually asked for)?

     Yes. Turn 3's tool_result is for order A-4417 (matching GROUND_TRUTH_BACKEND's
     "A-4417" entry exactly: delivered, 2026-08-19, Wireless Mouse) and correctly
     answers the tool_use call's actual argument. The tool and the plumbing around it
     behaved correctly given what they were asked -- they just were asked about the
     wrong order.

  5. Given steps 1-4: which numbered TURN introduced the failure? Quote the exact
     field/value that is wrong.

     Turn: 2
     Field/value: the tool_use block's `input.order_id`, value "A-4417", should have
     been "A-4471" to match the order number the user actually gave in turn 1.

  6. Is this an INTEGRATION-LAYER bug or a MODEL-OUTPUT issue? Justify your answer using
     the diagnostic questions above -- don't just assert it.

     MODEL-OUTPUT issue. Applying the README's diagnostic order:
       - Step 1 (was the exact input correct and complete?) -- yes, turn 1 clearly and
         unambiguously states "A-4471", and that's all the model needed.
       - Step 2 (does the tool schema/description invite this mistake?) -- there's no
         evidence of that here; nothing in the trace suggests an ambiguous schema, a
         misleading parameter description, or a few-shot example biasing toward
         "A-4417". (If you were debugging this for real, you'd want to go check the
         actual tool schema/system prompt for exactly that, per the checklist -- absence
         of evidence in this trace is not the same as proof, it's just what this
         exercise gives you to work with.)
       - Step 3 (was the tool_result faithfully relayed?) -- yes, turn 3 correctly
         answers the (wrong) argument it was actually given.
       - Step 4 (attribute to the model) -- with correct input, an unambiguous schema
         (as far as this trace shows), and faithful tool-result relay, the wrong
         argument value is a genuine model reasoning slip: a digit transposition typo
         when copying the order number from the user's message into the tool call.
         This is the "hallucinated/incorrect tool argument" failure mode named in the
         blueprint -- the model called the right tool, in the right shape, with a value
         that doesn't trace back to anything in its correct input.

     Also worth naming as a secondary, compounding issue: turn 4's text says
     "Order #A-4471 has already been delivered..." -- i.e. the model's FINAL reply cites
     the CORRECT order number (A-4471, matching what the user asked) while reporting
     data that actually came from a DIFFERENT order (A-4417's tool result). This makes
     the error harder for the customer to catch (the order number they see matches what
     they asked about) and is itself further evidence this is a model-output issue
     rather than a simple plumbing bug: nothing in the integration layer would explain
     why the displayed number and the underlying data source diverge like that -- that
     divergence is consistent with the model "smoothing over" its own earlier mistake
     rather than a code-level data-routing error.

  7. What is the one-line fix, and where does it belong (prompt/instructions, tool
     schema, application code, or "this is a real model limitation, add a guardrail")?

     Primary fix: application-code guardrail, not a prompt tweak alone. Since this is a
     genuine model slip (not an integration bug), prompting alone ("please be careful
     copying order numbers") reduces but does not reliably eliminate this class of
     error. The robust fix is a guardrail in the integration layer: after the tool
     returns, programmatically assert that `tool_result["order_id"] == ` the order_id
     the user actually referenced (extracted independently, e.g. via a regex/parse of
     the user's message, or by having the tool itself echo back and cross-checking
     before the model is allowed to present it as final). If they don't match, don't let
     the model's answer reach the customer -- re-prompt the model with the mismatch
     surfaced explicitly ("you looked up A-4417 but the customer asked about A-4471,
     please retry"), which is the "validate and re-prompt on malformed output" recovery
     pattern from this module's README, applied to a tool-argument mismatch instead of a
     JSON-schema mismatch.

     A secondary, complementary mitigation belongs in the prompt/instructions: explicitly
     instruct the model to double-check that the order_id in the tool_result matches the
     order_id the customer stated before writing its final reply. This won't guarantee
     the transposition never happens, but it gives the model a chance to self-correct,
     and costs nothing to add.
"""


if __name__ == "__main__":
    print_trace()
    print("\n" + "=" * 70)
    print("SOLUTION ANALYSIS SUMMARY")
    print("=" * 70)
    print(
        """
Failure introduced at: Turn 2 (assistant tool_use), input.order_id = "A-4417"
Should have been:      "A-4471" (matching the user's stated order number in Turn 1)

Classification: MODEL-OUTPUT issue (not integration-layer).
  - Turn 1's input to the model was correct and complete.
  - Turn 2's tool_result was correctly relayed for whatever order_id was actually asked.
  - Nothing in the surrounding code mangled data going in or coming out --
    the model itself produced an argument value that doesn't trace back to
    anything in its correct context (a digit-transposition-style hallucinated
    tool argument), then compounded it by citing the CORRECT order number in
    its final text while reporting the WRONG order's data.

Fix: an application-layer guardrail that cross-checks the tool_result's order_id
against the order_id the user actually stated before allowing a final reply to
go out, with a bounded re-prompt-on-mismatch loop -- plus a supporting prompt
instruction asking the model to self-verify the same thing.
"""
    )
