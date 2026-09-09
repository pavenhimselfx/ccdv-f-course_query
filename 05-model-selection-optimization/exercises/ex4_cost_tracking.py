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

# Real prices as of this writing, from claude.com/pricing ($ per MILLION tokens)
# -- verify against the live pricing page before trusting these for a real
# budgeting decision; prices change over time.
PRICING_PER_MILLION_TOKENS = {
    "claude-haiku-4-5": {
        "input": 1.0, "output": 5.0,
        "cache_read": 0.10, "cache_write": 1.25,
    },
    "claude-opus-5": {
        "input": 5.0, "output": 25.0,
        "cache_read": 0.50, "cache_write": 6.25,
    },
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
        return sum(record.cost_usd for record in self.records)

    def total_tokens(self) -> tuple[int, int]:
        """Return (total_input_tokens, total_output_tokens) across all records."""
        total_in = sum(record.input_tokens for record in self.records)
        total_out = sum(record.output_tokens for record in self.records)
        return total_in, total_out

    def report(self) -> str:
        """Return a short human-readable summary string."""
        total_in, total_out = self.total_tokens()
        return (
            f"Calls tracked: {len(self.records)}\n"
            f"Total input tokens: {total_in}\n"
            f"Total output tokens: {total_out}\n"
            f"Total estimated cost: ${self.total_cost():.6f}"
        )


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate $ cost for one call given token counts and PRICING_PER_MILLION_TOKENS.

    cost = (input_tokens / 1_000_000) * price["input"]
         + (output_tokens / 1_000_000) * price["output"]

    Raise a KeyError (or handle it explicitly) if `model` isn't in the
    pricing table, rather than silently returning 0 — a silent $0 estimate
    for an unpriced model is worse than an explicit error.
    """
    if model not in PRICING_PER_MILLION_TOKENS:
        raise KeyError(
            f"No pricing entry for model {model!r} in PRICING_PER_MILLION_TOKENS "
            "-- add one (verified against claude.com/pricing) before estimating cost."
        )
    price = PRICING_PER_MILLION_TOKENS[model]
    return (
        (input_tokens / 1_000_000) * price["input"]
        + (output_tokens / 1_000_000) * price["output"]
    )


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
    response = client.messages.create(
        model=model,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    cache_creation = getattr(response.usage, "cache_creation_input_tokens", 0)
    cache_read = getattr(response.usage, "cache_read_input_tokens", 0)

    cost = estimate_cost(model, input_tokens, output_tokens)

    tracker.add(
        UsageRecord(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_creation_input_tokens=cache_creation,
            cache_read_input_tokens=cache_read,
            cost_usd=cost,
        )
    )

    # Not response.content[0].text: see ex1/ex3 -- a thinking block can
    # precede the text block, so filter by type rather than assume position.
    return "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )


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
    model = "claude-haiku-4-5"  # verified current in ex1/ex2/ex3

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
    # YOUR OBSERVATION (from a real run):
    #   3 tiny factual-lookup calls cost $0.000310 total (40 input + 54
    #   output tokens on Haiku 4.5) -- negligibly small, as expected for
    #   one-line questions on the cheapest tier. Worth noting output tokens
    #   dominated the cost more than raw token count suggests: output is
    #   priced 5x input per token for Haiku ($5 vs $1/MTok), so the 54 output
    #   tokens contributed roughly 4x the cost the 40 input tokens did,
    #   despite being a similar token count.
    #   Projected to 100,000 calls/day at this same per-call average (~13.3
    #   input / 18 output tokens): Haiku 4.5 would cost ~$10.33/day
    #   (~$3,772/year). The SAME workload on Opus 5 (5x the per-token price
    #   on both input and output) would cost ~$51.67/day (~$18,858/year) --
    #   a >$15,000/year difference for identical trivial factual-lookup
    #   questions that don't need Opus's reasoning depth at all.
    #   This directly reinforces ex3's conclusion rather than changing it:
    #   for a task shape like this (short, simple, no multi-step reasoning
    #   required), volume is exactly what turns "which tier" from an
    #   abstract preference into a concrete, material cost decision --
    #   $15k/year isn't a rounding error, and none of it would have bought
    #   better answers here. The lesson from ex3 (match tier to whether the
    #   task actually needs the capability) is the same lesson that makes
    #   this projection worth computing before shipping, not after.


if __name__ == "__main__":
    main()
