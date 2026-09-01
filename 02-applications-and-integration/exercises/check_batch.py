"""Small helper: check a batch's status and print results if it's done.

Usage:
    python check_batch.py <batch_id>
"""

import sys

from ex4_batch_vs_realtime import load_client, retrieve_results

if __name__ == "__main__":
    batch_id = sys.argv[1]
    client = load_client()
    batch = client.messages.batches.retrieve(batch_id)
    print("processing_status:", batch.processing_status)
    if batch.processing_status == "ended":
        retrieve_results(client, batch.id)
    else:
        print("Still not done -- wait a bit and re-run this same command.")
