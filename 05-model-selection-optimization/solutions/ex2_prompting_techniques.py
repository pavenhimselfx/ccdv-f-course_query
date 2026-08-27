"""
ex2_prompting_techniques.py — SOLUTION — CCDV-F course, Module 05

Reference solution comparing zero-shot, one-shot, and few-shot prompting
for a small support-ticket classification task.
"""

import os

TEST_INPUTS = [
    "I was charged twice for my subscription this month, please refund one charge.",
    "The app crashes every time I try to upload a photo larger than 5MB.",
    "Just wanted to say I love the new dashboard redesign, great work!",
    "My invoice PDF won't download, it just spins forever.",
    "Can you add dark mode to the mobile app in a future release?",
]

CATEGORIES = ["billing", "technical", "other"]


def build_zero_shot_prompt(text: str) -> str:
    return (
        "Classify the following customer support message into exactly one of these "
        "categories: billing, technical, other.\n"
        "Reply with only the category word, nothing else.\n\n"
        f"Message: {text}\n"
        "Category:"
    )


def build_one_shot_prompt(text: str) -> str:
    return (
        "Classify the following customer support message into exactly one of these "
        "categories: billing, technical, other.\n"
        "Reply with only the category word, nothing else.\n\n"
        "Example:\n"
        "Message: I think I was overcharged on my last invoice.\n"
        "Category: billing\n\n"
        f"Message: {text}\n"
        "Category:"
    )


def build_few_shot_prompt(text: str) -> str:
    # Three examples spanning all categories, including one edge case
    # (a message that mentions an invoice/PDF but is really a technical
    # download bug, not a billing dispute) to help the model discriminate.
    return (
        "Classify the following customer support message into exactly one of these "
        "categories: billing, technical, other.\n"
        "Reply with only the category word, nothing else.\n\n"
        "Example 1:\n"
        "Message: I think I was overcharged on my last invoice.\n"
        "Category: billing\n\n"
        "Example 2:\n"
        "Message: The export button does nothing when I click it on Firefox.\n"
        "Category: technical\n\n"
        "Example 3:\n"
        "Message: Thanks for the quick support last week, you all rock!\n"
        "Category: other\n\n"
        "Example 4 (edge case - mentions an invoice but is a download bug, not billing):\n"
        "Message: My invoice PDF from March won't open, the file seems corrupted.\n"
        "Category: technical\n\n"
        f"Message: {text}\n"
        "Category:"
    )


def classify(client, model: str, prompt: str) -> str:
    response = client.messages.create(
        model=model,
        max_tokens=10,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ANTHROPIC_API_KEY is not set — skipping live comparison.")
        return

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    model = "claude-haiku-4-5"  # TODO (learner): verify current model name

    builders = {
        "zero-shot": build_zero_shot_prompt,
        "one-shot": build_one_shot_prompt,
        "few-shot": build_few_shot_prompt,
    }

    results: dict[str, list[tuple[str, str, int]]] = {name: [] for name in builders}

    for style_name, builder in builders.items():
        print(f"\n=== {style_name} ===")
        for text in TEST_INPUTS:
            prompt = builder(text)
            label = classify(client, model, prompt)
            prompt_len_chars = len(prompt)
            results[style_name].append((text, label, prompt_len_chars))
            print(f"  [{label:10}] (~{prompt_len_chars // 4:4} est. tokens) {text[:60]}")

    # OBSERVATIONS (representative — your exact run may differ, but the
    # qualitative pattern below is what this exercise is designed to show):
    #
    # - Zero-shot usually gets the "obvious" cases right (clear billing
    #   complaint, clear crash report, clear compliment) but is the most
    #   likely of the three to stumble on the edge-case-flavored input in
    #   this test set (the invoice-PDF-won't-download message, which
    #   mentions "invoice" but is really a technical download bug) — with
    #   only an instruction and no worked example, the model has to infer
    #   the exact category boundary from the category *names* alone.
    # - One-shot tends to lock in the exact output format reliably (just
    #   the bare category word, matching the one example's format) and
    #   usually improves accuracy a bit over zero-shot, but with only one
    #   example the model still hasn't seen a demonstration of the tricky
    #   billing-vs-technical boundary.
    # - Few-shot, which explicitly includes the ambiguous invoice/PDF-style
    #   edge case as one of its worked examples, is the most consistent at
    #   getting that specific edge case right, and generally the most
    #   format-consistent of the three across the whole test set.
    # - Cost: the few-shot prompt is roughly 4-5x the character count (and
    #   therefore roughly 4-5x the estimated input tokens) of the zero-shot
    #   prompt in this example, purely from the added example text. At low
    #   volume that's negligible; at 100,000 tickets/day it's a meaningful,
    #   multiplied-by-100,000 difference in input-token cost every single
    #   day, even though output is capped small (max_tokens=10) either way.
    # - Recommendation: for THIS task (a small, fixed category set where
    #   the edge cases are foreseeable and worth encoding as examples),
    #   few-shot is worth shipping — the accuracy gain on the hard edge
    #   cases outweighs the added prompt cost, especially paired with a
    #   cheap/fast model tier (see Exercise 3) to keep the multiplied cost
    #   low. If the task were simpler (no realistic ambiguous cases),
    #   zero-shot would likely be the better cost/quality tradeoff.


if __name__ == "__main__":
    main()
