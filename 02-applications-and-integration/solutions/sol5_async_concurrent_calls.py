"""
sol5_async_concurrent_calls.py -- reference solution for ex5_async_concurrent_calls.py

Assumptions/notes on SDK specifics: anthropic.AsyncAnthropic mirrors the sync
client's interface with async methods (`await client.messages.create(...)`),
and supports use as an async context manager for cleanup.
"""

import asyncio
import os
import sys
import time

MODEL = "claude-sonnet-4-5-20250929"

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
        sys.exit(1)
    return api_key


def run_sequential(api_key: str):
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    results = []
    for item in ITEMS:
        response = client.messages.create(
            model=MODEL,
            max_tokens=60,
            messages=[{"role": "user", "content": item}],
        )
        results.append(response.content[0].text)
    return results


async def run_concurrent(api_key: str):
    import anthropic

    async with anthropic.AsyncAnthropic(api_key=api_key) as client:

        async def ask(item: str) -> str:
            response = await client.messages.create(
                model=MODEL,
                max_tokens=60,
                messages=[{"role": "user", "content": item}],
            )
            return response.content[0].text

        # gather() fires every ask(item) coroutine essentially at once and
        # returns results in the SAME ORDER as the input iterable, even
        # though completion order under the hood may differ -- that's why
        # this is preferable to as_completed() here, where we want results
        # aligned back to ITEMS by position.
        results = await asyncio.gather(*(ask(item) for item in ITEMS))
        return list(results)


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
        f"(concurrency overlaps the network-wait time of each call; each "
        f"call is I/O-bound, not CPU-bound, which is exactly the situation "
        f"asyncio is designed to speed up)."
    )

    # -------------------------------------------------------------------
    # Short answer:
    #
    # asyncio concurrency and the batch API both avoid one-at-a-time
    # sequential waiting, but they solve different problems:
    #   - asyncio concurrency still uses the REALTIME endpoint (no cost
    #     discount), requires your process to stay up and connected for
    #     the duration, and gets you results back in roughly one call's
    #     worth of wall-clock time -- ideal when something (a user, a
    #     downstream step) needs the results soon, and the item count is
    #     small enough to not seriously strain rate limits.
    #   - batch is for large volume with nobody waiting synchronously: it's
    #     cheaper per token, doesn't require your process to hold a
    #     connection open the whole time (submit now, come back later), and
    #     scales to far larger item counts without you hand-rolling
    #     concurrency/backoff logic -- at the cost of a much longer,
    #     variable completion window.
    #
    # Rule of thumb: a handful to a few dozen items where a human/system is
    # waiting -> asyncio concurrency. Hundreds to millions of items, nobody
    # waiting synchronously -> batch.
    # -------------------------------------------------------------------


if __name__ == "__main__":
    main()
