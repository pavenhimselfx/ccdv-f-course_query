"""
ex4_cost_tracking.py — SOLUTION — CCDV-F course, Module 05

Reference solution for a small cost-tracking utility that wraps Messages API
calls, reads `usage`, and accumulates estimated cost via a pluggable
per-model pricing table.

*** PRICES BELOW ARE ILLUSTRATIVE PLACEHOLDERS, NOT REAL CURRENT PRICES. ***
Verify at anthropic.com/pricing before using this pattern for real budgeting.
*** CACHE-RELATED usage FIELD NAMES ARE BEST-EFFORT/ASSUMED ***
(cache_creation_input_tokens / cache_read_input_tokens) — verify the exact
current field names against a real response or docs.claude.com; this
solution defensively uses getattr(..., default=0) specifically so it keeps
working even if those exact names have changed on your installed SDK.
"""

import os
from dataclasses import dataclass, field

# Illustrative placeholder $ per MILLION tokens — NOT real prices.
# Roughly shaped (small model cheaper than large model, output pricier than
# input, which is the general pattern across Anthropic's tiers) but the
# actual numbers must come from anthropic.com/pricing.
PRICING_PER_MILLION_TOKENS = {
    "claude-haiku-4-5": {"input": 0.80, "output": 4.00},   # PLACEHOLDER — verify!
    "claude-opus-4-latest": {"input": 15.00, "output": 75.00},     # PLACEHOLDER — verify!
}


@dataclass
class UsageRecord:
    model: str
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class CostTracker:
    records: list[UsageRecord] = field(default_factory=list)

    def add(self, record: UsageRecord) -> None:
        self.records.append(record)

    def total_cost(self) -> float:
        return sum(r.cost_usd for r in self.records)

    def total_tokens(self) -> tuple[int, int]:
        total_in = sum(r.input_tokens for r in self.records)
        total_out = sum(r.output_tokens for r in self.records)
        return total_in, total_out

    def report(self) -> str:
        total_in, total_out = self.total_tokens()
        lines = [
            "=== Cost Tracker Report ===",
            f"  Calls tracked:        {len(self.records)}",
            f"  Total input tokens:   {total_in}",
            f"  Total output tokens:  {total_out}",
            f"  Total estimated cost: ${self.total_cost():.6f}",
        ]
        return "\n".join(lines)


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    if model not in PRICING_PER_MILLION_TOKENS:
        # Explicit failure rather than a silent $0 estimate — an unpriced
        # model should be a visible bug, not a quietly wrong dashboard.
        raise KeyError(
            f"No pricing configured for model {model!r}. "
            f"Add it to PRICING_PER_MILLION_TOKENS with current rates from "
            f"anthropic.com/pricing."
        )
    price = PRICING_PER_MILLION_TOKENS[model]
    return (input_tokens / 1_000_000) * price["input"] + (output_tokens / 1_000_000) * price["output"]


def call_and_track(client, model: str, prompt: str, tracker: CostTracker) -> str:
    response = client.messages.create(
        model=model,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )

    usage = response.usage
    input_tokens = usage.input_tokens
    output_tokens = usage.output_tokens
    # Defensive getattr: these cache fields may not exist on every SDK
    # version's usage object, and may be 0/absent if caching wasn't used
    # on this particular call anyway.
    cache_creation = getattr(usage, "cache_creation_input_tokens", 0) or 0
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0

    # NOTE: this simple estimate_cost() call treats cache_creation/cache_read
    # tokens as informational only and does not apply a separate discounted
    # rate to them. A more complete cost model would look up distinct
    # cache-write and cache-read per-token rates (verify these at
    # docs.claude.com/anthropic.com/pricing — cache reads are typically
    # billed at a reduced rate vs. a normal input token, and cache writes
    # at a slight premium) and price those token counts separately instead
    # of folding them into the plain input_tokens count.
    cost = estimate_cost(model, input_tokens, output_tokens)

    record = UsageRecord(
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_creation_input_tokens=cache_creation,
        cache_read_input_tokens=cache_read,
        cost_usd=cost,
    )
    tracker.add(record)

    return response.content[0].text


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY is not set.")
        print("Demonstrating estimate_cost() with made-up token counts instead:")
        demo_cost = estimate_cost("claude-haiku-4-5", 1000, 200)
        print(f"  estimate_cost('claude-haiku-4-5', 1000, 200) = ${demo_cost:.6f}")
        print("  (using PLACEHOLDER prices — fill in real ones from anthropic.com/pricing)")
        return

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    model = "claude-haiku-4-5"  # TODO (learner): verify current model name

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

    # OBSERVATION:
    # With these tiny prompts and max_tokens=200 (but short actual replies),
    # total cost across 3 calls should be a very small fraction of a cent
    # even at real (non-placeholder) prices — these prompts are only a
    # handful of tokens of input and output each. Scaling this same
    # per-call shape to 100,000 calls/day multiplies both token counts and
    # cost by 100,000, which is exactly the point where the model-tier
    # choice from Exercise 3 stops being academic: at that volume, the
    # difference between a Haiku-class rate and an Opus-class rate (often
    # a double-digit multiplier apart) turns a trivial per-call cost into a
    # daily bill that can differ by a large multiple, which is why
    # high-volume/low-complexity work (like this trivia-question shape)
    # should default to the cheapest tier that reliably gets the task
    # right, reserving the larger tier for calls that actually need its
    # extra reasoning capability.


if __name__ == "__main__":
    main()
