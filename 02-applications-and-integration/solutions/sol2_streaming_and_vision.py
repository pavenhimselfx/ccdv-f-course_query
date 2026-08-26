"""
sol2_streaming_and_vision.py -- reference solution for ex2_streaming_and_vision.py

Assumptions/notes on SDK specifics (correct as of this writing -- verify
against docs.claude.com if behavior differs):
  - client.messages.stream(...) returns a MessageStreamManager used as a
    context manager; `.text_stream` yields plain text deltas as they arrive;
    `.get_final_message()` (called after the `with` block, or via the
    stream object) returns the fully-assembled Message once done.
  - Image content blocks use {"type": "image", "source": {"type": "base64",
    "media_type": ..., "data": ...}}.
"""

import os
import sys

MODEL = "claude-sonnet-4-5-20250929"


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


def part_a_streaming(client):
    print("\n=== Part A: Streaming ===\n")

    prompt = "List five uses for the number pi, one short sentence each."

    with client.messages.stream(
        model=MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        # This is the part that demonstrates *incremental* processing: text
        # is printed as each delta arrives, not after the whole response is
        # complete. In a real UI, each chunk would be pushed to the client
        # (e.g. over a websocket or SSE passthrough) as it's received here.
        for chunk in stream.text_stream:
            print(chunk, end="", flush=True)

        final_message = stream.get_final_message()

    print()  # newline after the streamed text
    print(f"\nFinal usage: {final_message.usage}")
    print(f"Stop reason: {final_message.stop_reason}")

    # Why streaming here: even though the total generation time for five
    # short sentences might only be a couple of seconds, the user sees the
    # FIRST sentence almost immediately instead of waiting for all five --
    # that's the UX win, independent of total cost or token count (which
    # streaming does not change).


def part_b_vision(client):
    print("\n=== Part B: Vision ===\n")

    tiny_red_png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAQAAAAECAIAAAAmkwkpAAAAFElEQVR4nGO8IyLCAANMDEgANwcANJQBDI8EgxYAAAAASUVORK5CYII="
    )

    question = "What color is this image? Answer in one word."

    response = client.messages.create(
        model=MODEL,
        max_tokens=20,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": tiny_red_png_b64,
                        },
                    },
                    {"type": "text", "text": question},
                ],
            }
        ],
    )

    print(f"Claude's answer: {response.content[0].text!r}")
    # Expected: something like "Red." -- confirming the image block was
    # actually processed, not ignored. If you swap in a different image on
    # disk, re-run and confirm the answer tracks the new image's real color/
    # content rather than staying static -- that's your check that vision
    # content blocks are doing real work, not just being silently dropped.


def main():
    client = load_client()
    part_a_streaming(client)
    part_b_vision(client)


if __name__ == "__main__":
    main()
