"""
ex1_tokens_and_sampling.py — CCDV-F course, Module 05 (LLM Fundamentals)

Goal: build intuition for (a) token counting/estimation and (b) sampling and
non-determinism (temperature).

You do NOT need an Anthropic API key to do Part 1 of this exercise (it's just
arithmetic/estimation over local strings). Part 2 calls the live API and
compares outputs across temperature settings, so it does need
ANTHROPIC_API_KEY set (see the 00-setup module) — if you don't have a key
yet, read Part 2 carefully, predict in a comment what you *expect* to see,
and come back to actually run it once your key is set up.

Run with:
    python ex1_tokens_and_sampling.py
"""

import os
import time

SAMPLE_STRINGS = [
    "The quick brown fox jumps over the lazy dog.",
    "Tokenization splits text into subword units, not whole words or characters.",
    "def add(a, b):\n    return a + b",
    "supercalifragilisticexpialidocious",
    "こんにちは、世界",  # non-English script: expect a different chars/token ratio
]


def estimate_tokens_rule_of_thumb(text: str) -> float:
    """Estimate token count using the ~4-characters-per-token rule of thumb.

    This is a rough heuristic for English prose, NOT an exact tokenizer.
    Returns a float so callers can see the raw estimate before rounding.
    """
    # TODO: implement the ~4 chars/token estimate.
    # Hint: len(text) / 4
    raise NotImplementedError


def try_exact_token_count(text: str) -> int | None:
    """Try to get an exact token count via the Anthropic SDK, if available.

    The `anthropic` Python SDK exposes a way to count tokens for a given set
    of messages against a specific model without actually generating a
    response (useful for pre-flight cost/context estimates). The exact
    method name has moved around between SDK versions (for example, some
    versions expose `client.messages.count_tokens(...)`) — check the
    installed SDK's docs/docstrings, or docs.claude.com, if this doesn't
    work out of the box.

    Return None (instead of raising) if the SDK/method isn't available, so
    this exercise still runs without a key.
    """
    # TODO (optional/bonus): implement using anthropic.Anthropic().messages.count_tokens(...)
    # or equivalent. It's fine to return None here if you don't have a key
    # yet, or if your installed SDK version doesn't expose this.
    return None


def part1_estimate_tokens() -> None:
    print("=== Part 1: token estimation ===")
    for s in SAMPLE_STRINGS:
        estimate = estimate_tokens_rule_of_thumb(s)
        exact = try_exact_token_count(s)
        preview = s if len(s) <= 40 else s[:37] + "..."
        print(f"  {preview!r:45} chars={len(s):4}  ~tokens={estimate:6.1f}  exact={exact}")

    # TODO: write a short comment here (2-4 sentences) on what you notice.
    # In particular: does the non-English string (Japanese) or the code
    # snippet look like it deviates from the ~4 chars/token rule compared to
    # the plain English sentences? Why might that be?
    #
    # YOUR OBSERVATION:
    # (write here)


def part2_sampling_and_temperature() -> None:
    print("\n=== Part 2: sampling and non-determinism ===")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  Skipping live calls: ANTHROPIC_API_KEY is not set.")
        print("  (See README.md Part 2 instructions and predict the outcome instead.)")
        return

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    # TODO: pick a model identifier. Use a fast/cheap tier for this exercise
    # since you're making several repeated calls. Check docs.claude.com for
    # the current model name if this one has been superseded.
    model = "claude-haiku-4-5"

    prompt = "In one short sentence, describe an unusual pet."

    # TODO: for each temperature in this list, call the API 3 times with the
    # SAME prompt and print each response. Use client.messages.create(...)
    # with model=model, max_tokens=40, temperature=temp,
    # messages=[{"role": "user", "content": prompt}].
    for temperature in [0.0, 1.0]:
        print(f"\n  temperature={temperature}")
        for i in range(3):
            start = time.time()
            # TODO: make the call and extract response.content[0].text
            response_text = None  # replace with the real call
            elapsed = time.time() - start
            print(f"    call {i + 1} ({elapsed:.2f}s): {response_text!r}")

    # TODO: write a short comment here (3-5 sentences) comparing what you
    # observed at temperature=0.0 vs temperature=1.0. Were the three
    # temperature=0.0 responses identical, similar-but-not-identical, or
    # wildly different from each other? What about temperature=1.0? Does
    # this match what the README said about temperature=0 being "more
    # deterministic" rather than "guaranteed identical"?
    #
    # YOUR OBSERVATION:
    # (write here)


if __name__ == "__main__":
    part1_estimate_tokens()
    part2_sampling_and_temperature()
