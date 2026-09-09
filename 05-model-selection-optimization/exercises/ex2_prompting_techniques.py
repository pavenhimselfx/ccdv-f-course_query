"""
ex2_prompting_techniques.py — CCDV-F course, Module 05 (LLM Fundamentals)

Goal: run the SAME task three ways — zero-shot, one-shot, and few-shot (3+
examples) — and compare output quality/consistency and prompt cost.

Task for this exercise: classify a short piece of customer-support text into
exactly one of three categories: "billing", "technical", "other". This is a
deliberately small, easy-to-eyeball classification task so you can focus on
comparing the three prompting styles rather than on a hard task itself.

This exercise needs ANTHROPIC_API_KEY set to run the live comparison (see
00-setup). If you don't have a key yet, read through the TODOs, write out by
hand what you predict each prompt style would produce for the test inputs,
and note that prediction in the OBSERVATIONS section — then come back and
actually run it once you have a key.

Run with:
    python ex2_prompting_techniques.py
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
    """No examples — just an instruction."""
    return (
        "Classify the following customer support message into exactly one "
        "category: billing, technical, or other. Reply with only the "
        "category word, nothing else.\n\n"
        f"Message: {text}"
    )


def build_one_shot_prompt(text: str) -> str:
    """Exactly one worked example before the real task."""
    return (
        "Classify the following customer support message into exactly one "
        "category: billing, technical, or other. Reply with only the "
        "category word, nothing else.\n\n"
        "Message: I was double-billed for my last order, can I get a refund?\n"
        "Category: billing\n\n"
        f"Message: {text}\n"
        "Category:"
    )


def build_few_shot_prompt(text: str) -> str:
    """Three or more worked examples, spanning categories/edge cases."""
    return (
        "Classify the following customer support message into exactly one "
        "category: billing, technical, or other. Reply with only the "
        "category word, nothing else.\n\n"
        "Message: I was double-billed for my last order, can I get a refund?\n"
        "Category: billing\n\n"
        "Message: The export button does nothing when I click it.\n"
        "Category: technical\n\n"
        "Message: Your support team was really helpful yesterday, thanks!\n"
        "Category: other\n\n"
        # Edge case: mentions payment (sounds billing-ish) but the actual
        # problem is a software error, not an account/charge issue.
        "Message: My payment page keeps throwing a 500 error when I try to "
        "update my card.\n"
        "Category: technical\n\n"
        f"Message: {text}\n"
        "Category:"
    )


def classify(client, model: str, prompt: str) -> str:
    """Send `prompt` to the model and return the raw text reply, stripped."""
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
        print("Fill in the TODOs, write your predictions in OBSERVATIONS below,")
        print("then re-run once you have a key.")
        return

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    # TODO: pick a model. A smaller/cheaper tier is fine for this exercise;
    # check docs.claude.com for the current model name.
    model = "claude-haiku-4-5"

    builders = {
        "zero-shot": build_zero_shot_prompt,
        "one-shot": build_one_shot_prompt,
        "few-shot": build_few_shot_prompt,
    }

    # Track prompt length (as a rough cost proxy) alongside outputs.
    results: dict[str, list[tuple[str, str, int]]] = {name: [] for name in builders}

    for style_name, builder in builders.items():
        print(f"\n=== {style_name} ===")
        for text in TEST_INPUTS:
            prompt = builder(text)
            label = classify(client, model, prompt)
            prompt_len_chars = len(prompt)
            results[style_name].append((text, label, prompt_len_chars))
            print(f"  [{label:10}] (~{prompt_len_chars // 4:4} est. tokens) {text[:60]}")

    # TODO: write a short comparison here (4-6 sentences) covering:
    #   - Did zero-shot ever produce an unexpected/invalid label (something
    #     other than exactly "billing"/"technical"/"other", or an
    #     inconsistent format)?
    #   - Did one-shot and few-shot look more consistent/well-formatted?
    #   - How much bigger was the few-shot prompt than the zero-shot prompt,
    #     roughly, in estimated tokens? What does that mean for cost if this
    #     ran on thousands of tickets per day?
    #   - Given the tradeoff, which style would you actually ship for this
    #     task, and why?
    #
    # OBSERVATIONS (from a real run against claude-haiku-4-5):
    #   Zero-shot never produced an invalid or malformed label -- all five
    #   inputs got exactly one of billing/technical/other, correctly
    #   formatted, on the first try. One-shot and few-shot produced the
    #   IDENTICAL five labels, with no visible improvement in consistency or
    #   formatting over zero-shot. This is a genuinely useful negative
    #   result, not a failed experiment: for a strong model on a small,
    #   clearly-specified 3-category task, extra examples bought nothing
    #   measurable here, including on the deliberate near-miss input
    #   ("invoice PDF won't download" -- correctly technical, not billing,
    #   even zero-shot).
    #   Cost scaled clearly with example count: zero-shot ran ~54-60 est.
    #   tokens/call, one-shot ~78-84 (~1.4x), few-shot ~144-150 (~2.5-2.7x
    #   zero-shot). At real volume (thousands of tickets/day), few-shot's
    #   prompt-token cost for this task would run roughly 2.5x zero-shot's
    #   for identical output quality on this test set.
    #   Given that tradeoff, I'd ship zero-shot for this specific task: same
    #   correct output, ~40% of the token cost. Important caveat: this
    #   conclusion rests on only 5 curated test inputs. Before fully trusting
    #   it in production, I'd want to validate zero-shot against a larger,
    #   messier sample of real tickets (more ambiguous phrasing, multiple
    #   issues in one message) rather than assume 5 clean examples generalize
    #   -- few-shot's real value tends to show up precisely on the harder,
    #   more ambiguous cases a small hand-picked test set is unlikely to
    #   contain by construction.


if __name__ == "__main__":
    main()
