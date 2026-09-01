"""
ex2_streaming_and_vision.py — CCDV-F course, Module 02 (Claude API Mechanics)

Two small, separate tasks:

  Part A — Streaming: make a Messages API call with stream=True and process the
  response incrementally, printing text as it arrives instead of waiting for the
  full completion.

  Part B — Vision: send an image alongside a question using an image content
  block, and print Claude's answer.

No API key handy yet? You can still do this exercise by reading: for Part A, trace
through the TODOs and predict what streaming event types you'd see and in what
order. For Part B, read the content-block shape and predict what happens if you
swap the image for one that doesn't contain the thing you asked about.

Run with:
    python ex2_streaming_and_vision.py
"""

import base64
import os
import sys

MODEL = "claude-sonnet-4-5-20250929"  # pin a dated version -- see Configuration Management


def load_client():
    """Small shared helper: load .env if present, return an anthropic.Anthropic client."""
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


def part_a_streaming(client):
    """Stream a response and print text as it arrives."""
    print("\n=== Part A: Streaming ===\n")

    prompt = "List five uses for the number pi, one short sentence each."

    # TODO 1: Use client.messages.stream(...) as a context manager, passing
    #   model=MODEL, max_tokens=300, messages=[{"role": "user", "content": prompt}]
    #
    # TODO 2: Inside the `with` block, iterate `stream.text_stream` and print
    #   each chunk of text as it arrives (use `print(chunk, end="", flush=True)`
    #   so you can actually see it stream rather than appearing all at once).
    #
    # TODO 3: After the loop, call `stream.get_final_message()` (or the
    #   equivalent on the stream object) to get the completed Message, and
    #   print its `.usage` field so you can see input/output token counts.
    #
    # Hint on the shape of what you're iterating: the raw event stream carries
    # distinct event types (message_start, content_block_start,
    # content_block_delta, content_block_stop, message_delta, message_stop).
    # `stream.text_stream` is a convenience the SDK provides that filters this
    # down to just the text deltas -- know that the raw events exist even if
    # you use the convenience wrapper here.

    with client.messages.stream(
        model=MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for chunk in stream.text_stream:
            print(chunk, end="", flush=True)
        final_message = stream.get_final_message()

    print("\n\nUsage:", final_message.usage)


def part_b_vision(client):
    """Send an image alongside a question using a vision content block."""
    print("\n=== Part B: Vision ===\n")

    # A tiny 4x4 solid-red PNG, base64-encoded, so this exercise doesn't depend
    # on any external image file. Feel free to swap this for a real image on
    # disk (read the bytes, base64-encode them, keep the media_type accurate).
    tiny_red_png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAQAAAAECAIAAAAmkwkpAAAAFElEQVR4nGO8IyLCAANMDEgANwcANJQBDI8EgxYAAAAASUVORK5CYII="
    )

    question = "What color is this image? Answer in one word."

    # TODO 4: Build a `messages` list with one user turn whose `content` is a
    #   LIST of content blocks (not a plain string), containing:
    #     - an image block:
    #         {"type": "image", "source": {"type": "base64",
    #          "media_type": "image/png", "data": tiny_red_png_b64}}
    #     - a text block:
    #         {"type": "text", "text": question}
    #
    # TODO 5: Call client.messages.create(model=MODEL, max_tokens=20,
    #   messages=...) with that content list and print response.content[0].text
    #
    # Optional extension: load a real image file from disk instead
    # (e.g. with open("some.jpg", "rb") as f: data = base64.b64encode(f.read())
    #  .decode("utf-8")), and ask a real question about it.

    messages = [
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
    ]

    response = client.messages.create(
        model=MODEL,
        max_tokens=20,
        messages=messages,
    )
    print(response.content[0].text)


def main():
    client = load_client()
    part_a_streaming(client)
    part_b_vision(client)


if __name__ == "__main__":
    main()
