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
    # TODO: write an instruction-only prompt that asks the model to classify
    # `text` into exactly one of CATEGORIES and reply with only the category
    # word. Keep it concise.
    raise NotImplementedError


def build_one_shot_prompt(text: str) -> str:
    """Exactly one worked example before the real task."""
    # TODO: write a prompt that includes ONE example input -> expected
    # category label, formatted exactly like you want the real answer
    # formatted, followed by the real `text` to classify.
    raise NotImplementedError


def build_few_shot_prompt(text: str) -> str:
    """Three or more worked examples, spanning categories/edge cases."""
    # TODO: write a prompt that includes AT LEAST THREE examples — try to
    # cover all three categories, and include at least one edge case (e.g.
    # a message that could sound billing-ish but is really technical, or
    # vice versa) — followed by the real `text` to classify.
    raise NotImplementedError


def classify(client, model: str, prompt: str) -> str:
    """Send `prompt` to the model and return the raw text reply, stripped."""
    # TODO: call client.messages.create(model=model, max_tokens=10,
    # messages=[{"role": "user", "content": prompt}]) and return
    # response.content[0].text.strip()
    raise NotImplementedError


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
    # OBSERVATIONS:
    # (write here)


if __name__ == "__main__":
    main()
