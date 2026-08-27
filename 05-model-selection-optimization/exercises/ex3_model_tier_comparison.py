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

# TODO: verify/update these against docs.claude.com before running.
MODEL_SMALL = "claude-haiku-4-5"   # "fast/small" tier placeholder
MODEL_LARGE = "claude-opus-4-latest"      # "larger/more capable" tier placeholder — VERIFY THIS NAME

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
    # TODO: implement using client.messages.create(model=model,
    # max_tokens=300, messages=[{"role": "user", "content": prompt}]).
    # Measure elapsed time with time.time() before/after the call.
    # Return (response.content[0].text, elapsed_seconds).
    raise NotImplementedError


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

    # TODO: verify the correct answer to the train problem yourself (do the
    # math by hand or with a calculator) and check whether each model's
    # ANSWER line was actually correct.

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
    # OBSERVATIONS:
    # (write here)


if __name__ == "__main__":
    main()
