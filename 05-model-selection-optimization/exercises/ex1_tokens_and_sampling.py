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
import sys
import time

# Windows terminals commonly default stdout to a legacy codepage (e.g. cp1252) that
# can't encode the Japanese sample string below, causing a crash on print() rather
# than anything related to token counting. Force UTF-8 so this runs the same on any
# platform. (Only Python 3.7+'s TextIOWrapper.reconfigure supports this.)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MODEL = "claude-haiku-4-5"  # fast/cheap tier -- appropriate for repeated calls in ex2
# Confirmed by actually running this exercise: Haiku 4.5 still fully supports
# `temperature` (a real 400 rejection did NOT happen) but does NOT support
# `output_config.effort` at all (a real 400 DID happen: "This model does not
# support the effort parameter."). The temperature/top_p/top_k deprecation
# documented at docs.claude.com applies to "models released after Claude Opus
# 4.6" -- Haiku 4.5 is evidently outside that boundary, unlike the newer
# effort-based family. Use a model from that newer family to see `effort`
# actually take effect.
EFFORT_MODEL = "claude-sonnet-5"


def _extract_text(content_blocks) -> str:
    """Join just the text blocks from a Messages API response's `.content`.

    Discovered why this is necessary by actually running Part 2 below: at
    effort="max", claude-sonnet-5 puts a ThinkingBlock BEFORE the text block in
    `.content`, so `response.content[0].text` crashes with an AttributeError
    (ThinkingBlock has no `.text`). `.content` is not reliably "just the
    answer at index 0" once thinking is involved -- filter by block type
    instead of assuming position.
    """
    return "".join(
        block.text for block in content_blocks if getattr(block, "type", None) == "text"
    )

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
    return len(text) / 4


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
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        result = client.messages.count_tokens(
            model=MODEL,
            messages=[{"role": "user", "content": text}],
        )
        return result.input_tokens
    except Exception:
        return None


def part1_estimate_tokens() -> None:
    print("=== Part 1: token estimation ===")
    for s in SAMPLE_STRINGS:
        estimate = estimate_tokens_rule_of_thumb(s)
        exact = try_exact_token_count(s)
        preview = s if len(s) <= 40 else s[:37] + "..."
        print(f"  {preview!r:45} chars={len(s):4}  ~tokens={estimate:6.1f}  exact={exact}")

    # YOUR OBSERVATION (from a real run with ANTHROPIC_API_KEY set):
    #   English sentence: chars=44, ~tokens=11.0 (estimate), exact=18 -- the
    #   ~4-chars/token heuristic UNDERSHOOTS noticeably even for plain English
    #   prose (18 actual vs. 11 estimated), so "4 chars/token" is a rough floor,
    #   not a tight prediction, even in the "easy" case it's designed for.
    #   The code snippet ("def add(a, b): return a + b") is the most extreme
    #   English-ish case: chars=31, ~tokens=7.8 estimated, exact=20 -- more
    #   than 2.5x the estimate. Code tokenizes far less efficiently than prose
    #   because punctuation, indentation whitespace, and short identifiers each
    #   tend to become their own token(s) rather than combining into
    #   dictionary-common subwords the way English words do.
    #   The Japanese string is the starkest case: chars=8, ~tokens=2.0
    #   estimated, exact=15 -- nearly 7.5x the estimate. Non-Latin scripts
    #   tokenize far less efficiently per character because the tokenizer's
    #   vocabulary was built predominantly from English/Latin-script text, so
    #   each Japanese character (or small cluster) often becomes its own
    #   token rather than several characters combining into one, unlike
    #   English where common multi-character chunks get their own token.
    #   Takeaway: the ~4 chars/token rule is only a rough floor for plain
    #   English prose, and gets progressively worse the further content is
    #   from that case (code, then non-Latin scripts) -- use the real
    #   count_tokens count for anything where the estimate actually matters
    #   (cost/context budgeting), not the heuristic.


def part2_sampling_and_temperature() -> None:
    print("\n=== Part 2: sampling and non-determinism ===")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("  Skipping live calls: ANTHROPIC_API_KEY is not set.")
        print("  (See README.md Part 2 instructions and predict the outcome instead.)")
        return

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    model = MODEL

    prompt = "In one short sentence, describe an unusual pet."

    # DISCOVERY (found by actually running this against a live account, not from
    # docs alone): docs.claude.com states `temperature`/`top_p`/`top_k` are
    # DEPRECATED for models released after Claude Opus 4.6, replaced by
    # `output_config={"effort": ...}`. The installed SDK's typed
    # `messages.create()` doesn't even expose `temperature` as a keyword anymore
    # (confirmed: passing it directly raises a local TypeError before any network
    # call happens) -- but running this for real against claude-haiku-4-5 showed
    # temperature=0.0 was ACCEPTED, not rejected. Testing against a model from the
    # newer family (see EFFORT_MODEL) is needed to actually see `effort` do
    # anything -- Haiku 4.5 rejects `effort` outright ("This model does not
    # support the effort parameter"). Conclusion: the deprecation boundary is
    # model-specific, not a blanket SDK-version change -- Haiku 4.5 sits outside
    # it (still classic temperature-based sampling), the effort-based family
    # sits inside it (temperature locked to 1.0, effort is the real control).

    # --- Step 1: temperature on Haiku 4.5 -- still genuinely supported --------
    # Sent via extra_body (bypasses the SDK's own typed parameters, so this is
    # exactly what the API itself does with a raw temperature field in the
    # request body, not just an SDK-level restriction).
    print("\n  Step 1: attempting temperature=0.0 via extra_body")
    try:
        client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}],
            extra_body={"temperature": 0.0},
        )
        print("    Accepted: this model (Haiku 4.5) still honors temperature for real.")
    except anthropic.BadRequestError as e:
        print(f"    Rejected: {e}")

    # --- Step 2: baseline non-determinism with NO temperature control ---------
    # This is the old exercise's "temperature=1.0" arm -- now the ONLY arm
    # available, since there's no way to dial it down anymore.
    print("\n  Step 2: 3 calls at default settings (no temperature control possible)")
    for i in range(3):
        start = time.time()
        response = client.messages.create(
            model=model,
            max_tokens=40,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = _extract_text(response.content)
        elapsed = time.time() - start
        print(f"    call {i + 1} ({elapsed:.2f}s): {response_text!r}")

    # --- Step 3: the modern control surface -- output_config.effort -----------
    # effort governs how much the model reasons/computes, not randomness -- so
    # this is exploring "what replaced temperature as a tunable knob," not
    # trying to reproduce temperature's exact old behavior. Uses EFFORT_MODEL,
    # not MODEL/Haiku 4.5, since Haiku 4.5 rejects `effort` outright (confirmed
    # above) -- a concrete reminder that per-model capability, not just SDK
    # version, decides which parameters are even valid to send.
    print(f"\n  Step 3: output_config.effort comparison on {EFFORT_MODEL} "
          f"(Haiku 4.5 doesn't support effort at all)")
    # max_tokens=1024, not 40: found by actually running this that effort="max"
    # triggers real thinking-block reasoning tokens BEFORE the answer, and a
    # tight max_tokens=40 budget got entirely consumed by thinking, leaving
    # zero tokens for the actual answer text (empty string, no crash --
    # response.stop_reason below confirms it hit "max_tokens" while still
    # inside the thinking block). Higher effort needs headroom for the
    # reasoning that happens before the visible answer, not just the answer
    # itself.
    for effort in ["low", "max"]:
        print(f"\n  effort={effort}")
        for i in range(2):
            start = time.time()
            response = client.messages.create(
                model=EFFORT_MODEL,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
                output_config={"effort": effort},
            )
            response_text = _extract_text(response.content)
            elapsed = time.time() - start
            print(
                f"    call {i + 1} ({elapsed:.2f}s, stop_reason={response.stop_reason}, "
                f"blocks={[b.type for b in response.content]}): {response_text!r}"
            )

    # TODO: write a short comment here (3-5 sentences) on what you observed
    # across the three steps above:
    #   - Step 1: did temperature=0.0 actually get rejected with a 400 error,
    #     confirming the deprecation is real and not just a docs typo?
    #   - Step 2: were the three default-settings responses identical,
    #     similar-but-not-identical, or wildly different from each other?
    #     (This is the closest thing to the old "temperature=1.0" arm --
    #     there's no lower-variance arm to compare it against anymore.)
    #   - Step 3: did effort="low" vs effort="max" visibly change anything
    #     about the responses (length, care taken, variability between the 2
    #     calls at each level)? Does that feel like the same kind of control
    #     temperature used to give you, or a genuinely different axis?
    #
    # YOUR OBSERVATION (from a real run):
    #   Step 1: temperature=0.0 was ACCEPTED on Haiku 4.5, not rejected -- this
    #   model sits outside the deprecation boundary docs.claude.com describes
    #   for "models released after Claude Opus 4.6."
    #   Step 2 (Haiku 4.5, default settings, no temperature control possible):
    #   three calls produced three completely different pets and phrasings
    #   (an iguana "like a scaly parrot," a tarantula "on a leash made of silk
    #   thread," an octopus that "opens jars and recognizes his face") -- clear
    #   non-determinism persists by default, matching the old temp=1.0 arm's
    #   behavior even with no dial to turn it down anymore.
    #   Step 3 (claude-sonnet-5): effort="low" produced NO thinking block
    #   (blocks=['text']) and two calls that were nearly identical in content
    #   and wording (both "a pet octopus that solves puzzles... recognizes its
    #   owner's face", differing only in a clause and a curly quote) -- low
    #   effort converged toward a similar answer, fast (~1.5s). effort="max"
    #   DID include a real thinking block (blocks=['thinking', 'text']), took
    #   4-6x longer (6.3s/10.0s vs ~1.5s), and produced two totally different,
    #   more creative answers (a sock-hoarding fennec fox vs. a
    #   barbecue-crashing capybara). This is the opposite of what raising
    #   temperature toward "more random" would predict getting MORE similar --
    #   here, MORE effort correlated with MORE variety between calls, not
    #   less. Confirms effort is a genuinely different axis than temperature:
    #   temperature/top_p/top_k control sampling randomness at fixed
    #   computation; effort controls how much the model reasons before
    #   answering (visible as an actual thinking block at higher levels), at
    #   a real, substantial latency cost. Also confirms the earlier
    #   max_tokens=40 mystery: stop_reason=end_turn here (natural completion,
    #   not truncation) once the budget was raised to 1024 -- at effort="max"
    #   with only 40 tokens, the thinking block alone was consuming the whole
    #   budget before any answer text could be generated, producing an empty
    #   string with no error. Takeaway for real usage: budget max_tokens for
    #   thinking + answer combined at higher effort levels, not just the
    #   answer you expect to see.


if __name__ == "__main__":
    part1_estimate_tokens()
    part2_sampling_and_temperature()
