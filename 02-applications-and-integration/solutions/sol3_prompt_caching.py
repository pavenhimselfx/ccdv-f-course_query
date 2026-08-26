"""
sol3_prompt_caching.py -- reference solution for ex3_prompt_caching.py

Assumptions/notes on SDK specifics (correct as of this writing -- verify
against docs.claude.com if fields differ): the `system` parameter accepts a
list of content blocks, each of which may carry a `cache_control` field;
`{"type": "ephemeral"}` is the standard cache type. The response `usage`
object exposes `cache_creation_input_tokens` and `cache_read_input_tokens`
alongside `input_tokens` / `output_tokens`.
"""

import os
import sys
import time

MODEL = "claude-sonnet-4-5-20250929"

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
        sys.exit(1)

    return anthropic.Anthropic(api_key=api_key)


def make_call(client, question: str):
    system = [
        {
            "type": "text",
            "text": STATIC_CONTEXT,
            "cache_control": {"type": "ephemeral"},
        }
    ]
    return client.messages.create(
        model=MODEL,
        max_tokens=100,
        system=system,
        messages=[{"role": "user", "content": question}],
    )


def print_usage(label: str, response):
    usage = response.usage
    print(f"\n--- {label} ---")
    print(f"  input_tokens:              {getattr(usage, 'input_tokens', 'n/a')}")
    print(f"  output_tokens:             {getattr(usage, 'output_tokens', 'n/a')}")
    print(f"  cache_creation_input_tokens: {getattr(usage, 'cache_creation_input_tokens', 'n/a')}")
    print(f"  cache_read_input_tokens:     {getattr(usage, 'cache_read_input_tokens', 'n/a')}")


def main():
    client = load_client()

    print("Making call #1 (expected: cache WRITE)...")
    response_1 = make_call(client, "In one sentence, who should a P1 outage be escalated to?")
    print_usage("Call 1 (cache write, expected)", response_1)

    time.sleep(1)

    print("\nMaking call #2 (expected: cache READ)...")
    response_2 = make_call(client, "In one sentence, what's the SLA credit process for a P1 outage?")
    print_usage("Call 2 (cache read, expected)", response_2)

    print(
        "\nExpected pattern: call 1 shows a large cache_creation_input_tokens "
        "and cache_read_input_tokens == 0. Call 2 shows the reverse -- a large "
        "cache_read_input_tokens, cache_creation_input_tokens == 0, and a small "
        "input_tokens (just the new question, since the static block was served "
        "from cache rather than reprocessed)."
    )

    # -------------------------------------------------------------------
    # TODO 4 answer (short answer):
    #
    # Caching IS worth it when:
    #   - A large block of context (system prompt, reference document, tool
    #     definitions) is IDENTICAL across many requests.
    #   - Those requests happen frequently enough to land within the cache's
    #     short lifetime (minutes, not hours) -- e.g. a support tool used
    #     continuously through the workday, not a batch job that touches
    #     the same prompt once a day.
    #   - The static block is large relative to the unique, per-call content
    #     (a 5,000-token policy document behind a 20-token question is a
    #     great fit; a 20-token system prompt behind a 20-token question is
    #     not worth the mechanism's overhead).
    #
    # Caching is NOT worth it when:
    #   - Context differs on every call (e.g. each request embeds a unique,
    #     large user-supplied document -- nothing to reuse).
    #   - Call volume/frequency is too low or sporadic to land two calls
    #     within the cache lifetime -- you'd pay the (slightly higher)
    #     cache-write cost on every call and never benefit from a read.
    #   - The static portion is small -- the savings on a short prefix don't
    #     outweigh the added complexity of managing cache_control breakpoints.
    # -------------------------------------------------------------------


if __name__ == "__main__":
    main()
