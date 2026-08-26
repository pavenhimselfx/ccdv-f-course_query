"""
sol4_batch_vs_realtime.py -- reference solution for ex4_batch_vs_realtime.py

Assumptions/notes on SDK specifics (correct as of this writing -- this is a
newer part of the API surface and naming has been more prone to change than
core messages.create, so verify against docs.claude.com):
  - client.messages.batches.create(requests=[...]) submits a batch. Each
    entry in `requests` has `custom_id` and `params` (params mirrors normal
    messages.create kwargs).
  - client.messages.batches.retrieve(batch_id) returns current status; the
    field used here to check completion is `processing_status`, with a
    value of "ended" once done (vs. "in_progress" while running).
  - client.messages.batches.results(batch_id) returns an iterable of
    per-request results once the batch has ended; each result has
    `custom_id` and a `result` with a `type` of "succeeded" / "errored" and
    (on success) a `message` shaped like a normal Messages API response.
"""

import os
import sys
import time

MODEL = "claude-sonnet-4-5-20250929"

REQUESTS = [
    {"custom_id": "ticket-1", "question": "Summarize in one sentence: customer can't reset password after 3 attempts."},
    {"custom_id": "ticket-2", "question": "Summarize in one sentence: customer billed twice for the same invoice."},
    {"custom_id": "ticket-3", "question": "Summarize in one sentence: customer wants to upgrade from Basic to Pro plan."},
    {"custom_id": "ticket-4", "question": "Summarize in one sentence: customer reports the mobile app crashes on launch."},
]


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


def submit_batch(client):
    batch_requests = [
        {
            "custom_id": item["custom_id"],
            "params": {
                "model": MODEL,
                "max_tokens": 100,
                "messages": [{"role": "user", "content": item["question"]}],
            },
        }
        for item in REQUESTS
    ]
    return client.messages.batches.create(requests=batch_requests)


def poll_until_done(client, batch_id: str, max_attempts: int = 10, delay_seconds: float = 5.0):
    for attempt in range(1, max_attempts + 1):
        batch = client.messages.batches.retrieve(batch_id)
        print(f"  poll {attempt}/{max_attempts}: status={batch.processing_status}")
        if batch.processing_status == "ended":
            return batch
        time.sleep(delay_seconds)
    print("  gave up waiting -- batch may still be processing; check back later "
          "with client.messages.batches.retrieve(batch_id).")
    return batch


def retrieve_results(client, batch_id: str):
    questions_by_id = {item["custom_id"]: item["question"] for item in REQUESTS}

    for entry in client.messages.batches.results(batch_id):
        question = questions_by_id.get(entry.custom_id, "<unknown>")
        if entry.result.type == "succeeded":
            text = entry.result.message.content[0].text
            print(f"  [{entry.custom_id}] Q: {question}\n      A: {text}")
        else:
            print(f"  [{entry.custom_id}] Q: {question}\n      ERROR: {entry.result}")


def main():
    client = load_client()

    print(f"Submitting a batch of {len(REQUESTS)} requests...")
    batch = submit_batch(client)
    print(f"Batch submitted: id={batch.id}")

    print("Polling for completion (this may legitimately take a while)...")
    batch = poll_until_done(client, batch.id)

    if getattr(batch, "processing_status", None) == "ended":
        print("Retrieving results...")
        retrieve_results(client, batch.id)
    else:
        print("Batch not finished within polling window in this run -- that's "
              "expected/normal behavior for batch, not a bug. Re-run "
              "poll_until_done later, or check docs.claude.com's guidance on "
              "typical completion times for small batches.")

    # -------------------------------------------------------------------
    # Compare and contrast:
    #
    # Sequential realtime loop: total wall-clock time is roughly
    # (4 x per-call latency), and you get each ticket's result as soon as
    # its own call finishes -- useful if something needs to react to
    # ticket-1's result before ticket-4 is even sent. Cost: full realtime
    # rate on all 4 calls.
    #
    # Concurrent realtime (ex5, asyncio.gather): wall-clock time closer to
    # (1 x per-call latency) since all 4 run in parallel, at the cost of
    # more complex code and needing to mind rate limits. Still full
    # realtime rate on all 4 calls -- concurrency changes WHEN you pay
    # latency, not the per-token price.
    #
    # Batch: no one is waiting synchronously, so the ~24h-scale processing
    # window is a non-issue for this use case (nightly ticket triage), and
    # you get a meaningful cost discount plus effectively unlimited
    # throughput without managing your own concurrency/rate-limit logic.
    #
    # Decision criteria:
    #   1. Is a human or synchronous system waiting on each individual
    #      result right now? If yes -> realtime (sequential or concurrent
    #      depending on volume/independence). If no -> batch is worth
    #      strongly considering.
    #   2. What's the volume? A handful of items barely matters either way;
    #      thousands of items pushes hard toward batch for the cost
    #      discount and to avoid self-managing large-scale concurrency/rate
    #      limiting.
    #   3. How firm is "non-urgent"? If "non-urgent" secretly means "within
    #      the hour," check the batch API's actual current completion-time
    #      characteristics against that need before committing to it --
    #      don't assume worst-case ~24h always applies, but don't assume
    #      it's always fast either.
    # -------------------------------------------------------------------


if __name__ == "__main__":
    main()
