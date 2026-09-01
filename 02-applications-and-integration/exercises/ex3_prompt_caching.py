"""
ex3_prompt_caching.py -- CCDV-F course, Module 02 (Claude API Mechanics)

You'll make two Messages API calls that share a large, static system-prompt
block marked with cache_control: the first call is a cache WRITE (Claude
hasn't seen this exact prefix before), the second is a cache READ (it has).
You'll inspect the `usage` field on each response to see the difference.

No API key handy yet? Read through the TODOs and predict, for each call,
whether cache_creation_input_tokens or cache_read_input_tokens should be
larger than zero, and why. Then read solutions/sol3_prompt_caching.py to
check your reasoning.

Run with:
    python ex3_prompt_caching.py

Note: prompt caching has a minimum cacheable prefix length (small prompts
won't actually get cached even if you mark them) and a short cache lifetime
(on the order of minutes) that can vary by model/tier -- if your two calls
below don't show a cache read, the most likely cause is either (a) the
static block is too short to qualify, or (b) too much time passed between
calls. Check docs.claude.com for current minimums/lifetimes.
"""

import os
import sys
import time

MODEL = "claude-sonnet-4-5-20250929"  # pin a dated version -- see Configuration Management

# A large, static block of "context" -- in a real app this might be a policy
# document, a big tool-definitions block, or a large few-shot example set.
# It needs to be long enough to clear the minimum cacheable-prefix length, so
# this is deliberately padded out with repeated filler content.
STATIC_CONTEXT = (
    "You are a support assistant for Acme Cloud. Below is the full internal "
    "escalation policy. Use it to answer questions accurately and concisely.\n\n"
    + ("Escalation policy section filler text for cache-length padding. " * 400)
    + "\n\nEnd of escalation policy."
)


def load_client():
    try:
        from dotenv import load_dotenv
        if os.path.exists(".env"):
            load_dotenv(".env")
    except ImportError:
        pass

    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY is not set -- see 00-setup/README.md.")
        print("You can still read through this file and reason about the TODOs.")
        sys.exit(1)

    return anthropic.Anthropic(api_key=api_key)


def make_call(client, question: str):
    """Make one Messages API call with STATIC_CONTEXT as a cached system block.

    TODO 1: Build the `system` parameter as a LIST containing one text block:
        {"type": "text", "text": STATIC_CONTEXT, "cache_control": {"type": "ephemeral"}}
      (Passing `system` as a list of blocks, rather than a plain string, is
      what lets you attach cache_control to it.)

    TODO 2: Call client.messages.create(model=MODEL, max_tokens=100,
      system=<the list from TODO 1>,
      messages=[{"role": "user", "content": question}])

    TODO 3: Return the response.
    """
    system = [
        {
            "type": "text",
            "text": STATIC_CONTEXT,
            "cache_control": {"type": "ephemeral"},
        }
    ]
    response = client.messages.create(
        model=MODEL,
        max_tokens=100,
        system=system,
        messages=[{"role": "user", "content": question}],
    )
    return response


def print_usage(label: str, response):
    """Print the usage fields relevant to caching."""
    usage = response.usage
    print(f"\n--- {label} ---")
    print(f"  input_tokens:              {getattr(usage, 'input_tokens', 'n/a')}")
    print(f"  output_tokens:             {getattr(usage, 'output_tokens', 'n/a')}")
    # These two fields are the ones to watch: on a cache WRITE, expect
    # cache_creation_input_tokens > 0 and cache_read_input_tokens == 0 (or
    # absent). On a cache READ, expect the reverse.
    print(f"  cache_creation_input_tokens: {getattr(usage, 'cache_creation_input_tokens', 'n/a')}")
    print(f"  cache_read_input_tokens:     {getattr(usage, 'cache_read_input_tokens', 'n/a')}")


def main():
    client = load_client()

    print("Making call #1 (expected: cache WRITE -- this exact prefix is new)...")
    response_1 = make_call(client, "In one sentence, who should a P1 outage be escalated to?")
    print_usage("Call 1 (cache write, expected)", response_1)

    # A short pause is not required, but calling back-to-back like this
    # maximizes the chance the cache is still warm for call #2.
    time.sleep(1)

    print("\nMaking call #2 (expected: cache READ -- same static prefix, different question)...")
    response_2 = make_call(client, "In one sentence, what's the SLA credit process for a P1 outage?")
    print_usage("Call 2 (cache read, expected)", response_2)

    print(
        "\nCompare the two usage blocks above. Call 1 should show tokens under "
        "cache_creation_input_tokens; call 2 should show (roughly) the same "
        "count under cache_read_input_tokens instead, with a much smaller "
        "input_tokens count of its own (just the new question)."
    )

    # TODO 4 (short answer -- write your response as a comment or in a
    # separate notes file): When is prompt caching worth using, and when is
    # it NOT worth it? Consider: call frequency, how static the shared
    # content is, the size of the static block relative to per-call unique
    # content, and the cache's short lifetime. Give one concrete example of
    # each (a good caching fit, and a poor one).


# ANSWER (TODO 4):
# Caching is worth it when a large static block gets reused across many
# calls before the cache's short lifetime expires. My own run showed this
# directly: the 5641-token STATIC_CONTEXT was written once on call 1
# (cache_creation_input_tokens=5641) and then served from cache on call 2
# for free (cache_read_input_tokens=5641, input_tokens staying tiny at 25 --
# just the new question). Good fit example: a support tool where dozens of
# agents each ask a handful of questions per hour against the same 5000-token
# policy excerpt -- large enough to clear the minimum cacheable length, and
# frequent enough (many requests within a few minutes) to keep hitting the
# cache before it goes cold.
#
# Caching is NOT worth it when the static block is small, or when it's large
# but rarely reused before expiring. Poor fit example: a 50-token system
# prompt called once an hour -- too small to qualify for caching at all, and
# even if it did, an hour between calls is far longer than the cache
# lifetime, so every call would pay the cache-write overhead and never land
# a read. The failure mode to watch for isn't just "caching does nothing" in
# that case -- cache writes aren't free, so marking content cache_control
# without enough reuse can make a system slightly worse, not neutral.


if __name__ == "__main__":
    main()
