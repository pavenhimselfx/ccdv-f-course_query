"""
ex3_model_tier_comparison.py — SOLUTION — CCDV-F course, Module 05

Reference solution comparing a fast/small-tier model against a
larger/more-capable-tier model on a moderately hard reasoning task.

*** IMPORTANT: MODEL_SMALL / MODEL_LARGE ARE PLACEHOLDERS. ***
Verify current model identifiers at docs.claude.com before running.
"""

import os
import time

MODEL_SMALL = "claude-3-5-haiku-latest"   # TODO (learner): verify at docs.claude.com
MODEL_LARGE = "claude-opus-4-latest"      # TODO (learner): verify at docs.claude.com

TASK_PROMPT = """A train leaves City A at 60 mph heading toward City B, 300 miles away.
At the same moment, a second train leaves City B heading toward City A at 90 mph, but it
makes one 15-minute stop exactly 100 miles into its trip. Assuming both trains travel at
constant speed otherwise, how long after departure do the two trains meet, and how far
from City A does that happen? Show your reasoning briefly, then give a final answer line
in the format 'ANSWER: <time>, <distance from A>'."""


def call_model(client, model: str, prompt: str) -> tuple[str, float]:
    start = time.time()
    response = client.messages.create(
        model=model,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    elapsed = time.time() - start
    return response.content[0].text, elapsed


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY is not set — skipping live comparison.")
        return

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    print(f"Small/fast model: {MODEL_SMALL}")
    print(f"Large/capable model: {MODEL_LARGE}\n")

    small_text, small_time = call_model(client, MODEL_SMALL, TASK_PROMPT)
    print(f"=== {MODEL_SMALL} ({small_time:.2f}s) ===\n{small_text}\n")

    large_text, large_time = call_model(client, MODEL_LARGE, TASK_PROMPT)
    print(f"=== {MODEL_LARGE} ({large_time:.2f}s) ===\n{large_text}\n")

    # Reference math for the learner to check both models' ANSWER lines against
    # (track the remaining GAP between the trains, which starts at 300 mi and
    # shrinks to 0 at the meeting point):
    #   Phase 1 (0 <= t <= 1.1111h, both moving): B covers its first 100 mi
    #     at 90 mph, taking 100/90 = 1.1111h. During this phase the gap
    #     closes at 60+90=150 mph. Gap remaining at t=1.1111h:
    #     300 - 150*1.1111 = 300 - 166.67 = 133.33 mi.
    #   Phase 2 (1.1111h <= t <= 1.3611h, B stopped for its 15-min/0.25h
    #     break): gap closes at 60 mph (A only). Gap remaining at
    #     t=1.3611h: 133.33 - 60*0.25 = 133.33 - 15 = 118.33 mi.
    #   Phase 3 (t > 1.3611h, B resumes): gap closes at 150 mph again.
    #     Time to close the remaining 118.33 mi: 118.33/150 = 0.7889h.
    #     Meeting time: 1.3611 + 0.7889 = 2.15h (~2h 9min) after departure.
    #   Distance from City A at meeting: A moved at a constant 60 mph the
    #     entire time (it never stopped): 60 * 2.15 = ~129 miles from City A.
    #   ANSWER (reference): approximately 2.15 hours (~2h 9min), ~129 miles from City A.
    #   (Small rounding differences between this comment's arithmetic and a
    #   model's answer are expected/acceptable; check the model got the
    #   *approach* right, especially correctly accounting for the stop.)

    if small_time:
        print(
            f"Latency: small={small_time:.2f}s  large={large_time:.2f}s  "
            f"(large was {large_time / small_time:.2f}x the small model's time)"
        )

    # OBSERVATIONS (representative pattern — actual numbers vary by run):
    # - The small/fast-tier model is typically noticeably faster
    #   (frequently 2-5x+ lower latency on a call like this), consistent
    #   with it being optimized for throughput/latency over raw reasoning
    #   depth.
    # - On a multi-step word problem like this one — which has an easy
    #   trap (naively ignoring the 15-minute stop, or applying it at the
    #   wrong point in the timeline) — the larger/more-capable model is
    #   more consistently correct and its reasoning trace is usually more
    #   careful about explicitly accounting for the stop's timing. The
    #   smaller model sometimes gets it right too, but is more prone to an
    #   arithmetic slip or to mishandling the piecewise nature of the
    #   problem (forgetting the stop pauses the gap-closing rate for that
    #   interval).
    # - Recommendation for a task like THIS (multi-step reasoning where
    #   correctness matters and volume is presumably lower, e.g. an
    #   internal analytics/planning feature): prefer the larger/more
    #   capable tier, optionally with extended/adaptive thinking enabled,
    #   since the cost of a wrong multi-step answer likely outweighs the
    #   extra latency/cost of the bigger model.
    # - Recommendation for the CONTRASTING task (classifying a one-line
    #   ticket into 3 categories, 10,000 requests/day): prefer the
    #   small/fast tier instead. That task doesn't require deep multi-step
    #   reasoning, so the larger model's extra capability is mostly wasted
    #   spend — and at 10,000 requests/day, the per-call latency and
    #   per-token cost difference between tiers is multiplied by volume,
    #   making the cheaper/faster tier the clearly better fit. This is the
    #   core "match model tier to task difficulty and volume" tradeoff
    #   from the README.


if __name__ == "__main__":
    main()
