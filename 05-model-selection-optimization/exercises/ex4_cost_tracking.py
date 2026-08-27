"""
ex4_cost_tracking.py — CCDV-F course, Module 05 (Cost and Token Management)

Goal: build a small utility that wraps a Claude API call, reads the `usage`
object off the response, and accumulates/reports running estimated cost
across multiple calls, using a pluggable price-per-token config.

*** IMPORTANT ABOUT PRICES ***
PRICING_PER_MILLION_TOKENS below is a PLACEHOLDER with made-up numbers. Do
not use these figures for any real budgeting decision. Before treating this
utility's output as meaningful, go to anthropic.com/pricing, find the
current published price per million input tokens and per million output
tokens for the model(s) you're using, and fill in real numbers.

*** IMPORTANT ABOUT usage FIELD NAMES ***
input_tokens and output_tokens are stable, well-established fields on the
Messages API usage object. Cache-related fields (for tokens written to a
new cache entry vs. tokens read from an existing cache hit) also exist on
usage, but exact field names have shifted across SDK/API versions in the
past — this exercise's TODOs use best-guess names
(cache_creation_input_tokens / cache_read_input_tokens); verify the exact
current names by printing a real response's usage object, or by checking
docs.claude.com, before relying on them.

This exercise needs ANTHROPIC_API_KEY set to run live (see 00-setup). If you
don't have a key yet, you can still implement and unit-test
`estimate_cost()` against hand-built fake usage objects/dicts — that part
needs no network access at all.

Run with:
    python ex4_cost_tracking.py
"""

import os
from dataclasses import dataclass, field

# TODO: fill these in from anthropic.com/pricing (current $ per MILLION
# tokens). These starter numbers are PLACEHOLDERS, not real prices.
PRICING_PER_MILLION_TOKENS = {
    "claude-haiku-4-5": {"input": 0.0, "output": 0.0},   # TODO: fill in real $/1M
    "claude-opus-4-latest": {"input": 0.0, "output": 0.0},       # TODO: fill in real $/1M
    # Add more model entries as needed. Consider also adding a reduced
    # "cache_read" rate per model here once you've verified the current
    # cache pricing discount at docs.claude.com.
}


@dataclass
class UsageRecord:
    """One call's token usage, plus its computed cost."""
    model: str
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class CostTracker:
    """Accumulates UsageRecords across multiple calls and reports totals."""
    records: list[UsageRecord] = field(default_factory=list)

    def add(self, record: UsageRecord) -> None:
        self.records.append(record)

    def total_cost(self) -> float:
        # TODO: sum record.cost_usd across self.records
        raise NotImplementedError

    def total_tokens(self) -> tuple[int, int]:
        """Return (total_input_tokens, total_output_tokens) across all records."""
        # TODO: sum input_tokens and output_tokens separately across records
        raise NotImplementedError

    def report(self) -> str:
        """Return a short human-readable summary string."""
        total_in, total_out = self.total_tokens()
        # TODO: build and return a multi-line string reporting:
        #   - number of calls tracked
        #   - total input tokens, total output tokens
        #   - total estimated cost (formatted as e.g. "$0.001234")
        raise NotImplementedError


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate $ cost for one call given token counts and PRICING_PER_MILLION_TOKENS.

    cost = (input_tokens / 1_000_000) * price["input"]
         + (output_tokens / 1_000_000) * price["output"]

    Raise a KeyError (or handle it explicitly) if `model` isn't in the
    pricing table, rather than silently returning 0 — a silent $0 estimate
    for an unpriced model is worse than an explicit error.
    """
    # TODO: implement using PRICING_PER_MILLION_TOKENS
    raise NotImplementedError


def call_and_track(client, model: str, prompt: str, tracker: CostTracker) -> str:
    """Make one Messages API call, record its usage/cost on `tracker`, return the reply text.

    Steps:
      1. Call client.messages.create(model=model, max_tokens=200,
         messages=[{"role": "user", "content": prompt}]).
      2. Read response.usage.input_tokens and response.usage.output_tokens.
      3. Try to also read cache-related usage fields if present (use
         getattr(response.usage, "cache_creation_input_tokens", 0) and
         getattr(response.usage, "cache_read_input_tokens", 0) so this
         doesn't break if the SDK version you have doesn't expose them).
      4. Compute cost via estimate_cost(...).
      5. Build a UsageRecord and tracker.add(...) it.
      6. Return response.content[0].text.
    """
    # TODO: implement per the docstring above.
    raise NotImplementedError


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY is not set.")
        print("You can still implement/test estimate_cost() and CostTracker without a key —")
        print("try calling estimate_cost() by hand with made-up token counts, e.g.:")
        print("  estimate_cost('claude-haiku-4-5', 1000, 200)")
        print("(after filling in real prices in PRICING_PER_MILLION_TOKENS).")
        return

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    model = "claude-haiku-4-5"  # TODO: verify this model name at docs.claude.com

    tracker = CostTracker()

    prompts = [
        "Name one moon of Jupiter.",
        "Name one moon of Saturn.",
        "What is the capital of Peru?",
    ]

    for p in prompts:
        reply = call_and_track(client, model, p, tracker)
        print(f"  Q: {p}\n  A: {reply}\n")

    print(tracker.report())

    # TODO: write a short comment here (2-3 sentences): given the real
    # prices you looked up, was the total cost of these 3 tiny calls
    # roughly what you expected? If you ran this same pattern 100,000
    # times a day in production, roughly what would the daily cost be —
    # and does that change which model tier you'd choose (tie this back to
    # Exercise 3)?
    #
    # YOUR OBSERVATION:
    # (write here)


if __name__ == "__main__":
    main()
