"""
SOLUTION - Exercise 2: A Minimal Hand-Rolled Tool-Use Loop

Deliberately still built on the raw `anthropic` Messages API package (and so
still needs a metered Console API key - see 00-setup/README.md sections
2-3), unlike ex1/ex3 in this domain, which were reworked onto the Claude
Agent SDK to run free on a subscription. See the top of
exercises/ex2_basic_tool_use_loop.py for why: this exercise's whole point is
building protocol-level intuition for the tool_use/tool_result mechanics
that the Agent SDK exists to abstract away, so abstracting them away here
would defeat the exercise. Once this loop feels familiar, ex1's `run_agent()`
and ex3's subagent calls show the same loop with that abstraction applied.

SDK-usage assumptions: tool_use/tool_result content-block shapes,
stop_reason == "tool_use" as the loop-continuation signal, and tool_result
sent back as a user message. Verify against docs.claude.com if these have
drifted since this was written.
"""

import ast
import operator

from anthropic import Anthropic

client = Anthropic()
MODEL = "claude-sonnet-4-5"


# ---------------------------------------------------------------------------
# Step 1: Tool implementations
# ---------------------------------------------------------------------------

def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()
    if from_unit == to_unit:
        return value
    if from_unit == "celsius" and to_unit == "fahrenheit":
        return (value * 9 / 5) + 32
    if from_unit == "fahrenheit" and to_unit == "celsius":
        return (value - 32) * 5 / 9
    raise ValueError(f"Unsupported unit conversion: {from_unit} -> {to_unit}")


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
    return _safe_eval(ast.parse(expression, mode="eval"))


# ---------------------------------------------------------------------------
# Step 2: Tool schemas
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "convert_temperature",
        "description": (
            "Convert a temperature value between Celsius and Fahrenheit. "
            "Use this any time a conversion between these two units is needed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "value": {"type": "number", "description": "The numeric temperature to convert."},
                "from_unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The unit `value` is currently in.",
                },
                "to_unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The unit to convert to.",
                },
            },
            "required": ["value", "from_unit", "to_unit"],
        },
    },
    {
        "name": "calculate",
        "description": (
            "Evaluate a simple arithmetic expression using +, -, *, / and "
            "parentheses. Use this for any arithmetic instead of computing "
            "it yourself, so the result is exact."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "An arithmetic expression, e.g. '3 * 12'.",
                },
            },
            "required": ["expression"],
        },
    },
]

TOOL_IMPLEMENTATIONS = {
    "convert_temperature": convert_temperature,
    "calculate": calculate,
}


# ---------------------------------------------------------------------------
# Step 3: The loop
# ---------------------------------------------------------------------------

def run_agent_loop(user_question: str, max_iterations: int = 6) -> str:
    messages = [{"role": "user", "content": user_question}]

    for iteration in range(max_iterations):
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")

        tool_result_blocks = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            print(f"[iteration {iteration}] tool call: {block.name}({block.input})")

            fn = TOOL_IMPLEMENTATIONS.get(block.name)
            if fn is None:
                result_content = f"Error: unknown tool '{block.name}'"
            else:
                try:
                    result_content = str(fn(**block.input))
                except Exception as exc:  # noqa: BLE001 - surface any tool
                    # error back to Claude as a tool_result rather than
                    # crashing the loop, so it can react (e.g. retry with
                    # different arguments) instead of the whole program dying.
                    result_content = f"Error: {exc}"

            tool_result_blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_content,
                }
            )

        messages.append({"role": "user", "content": tool_result_blocks})

    return "Stopped: hit max_iterations without a final answer."


if __name__ == "__main__":
    question = (
        "The recipe says to preheat the oven to 220 celsius. What is that "
        "in fahrenheit, and if I need to fit 3 batches at that temperature "
        "and each batch takes 12 minutes, how many total minutes of oven "
        "time is that?"
    )
    answer = run_agent_loop(question)
    print("\nFinal answer:", answer)
    # Expected tool calls (order may vary - this is Claude's choice, not
    # hard-coded): convert_temperature(220, celsius, fahrenheit) -> 428.0,
    # and calculate("3 * 12") -> 36.0. Final answer should state both:
    # 220C is 428F, and total oven time is 36 minutes.
