"""
Exercise 2: A Minimal Hand-Rolled Tool-Use Loop
=================================================
Domain 1 (Agents and Workflows) - Skill: Agent Construction with Claude (5.3%)

WHY THIS EXERCISE STILL USES THE RAW API (DELIBERATELY, NOT AN OVERSIGHT)
---------------------------------------------------------------------------
Exercises 1 and 3 in this domain were reworked to run on the Claude Agent
SDK, authenticated against a Claude.ai subscription, so they run free for
anyone with a Team/Enterprise/Pro/Max plan (see 00-setup/README.md section
1). This exercise was deliberately left on the raw `anthropic` Messages API
package instead, and still needs a metered Console API key to run live
(00-setup/README.md sections 2-3) - here's why that's a considered choice,
not an inconsistency.

This exercise's entire pedagogical point is hand-rolling the raw tool-use
loop yourself: seeing a `tool_use` content block arrive, dispatching it to
your own Python function, constructing a `tool_result` block by hand, and
deciding when `stop_reason` means "done." That protocol-level mechanic -
not just "agents can use tools" but the actual message shapes and control
flow that make tool use work - is itself exam-tested content (this skill's
"custom agent loops and harnesses," and Domain 8's tool-use/function-calling
mechanics). Building it through the Agent SDK instead would abstract away
exactly the thing this exercise exists to teach: you'd never see a
`tool_use` block, never touch `stop_reason`, never build a `tool_result` by
hand - which is precisely what you want in production (that's why Exercises
1 and 3 now do exactly that), but precisely what you don't want while you're
still building the underlying intuition.

Before you reach for the Claude Agent SDK (or LangGraph, or Strands, or
PydanticAI), you should understand what those tools are actually doing
underneath, because it's a surprisingly small and learnable amount of
machinery: send messages + tool schemas to the Messages API, notice when
Claude asks to use a tool, run the tool yourself, hand the result back, and
repeat. Every agent framework you'll ever use is a more polished, more
guarded version of exactly this loop. Build it once by hand here so the SDK
elsewhere in this course reads as "the same loop, with conveniences and
guardrails added" rather than as unfamiliar magic. For a direct point of
comparison, look at `run_agent()` in `ex1_workflow_vs_agent.py` and the
subagent calls in `ex3_manager_subagent_pattern.py` (both now Agent-SDK
based) once you've finished this file - same underlying loop, now with the
SDK's `@tool`/`create_sdk_mcp_server`/`query()` machinery running the
mechanics for you instead of the `while` loop you're about to write by hand
below.

THE TASK
--------
Build a tiny "unit conversion assistant" agent with two tools:

  1. convert_temperature(value: float, from_unit: str, to_unit: str) -> float
     Converts between "celsius" and "fahrenheit".

  2. calculate(expression: str) -> float
     Evaluates a simple arithmetic expression (use a SAFE eval - see the
     TODO below, do not use bare eval() on untrusted input in real code).

Then ask it a question that requires BOTH tools in sequence, e.g.:
  "The recipe says to preheat the oven to 220 celsius. What is that in
   fahrenheit, and if I need to fit 3 batches at that temperature and each
   batch takes 12 minutes, how many total minutes of oven time is that?"

Claude should: call convert_temperature once, then call calculate once
(using the converted value or independently for the minutes math), then
give you a final text answer combining both results - all without you
hard-coding "call convert first, then calculate" anywhere. YOUR code just
loops and dispatches whatever Claude asks for, in whatever order it asks.

WHAT YOU SHOULD OBSERVE / HOW TO KNOW YOU SUCCEEDED
----------------------------------------------------
- Print each tool call as it happens (tool name + input). You should see at
  least two tool calls before the final answer, in an order Claude chose
  (not one you hard-coded).
- The final printed answer should correctly state ~428 F and 36 total
  minutes (220C = 428F; 3 batches * 12 min = 36 min) - if your loop and
  tool implementations are correct, Claude's arithmetic-via-tool should be
  exact, not an LLM-guessed number, because you're the one computing it in
  Python and handing back the exact result.
- If you deliberately break a tool (e.g., make calculate always return 0)
  and rerun, Claude's final answer should reflect the WRONG tool result -
  proving Claude is actually relying on your tool_result content, not just
  doing the math itself internally. This is a good way to convince yourself
  the loop is real and not a mirage.

NO API KEY? Trace through the loop by hand: write out what messages list
would look like after each iteration, and predict what tool_use blocks
Claude would plausibly emit for the oven-temperature question above. That
tracing exercise is 80% of the value here.
"""

import ast
import json
import operator

from anthropic import Anthropic

client = Anthropic()
MODEL = "claude-sonnet-4-5"


# ---------------------------------------------------------------------------
# Step 1: Tool implementations (plain Python functions)
# ---------------------------------------------------------------------------

def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """
    TODO: implement celsius<->fahrenheit conversion.
    celsius -> fahrenheit: (value * 9/5) + 32
    fahrenheit -> celsius: (value - 32) * 5/9
    If from_unit == to_unit, just return value.
    Raise ValueError for any other unit names.
    """
    raise NotImplementedError("TODO: implement convert_temperature")


# A safe-ish arithmetic evaluator restricted to numbers and +-*/ - do not
# use Python's bare eval() on model- or user-supplied strings in real code.
_ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPS:
        return _ALLOWED_OPS[type(node.op)](_safe_eval(node.operand))
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    raise ValueError(f"Disallowed expression: {ast.dump(node)}")


def calculate(expression: str) -> float:
    """Evaluate a simple arithmetic expression safely (+ - * / only)."""
    return _safe_eval(ast.parse(expression, mode="eval"))


# ---------------------------------------------------------------------------
# Step 2: Tool schemas Claude will see (the "tools" parameter)
# ---------------------------------------------------------------------------

# TODO: fill in the JSON schema for both tools. Each tool needs: "name",
# "description" (be specific - this is what Claude uses to decide WHEN to
# call it), and "input_schema" (a JSON Schema object describing the
# parameters). Model this on convert_temperature's signature above.
TOOLS = [
    {
        "name": "convert_temperature",
        "description": "TODO",
        "input_schema": {
            "type": "object",
            "properties": {
                # TODO: value (number), from_unit (string), to_unit (string)
            },
            "required": [],  # TODO
        },
    },
    {
        "name": "calculate",
        "description": "TODO",
        "input_schema": {
            "type": "object",
            "properties": {
                # TODO: expression (string)
            },
            "required": [],  # TODO
        },
    },
]

TOOL_IMPLEMENTATIONS = {
    "convert_temperature": convert_temperature,
    "calculate": calculate,
}


# ---------------------------------------------------------------------------
# Step 3: The loop itself
# ---------------------------------------------------------------------------

def run_agent_loop(user_question: str, max_iterations: int = 6) -> str:
    """
    TODO: implement the full loop.

    messages = [{"role": "user", "content": user_question}]

    for _ in range(max_iterations):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

        # Whatever Claude returned (text and/or tool_use blocks) must be
        # appended back onto `messages` as the assistant turn, in full,
        # before you continue - the API needs the complete prior turn to
        # correctly interpret the tool_result you send next.
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            # Claude is done - concatenate any text blocks and return.
            # TODO: extract and return the final text
            ...

        # Otherwise: find every tool_use block in response.content, run the
        # corresponding Python function, and build one user message
        # containing a tool_result block per tool_use block (matched by
        # tool_use_id). Print each call as you make it (see docstring).
        # TODO: build tool_result_blocks, append as a user message, continue

    return "Stopped: hit max_iterations without a final answer."
    """
    raise NotImplementedError("TODO: implement run_agent_loop")


if __name__ == "__main__":
    question = (
        "The recipe says to preheat the oven to 220 celsius. What is that "
        "in fahrenheit, and if I need to fit 3 batches at that temperature "
        "and each batch takes 12 minutes, how many total minutes of oven "
        "time is that?"
    )
    try:
        answer = run_agent_loop(question)
        print("\nFinal answer:", answer)
    except NotImplementedError as e:
        print(f"(not implemented yet: {e})")
