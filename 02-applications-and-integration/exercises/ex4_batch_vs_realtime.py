"""
ex4_batch_vs_realtime.py -- CCDV-F course, Module 02 (Claude API Mechanics)

You'll submit several independent requests via the Message Batches API,
poll until the batch finishes, and retrieve/print the results.

No API key handy yet? Read through the TODOs and predict the lifecycle a
batch goes through (submitted -> in_progress -> ended) and what you'd need
to do differently if this were five realtime calls instead.

Run with:
    python ex4_batch_vs_realtime.py

Note: batch processing is NOT instant -- Anthropic's docs describe a
processing window on the order of ~24 hours, though small batches are
often much faster in practice. This script polls with a delay and a
generous max-attempts count, but if you don't want to sit and wait, read
through the TODOs and solutions/sol4_batch_vs_realtime.py instead of
running it live end-to-end.
"""

import os
import sys
import time

MODEL = "claude-sonnet-4-5-20250929"  # pin a dated version -- see Configuration Management

# A handful of independent, non-urgent requests -- e.g. "summarize this
# ticket" run over a backlog. Nothing here depends on any other request's
# result, which is exactly the shape that's a good fit for batch.
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
        print("You can still read through this file and reason about the TODOs.")
        sys.exit(1)

    return anthropic.Anthropic(api_key=api_key)


def submit_batch(client):
    """Submit REQUESTS as one Message Batch and return the batch object.

    TODO 1: Build a list of "batch request" entries, one per item in
      REQUESTS. Each entry needs:
        - custom_id: the item's custom_id (lets you match results back up)
        - params: a dict shaped like normal messages.create() kwargs, e.g.
            {"model": MODEL, "max_tokens": 100,
             "messages": [{"role": "user", "content": item["question"]}]}

    TODO 2: Call client.messages.batches.create(requests=<the list from
      TODO 1>) and return the result. Note the returned batch object's `id`
      -- you'll need it to poll and to retrieve results.

    (Exact method/attribute names are correct as of this writing per the
    Python SDK's beta/batches interface -- if this errors with an
    AttributeError, check docs.claude.com for the current batches API
    surface, since this is a newer part of the API and naming has shifted
    before, e.g. across SDK versions that moved it in/out of a `beta`
    namespace.)
    """
    raise NotImplementedError("TODO: implement submit_batch -- see docstring above")


def poll_until_done(client, batch_id: str, max_attempts: int = 10, delay_seconds: float = 5.0):
    """Poll the batch's status until it's no longer in progress, or give up.

    TODO 3: Loop up to max_attempts times:
      - Call client.messages.batches.retrieve(batch_id) to get the current
        status.
      - Print the status (look for a `processing_status` field, values like
        "in_progress" / "ended", or an equivalent -- check the SDK's actual
        field name).
      - If the status indicates it's done, return the batch object.
      - Otherwise, sleep delay_seconds and try again.
    Return the last-seen batch object either way (caller checks status).
    """
    raise NotImplementedError("TODO: implement poll_until_done -- see docstring above")


def retrieve_results(client, batch_id: str):
    """Fetch and print each result once the batch has ended.

    TODO 4: Call client.messages.batches.results(batch_id) (this typically
      returns an iterable/stream of per-request results). For each result,
      print its custom_id and, if it succeeded, the response text; if it
      errored, print the error instead. Match each result's custom_id back
      to the original question in REQUESTS for readable output.
    """
    raise NotImplementedError("TODO: implement retrieve_results -- see docstring above")


def main():
    client = load_client()

    print(f"Submitting a batch of {len(REQUESTS)} requests...")
    batch = submit_batch(client)
    print(f"Batch submitted: id={batch.id}")

    print("Polling for completion (this may legitimately take a while)...")
    batch = poll_until_done(client, batch.id)

    print("Retrieving results...")
    retrieve_results(client, batch.id)

    # ---------------------------------------------------------------------
    # Compare and contrast (write your own notes as a comment here):
    #
    # If you did this same work as 4 sequential realtime calls in a loop,
    # what would change? (latency to see the first vs. last result, total
    # wall-clock time, per-token cost, code complexity, error-handling
    # shape)
    #
    # If you did this same work as 4 CONCURRENT realtime calls (asyncio +
    # gather -- see ex5), how would that compare to both the sequential
    # loop and to batch?
    #
    # Write down 2-3 concrete criteria you'd use to decide "batch" vs.
    # "realtime (sequential or concurrent)" for a new workload. Hint:
    # think about whether anything is waiting synchronously on the result,
    # the total volume, and how time-sensitive "non-urgent" really is for
    # your specific case.
    # ---------------------------------------------------------------------


if __name__ == "__main__":
    main()
