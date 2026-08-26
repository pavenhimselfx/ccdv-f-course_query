"""
ex1_tokens_and_sampling.py — SOLUTION — CCDV-F course, Module 05

Reference solution for the tokens/sampling exercise. Read the comments —
they explain *why*, not just *what*. Field/method names for token counting
are flagged where they are best-effort/SDK-version-dependent.
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
    """~4 characters per token is a rough rule of thumb for English prose."""
    return len(text) / 4


def try_exact_token_count(text: str) -> int | None:
    """Best-effort exact token count via the SDK's token-counting endpoint.

    ASSUMPTION FLAGGED: as of writing, recent versions of the `anthropic`
    Python SDK expose `client.messages.count_tokens(model=..., messages=...)`,
    which calls a server-side endpoint that reports the exact token count
    for a given set of messages against a specific model, WITHOUT actually
    generating a response (so it's cheap/free to call relative to a real
    completion). The exact method name and return shape have moved before
    and may move again — if this raises AttributeError on your installed
    SDK version, check `docs.claude.com` or `dir(client.messages)` for the
    current name, or just rely on the rule-of-thumb estimate instead.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        result = client.messages.count_tokens(
            model="claude-3-5-haiku-latest",  # TODO (learner): verify current model name
            messages=[{"role": "user", "content": text}],
        )
        # ASSUMPTION FLAGGED: the count-tokens response is assumed to expose
        # `.input_tokens` similarly to a normal usage object. Verify this
        # against your installed SDK/docs.claude.com.
        return result.input_tokens
    except Exception:
        # Any failure here (missing method, network issue, model name
        # stale, etc.) just means we fall back to the estimate-only view —
        # this helper is a bonus, not a requirement.
        return None


def part1_estimate_tokens() -> None:
    print("=== Part 1: token estimation ===")
    for s in SAMPLE_STRINGS:
        estimate = estimate_tokens_rule_of_thumb(s)
        exact = try_exact_token_count(s)
        preview = s if len(s) <= 40 else s[:37] + "..."
        print(f"  {preview!r:45} chars={len(s):4}  ~tokens={estimate:6.1f}  exact={exact}")

    # OBSERVATION:
    # The plain English sentences land close to the ~4 chars/token rule of
    # thumb. The code snippet tends to tokenize a bit differently than
    # prose because of indentation whitespace, punctuation (colons,
    # parentheses) and identifier splitting, so the ratio can drift from
    # the English-prose baseline. The Japanese string deviates the most:
    # non-Latin scripts commonly tokenize at closer to 1-2 characters per
    # token (sometimes even less than 1, i.e. more than one token per
    # character) rather than ~4, because the tokenizer's subword vocabulary
    # is trained mostly on data dominated by Latin-script text. The
    # practical lesson: the 4-chars/token heuristic is an English-prose
    # rule of thumb, not a universal constant — for non-English text or
    # code-heavy content, lean on an exact tokenizer/count_tokens call
    # instead of the rule of thumb when precision matters (e.g. right at a
    # context-window boundary).


def part2_sampling_and_temperature() -> None:
    print("\n=== Part 2: sampling and non-determinism ===")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  Skipping live calls: ANTHROPIC_API_KEY is not set.")
        return

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    model = "claude-3-5-haiku-latest"  # TODO (learner): verify current model name
    prompt = "In one short sentence, describe an unusual pet."

    for temperature in [0.0, 1.0]:
        print(f"\n  temperature={temperature}")
        for i in range(3):
            start = time.time()
            response = client.messages.create(
                model=model,
                max_tokens=40,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = response.content[0].text
            elapsed = time.time() - start
            print(f"    call {i + 1} ({elapsed:.2f}s): {response_text!r}")

    # OBSERVATION (representative of what you should typically see — your
    # actual run will differ since this is exactly the non-determinism
    # being demonstrated):
    # At temperature=1.0, the three responses are usually noticeably
    # different from each other — different unusual pets, different
    # phrasing — because the sampling distribution's tail gets a real
    # chance to be picked each time. At temperature=0.0, the three
    # responses are typically identical or very close to identical, since
    # the model is consistently favoring its single highest-probability
    # token at each step. They are NOT, however, guaranteed to be
    # byte-for-byte identical on every possible prompt/model/run — ties in
    # the probability distribution, minor backend nondeterminism, or
    # streaming/batching effects can still occasionally produce small
    # differences even at temperature=0. This matches the README's framing:
    # temperature=0 is "more deterministic," not an absolute guarantee of
    # identical output. Practical implication: don't write an automated
    # test that asserts exact string equality against a live model call,
    # even at temperature=0 — assert on structure/content properties
    # instead (this connects to the Evaluation/Testing domain).


if __name__ == "__main__":
    part1_estimate_tokens()
    part2_sampling_and_temperature()
