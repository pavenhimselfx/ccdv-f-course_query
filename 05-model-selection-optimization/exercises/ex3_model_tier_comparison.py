"""
ex3_model_tier_comparison.py — CCDV-F course, Module 05 (Model Selection and Tradeoffs)

Goal: send the SAME moderately-hard task to a "fast/small" tier model and a
"larger/more capable" tier model, compare latency and qualitative output
quality, and write a recommendation for which tier fits which kind of task.

*** IMPORTANT ABOUT MODEL NAMES ***
The MODEL_SMALL / MODEL_LARGE placeholders below are illustrative only.
Exact model version strings change frequently as Anthropic ships new
releases (see README.md's "breaking behavior changes across releases"
section). Before running this exercise, go to docs.claude.com and fill in
the current model identifiers for a Haiku-class ("fast/small") model and an
Opus-class or Sonnet-class ("larger/more capable") model. Do not assume the
placeholder names below still exist by the time you read this.

This exercise needs ANTHROPIC_API_KEY set to run (see 00-setup). If you
don't have a key yet, read through the task and the TODOs, and write your
*prediction* of which tier will be faster and which will produce a more
thorough answer in the OBSERVATIONS section — then run it for real once you
have a key.

Run with:
    python ex3_model_tier_comparison.py
"""

import os
import time

# Verified against the current model lineup (not the exercise's original
# placeholders -- MODEL_LARGE's placeholder, "claude-opus-4-latest", is stale):
MODEL_SMALL = "claude-haiku-4-5"   # "fast/small" tier -- also used in ex1/ex2
MODEL_LARGE = "claude-opus-5"      # "larger/more capable" tier, current generation

# A moderately hard task: some multi-step reasoning, not a one-liner.
TASK_PROMPT = """A train leaves City A at 60 mph heading toward City B, 300 miles away.
At the same moment, a second train leaves City B heading toward City A at 90 mph, but it
makes one 15-minute stop exactly 100 miles into its trip. Assuming both trains travel at
constant speed otherwise, how long after departure do the two trains meet, and how far
from City A does that happen? Show your reasoning briefly, then give a final answer line
in the format 'ANSWER: <time>, <distance from A>'."""


def call_model(client, model: str, prompt: str) -> tuple[str, float]:
    """Call `model` with `prompt`, return (response_text, elapsed_seconds).

    Use time.time() around the call to measure latency, as the exercise
    spec requires — this is wall-clock latency for a single non-streaming
    call, not a rigorous benchmark (network conditions vary run to run).
    """
    start = time.time()
    response = client.messages.create(
        model=model,
        # 300 was the exercise's original value, and it's too small: found by
        # actually running this that Haiku's verbose step-by-step markdown
        # reasoning gets cut off mid-sentence at 300, and Opus 5's internal
        # reasoning (see ex1's effort="max" finding) can consume the ENTIRE
        # 300-token budget before any visible answer text is generated,
        # producing a silently empty response with no error. 2048 gives both
        # styles enough room to actually reach their final ANSWER line.
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    elapsed = time.time() - start
    # Not response.content[0].text: ex1 found that a thinking block can
    # precede the text block for newer-generation models, which breaks a
    # bare index-0 lookup. Filter by block type instead of assuming position.
    text = "".join(
        block.text for block in response.content if getattr(block, "type", None) == "text"
    )
    print(f"    [{model} diagnostic] stop_reason={response.stop_reason} "
          f"blocks={[b.type for b in response.content]}")
    return text, elapsed


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY is not set — skipping live comparison.")
        print("Write your prediction in OBSERVATIONS below, then re-run with a key.")
        return

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    print(f"Small/fast model: {MODEL_SMALL}")
    print(f"Large/capable model: {MODEL_LARGE}")
    print("\n(If either call below fails with a 404 / not_found_error, the model name is")
    print("stale — go update MODEL_SMALL/MODEL_LARGE from docs.claude.com and re-run.)\n")

    small_text, small_time = call_model(client, MODEL_SMALL, TASK_PROMPT)
    print(f"=== {MODEL_SMALL} ({small_time:.2f}s) ===\n{small_text}\n")

    large_text, large_time = call_model(client, MODEL_LARGE, TASK_PROMPT)
    print(f"=== {MODEL_LARGE} ({large_time:.2f}s) ===\n{large_text}\n")

    # Verified by hand (exact fractions, not estimation): train B reaches its
    # 100-mile stop point at t=10/9 h (~66.7 min), resumes at t=49/36 h
    # (~81.7 min) after the 15-min stop. Solving for where the two trains'
    # positions coincide (checking, and confirming, that the meeting happens
    # AFTER B resumes moving -- it does) gives t=43/20 h = 2.15 h = 2h 9min,
    # at 129 miles from City A. Ground truth: ANSWER: 2 hours 9 minutes (2.15
    # hours), 129 miles.
    CORRECT_TIME_HOURS = 2.15
    CORRECT_DISTANCE_FROM_A = 129
    print(f"(Ground truth: {CORRECT_TIME_HOURS} hours / 2h9m, "
          f"{CORRECT_DISTANCE_FROM_A} miles from City A -- verified by hand with exact fractions.)\n")

    print(f"Latency: small={small_time:.2f}s  large={large_time:.2f}s  "
          f"(large was {large_time / small_time:.2f}x the small model's time)"
          if small_time else "")

    # TODO: write a short comparison here (4-6 sentences) covering:
    #   - Which model was faster, and by roughly how much?
    #   - Did both models get the correct final answer? Was one's
    #     reasoning clearer, more careful about the 15-minute stop, etc.?
    #   - For a task like THIS one (moderate multi-step math/logic), which
    #     tier would you pick for a production feature, and why?
    #   - Now imagine a different task: classifying a one-line support
    #     ticket into 3 categories, at 10,000 requests/day. Which tier
    #     would you pick for THAT task, and why is it a different answer
    #     than for the train problem?
    #
    # OBSERVATIONS (from a real run):
    #   Haiku 4.5 was faster in absolute terms (6.54s vs. 12.19s -- Opus 5
    #   took ~1.86x as long), and both models got the EXACT correct answer:
    #   2.15 hours (2h9m), 129 miles from City A, matching the hand-verified
    #   ground truth precisely, including the dollar-for-dollar cross-check
    #   from Train B's side. Both were genuinely careful about the 15-minute
    #   stop -- each explicitly checked whether the trains could have met
    #   before or during the stop before concluding the meeting happens
    #   after B resumes, rather than just assuming the stop doesn't matter.
    #   Opus's derivation was more mathematically compact (a single "closing
    #   speed after the stop" step vs. Haiku's more verbose phase-by-phase
    #   walkthrough with extra headers), but that difference in style didn't
    #   translate into a correctness advantage here -- Haiku's more verbose
    #   answer was equally right. The diagnostic line also caught something
    #   new: Opus 5 emitted a thinking block by default with NO effort
    #   parameter set at all (blocks=['thinking', 'text']), unlike Sonnet 5
    #   in ex1, which only did that at effort="max" -- Opus's default
    #   behavior already leans toward visible reasoning, which is part of
    #   why it's slower here, not just "bigger model = slower."
    #   For a task like this train problem: I'd ship Haiku. It got the
    #   answer fully right, in less than half the wall-clock time, with no
    #   evidence in this trial that Opus's extra capability was needed to
    #   reach correctness -- paying ~1.86x the latency/cost bought nothing
    #   measurable here. (Caveat: this is one problem instance; a task this
    #   shape but harder, or higher-stakes, might justify Opus's margin --
    #   I wouldn't generalize "Haiku is always enough for word problems"
    #   from a single trial any more than I'd generalize ex2's zero-shot
    #   result from 5 examples.)
    #   For 10,000 one-line ticket classifications/day: Haiku, more
    #   decisively, and for a different reason than above. This isn't about
    #   "Haiku happened to be enough this time" -- ex2 already showed
    #   empirically that this exact shape of task (small closed label set,
    #   short input, low ambiguity) needs no multi-step reasoning at all, so
    #   Opus's deeper-reasoning default (that thinking block) is pure
    #   overhead here: extra latency and extra cost, multiplied by 10,000
    #   calls/day, for a task that doesn't need the capability it's paying
    #   for. The train problem and the ticket-classification task differ on
    #   exactly the axis that should drive model tier choice: does the task
    #   need multi-step reasoning to get right, or is it a simple, bounded
    #   decision a smaller model already nails -- volume then decides how
    #   much any wasted per-call cost/latency actually matters in practice.


if __name__ == "__main__":
    main()
