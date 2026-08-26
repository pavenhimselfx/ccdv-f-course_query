"""
SOLUTION — ex2_prompt_iteration.py — CCDV-F Module 06

Reference implementation with inline explanations. Compare against your own
attempt in exercises/ex2_prompt_iteration.py after a genuine attempt of your
own. See that file's docstring for full exercise context.
"""

import os
import sys

try:
    import anthropic
except ImportError:
    anthropic = None


MODEL = "claude-sonnet-4-5"  # verify current model name/availability at docs.claude.com

SAMPLE_TICKETS = [
    """Subject: App crashes on login
    Hi, every time I try to log in on my Android phone the app just closes.
    This started after the last update. I've tried reinstalling twice. I use
    this app for work every day so this is pretty urgent, please help asap.
    Ticket submitted by: jordan.k@example.com""",

    """Subject: billing question
    hey so i got charged twice this month for my subscription?? can someone
    look into this and refund the extra charge. not a huge emergency just
    annoying. thanks""",

    """Subject: Feature request - dark mode
    Would love to see a dark mode option in a future update. Not urgent at
    all, just a nice-to-have. Love the app otherwise!""",
]


def v0_prompt(ticket_text: str) -> dict:
    """
    Deliberately weak: no system prompt, no length/format guidance, no role.
    Expected behavior when you run this: length and focus wander from
    ticket to ticket (and can even vary a bit run to run on the SAME
    ticket), because nothing constrains what "summarize" should mean here.
    This is the baseline README section 2.1 says to avoid.
    """
    return {
        "system": None,
        "user": f"Summarize this: {ticket_text}",
    }


def v1_prompt(ticket_text: str) -> dict:
    """
    Adds:
      - A system prompt: stable role + a global rule ("always identify the
        core issue and the requested resolution") that should hold no
        matter which ticket comes in this turn -- exactly the kind of
        standing rule README section 2.3 says belongs in system, not user.
      - A clearer, more specific user instruction: names the task and gives
        a concrete length bound (1-2 sentences) instead of leaving it open.
    Expected improvement: length becomes much more consistent, and urgency/
    requested-action are reliably at least mentioned, because the system
    prompt makes "always cover these things" a standing rule instead of
    something to accidentally omit.
    """
    system = (
        "You are a customer support triage assistant. For every support "
        "ticket you are given, identify (1) the customer's core issue and "
        "(2) what resolution, if any, they are asking for. Always address "
        "both, even briefly."
    )
    user = (
        f"Summarize the following support ticket in 1-2 sentences, focusing "
        f"on the core issue and the requested resolution.\n\nTicket:\n{ticket_text}"
    )
    return {"system": system, "user": user}


def v2_prompt(ticket_text: str) -> dict:
    """
    Adds, on top of v1:
      - Explicit output-format constraints: a fixed three-line shape, and
        an explicit "nothing else" instruction (README 2.4). This is what
        makes the output SAFE TO PARSE programmatically -- the goal of
        Output Handling (Domain skill 3) starts here, at the prompt.
      - One few-shot example (README 2.2), showing the exact input/output
        pattern rather than only describing it in prose. The example is
        placed in the user turn, and the actual task ticket is placed
        AFTER it -- with the instruction restated right before the ticket
        text, so the "do this now" instruction is close to where the
        response begins (README 2.5's placement/recency point).
    """
    system = (
        "You are a customer support triage assistant. You always respond "
        "in the exact structured format you are asked for, with no "
        "additional commentary, greeting, or restated ticket text."
    )
    example_ticket = (
        "Subject: Can't reset password\nI clicked 'forgot password' three "
        "times and never got an email. I need to log in today for a client "
        "call. Please help quickly."
    )
    example_output = (
        "Issue: password reset email not arriving\n"
        "Urgency: high\n"
        "Requested action: help the customer log in / fix password reset"
    )
    user = textwrap_example(example_ticket, example_output, ticket_text)
    return {"system": system, "user": user}


def textwrap_example(example_ticket: str, example_output: str, ticket_text: str) -> str:
    return (
        "Summarize support tickets in exactly this three-line format, and "
        "output nothing else -- no greeting, no restated ticket text, no "
        "extra commentary:\n\n"
        "Issue: <one short clause>\n"
        "Urgency: <low|medium|high>\n"
        "Requested action: <one short clause, or \"none stated\" if the "
        "customer didn't ask for anything specific>\n\n"
        f"Example ticket:\n{example_ticket}\n\n"
        f"Example output:\n{example_output}\n\n"
        f"Now summarize this ticket, in the same format:\n{ticket_text}"
    )


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------

def call_claude(client, prompt_dict: dict) -> str:
    kwargs = {
        "model": MODEL,
        "max_tokens": 200,
        "messages": [{"role": "user", "content": prompt_dict["user"]}],
    }
    if prompt_dict.get("system"):
        kwargs["system"] = prompt_dict["system"]
    response = client.messages.create(**kwargs)
    return response.content[0].text


def main() -> None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or anthropic is None:
        print("ANTHROPIC_API_KEY not set (or `anthropic` package not installed).")
        print("Read the prompt strings built by v0_prompt/v1_prompt/v2_prompt")
        print("below and reason about how their outputs would differ.")
        sys.exit(0)

    client = anthropic.Anthropic(api_key=api_key)
    versions = [("v0 (weak)", v0_prompt), ("v1 (clear + system/user split)", v1_prompt),
                ("v2 (+ output constraints + few-shot)", v2_prompt)]

    for i, ticket in enumerate(SAMPLE_TICKETS, start=1):
        print(f"\n{'=' * 70}\nTICKET {i}:\n{ticket.strip()}\n{'=' * 70}")
        for label, fn in versions:
            prompt_dict = fn(ticket)
            output = call_claude(client, prompt_dict)
            print(f"\n--- {label} ---\n{output}")

    print(write_up())


def write_up() -> str:
    return """

WRITE-UP (reference observations -- your actual run's wording will differ,
but the pattern should match):

  1. v0: summary length swings from one short sentence to a full paragraph
     depending on the ticket; urgency is sometimes mentioned, sometimes not;
     sometimes the model adds a "Sure, here's a summary:" preamble and
     sometimes it doesn't. Nothing about the prompt told it these things
     mattered or what shape to use, so it's guessing every time.

  2. v1 vs v0: length becomes reliably 1-2 sentences (the explicit bound in
     the user turn), and the core issue + requested action are consistently
     both covered (the system prompt's standing rule). The system prompt is
     what makes "always cover both things" hold across EVERY ticket without
     having to repeat that rule in each user turn.

  3. v2 vs v1: the few-shot example changes FORMAT primarily -- output
     reliably becomes exactly the three "Issue:/Urgency:/Requested action:"
     lines, safe to parse with a simple split on those labels across all
     three sample tickets (including ticket 3, the feature request, where
     "requested_action" ends up close to "add dark mode" and urgency close
     to "low" -- the format holds even though the CONTENT is quite different
     from the few-shot example's urgent password-reset ticket). This is the
     key evidence that a good few-shot example teaches PATTERN, not just
     memorized content.

  4. In this comparison, the biggest single jump in consistency is usually
     v0 -> v1 (adding a system prompt + explicit length bound turns "wildly
     variable" into "roughly consistent"), while v1 -> v2 mostly turns
     "roughly consistent prose" into "reliably machine-parseable" -- both
     matter, but for different reasons: v1 addresses README skill "Prompt
     Engineering" quality; v2 is what actually makes the output usable by
     the kind of validation/parsing pipeline built in Exercise 3.
"""


if __name__ == "__main__":
    main()
