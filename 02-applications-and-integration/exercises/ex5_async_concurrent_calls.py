"""
ex5_async_concurrent_calls.py -- CCDV-F course, Module 02
(Software Engineering Foundations + Claude API Mechanics)

You'll write two versions of "ask Claude about N independent items":
  1. A naive SEQUENTIAL version using the sync client in a for loop.
  2. A CONCURRENT version using asyncio + the async client + asyncio.gather.

Then compare their wall-clock time and think about when this pattern is the
right call versus the batch API (ex4).

No API key handy yet? Read through the TODOs and predict, before running
anything: for 5 independent calls that each take ~1-2 seconds of server
time, roughly how long should the sequential version take vs. the
concurrent version, and why?

Run with:
    python ex5_async_concurrent_calls.py
"""

import asyncio
import os
import sys
import time

MODEL = "claude-sonnet-4-5-20250929"  # pin a dated version -- see Configuration Management

ITEMS = [
    "Explain what a REST API is, in one sentence.",
    "Explain what JSON is, in one sentence.",
    "Explain what an async function is, in one sentence.",
    "Explain what version control is, in one sentence.",
    "Explain what a code review is, in one sentence.",
]


def load_api_key():
    try:
        from dotenv import load_dotenv
        if os.path.exists(".env"):
            load_dotenv(".env")
    except ImportError:
        pass

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY is not set -- see 00-setup/README.md.")
        print("You can still read through this file and reason about the TODOs.")
        sys.exit(1)
    return api_key


def run_sequential(api_key: str):
    """Ask about each item in ITEMS one at a time, using the sync client.

    TODO 1: import anthropic, create anthropic.Anthropic(api_key=api_key).

    TODO 2: Loop over ITEMS; for each, call client.messages.create(model=MODEL,
      max_tokens=60, messages=[{"role": "user", "content": item}]) and
      collect response.content[0].text into a results list, in order.

    TODO 3: Return the results list.
    """
    raise NotImplementedError("TODO: implement run_sequential -- see docstring above")


async def run_concurrent(api_key: str):
    """Ask about each item in ITEMS concurrently, using the async client.

    TODO 4: import anthropic, create anthropic.AsyncAnthropic(api_key=api_key).

    TODO 5: Write a small async helper `async def ask(item): ...` that awaits
      client.messages.create(...) with the same params as run_sequential,
      and returns response.content[0].text.

    TODO 6: Use `await asyncio.gather(*(ask(item) for item in ITEMS))` to
      fire all requests concurrently and collect results IN ORDER (gather
      preserves input order in its output, which is one reason to prefer it
      here over e.g. asyncio.as_completed when order matters to you).

    TODO 7: Return the results list.

    Note: remember to close the async client when you're done with it if
    your SDK version requires it (e.g. `await client.close()`), or use it
    as an async context manager (`async with anthropic.AsyncAnthropic(...)
    as client:`) so cleanup happens automatically.
    """
    raise NotImplementedError("TODO: implement run_concurrent -- see docstring above")


def main():
    api_key = load_api_key()

    print(f"Asking about {len(ITEMS)} independent items, sequentially...")
    start = time.perf_counter()
    seq_results = run_sequential(api_key)
    seq_elapsed = time.perf_counter() - start
    for text in seq_results:
        print(f"  - {text}")
    print(f"Sequential wall-clock time: {seq_elapsed:.2f}s")

    print(f"\nAsking about {len(ITEMS)} independent items, concurrently...")
    start = time.perf_counter()
    conc_results = asyncio.run(run_concurrent(api_key))
    conc_elapsed = time.perf_counter() - start
    for text in conc_results:
        print(f"  - {text}")
    print(f"Concurrent wall-clock time: {conc_elapsed:.2f}s")

    print(
        f"\nSpeedup: {seq_elapsed / conc_elapsed:.1f}x "
        f"(expect meaningfully faster concurrent, though not a perfect "
        f"5x -- there's still per-request overhead, and you may hit "
        f"rate limits that throttle real-world concurrency)."
    )

    # ---------------------------------------------------------------------
    # Short answer (write as a comment): asyncio concurrency and the batch
    # API (ex4) both let you handle multiple Claude calls without doing
    # them one-at-a-time-and-waiting. What's actually different between
    # them? Consider: does anything need the results back within seconds?
    # Does your process need to stay running and connected the whole time?
    # Is there a cost discount? At what volume (5 items? 5,000? 5 million?)
    # does one clearly beat the other, and why?
    # ---------------------------------------------------------------------


if __name__ == "__main__":
    main()
