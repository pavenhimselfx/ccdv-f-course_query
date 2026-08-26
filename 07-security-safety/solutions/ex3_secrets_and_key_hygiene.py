"""
SOLUTION — ex3_secrets_and_key_hygiene.py — CCDV-F Module 07

Reference solution. See exercises/ex3_secrets_and_key_hygiene.py for the
scenario and instructions. Read that file first and make a genuine attempt
before comparing against this.

Run with:
    python ex3_secrets_and_key_hygiene.py
"""

import os


def bad_get_client():
    """DO NOT DO THIS. Kept here only as a worked "what's wrong" example."""
    import anthropic

    api_key = "sk-ant-api03-THIS-IS-A-FAKE-EXAMPLE-KEY-DO-NOT-USE-1234567890"
    print(f"Connecting to Anthropic with key: {api_key}")
    client = anthropic.Anthropic(api_key=api_key)
    return client


# Mistakes in bad_get_client(), in a teammate's own words:
#
# 1. The API key is hardcoded as a string literal in source code. The
#    moment this file is committed to version control, the key is
#    compromised — permanently, since git history retains it even after a
#    later commit deletes the line, and any clone/fork/CI log that touched
#    this commit has a copy. Automated secret-scanners (both attackers' and
#    GitHub's own) actively look for exactly this pattern in public repos.
#
# 2. There is no per-environment scoping: the same literal key would be
#    used for local dev, staging, and production alike if this function
#    were called from all three. That means one leak (e.g. a laptop
#    compromise) exposes production, and revoking/rotating the key to fix
#    it takes down every environment at once instead of just the affected
#    one — the opposite of least privilege applied to credentials.
#
# 3. The key is printed to stdout/logs (`print(f"...{api_key}")`). Any log
#    aggregator, terminal scrollback, CI job log, or error-reporting service
#    that captures stdout now has a full copy of the secret, readable by
#    everyone with access to those logs — very often a much larger audience
#    than the people who are supposed to be able to use the key itself.
#
# 4. (Related to #1) there's no fallback/guidance for what to do when a key
#    IS missing — a hardcoded key means "missing key" was never even a case
#    this code had to think about, which is a sign the design never
#    considered key management as a first-class concern at all.


def _load_dotenv_if_present() -> None:
    """Mirrors 00-setup/verify_setup.py's load_env_file(): optional, and
    silently does nothing if python-dotenv isn't installed or no .env file
    exists — exporting the var directly in your shell works fine too."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    if os.path.exists(".env"):
        load_dotenv(".env")


def good_get_client():
    """Loads the key from the environment (optionally via .env), never logs
    the value, fails loudly with actionable guidance if it's missing, and
    returns a properly constructed client."""
    import anthropic

    _load_dotenv_if_present()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Fix this by either:\n"
            "  - exporting it in your shell: export ANTHROPIC_API_KEY=your-real-key\n"
            "  - or copying .env.example to .env and filling in a real key\n"
            "See 00-setup/README.md for details."
        )

    # Safe to report presence/length — never the value itself, not even a
    # substring of it. This is enough to confirm "a key is loaded" during
    # debugging without creating a new leak path.
    print(f"ANTHROPIC_API_KEY is set ({len(api_key)} chars)")

    client = anthropic.Anthropic(api_key=api_key)
    return client


# KEY MANAGEMENT CHECKLIST
# -------------------------
# [ ] Never hardcode API keys or other secrets as string literals in source
#     code — a key committed to version control is compromised permanently,
#     even if the line is deleted in a later commit.
# [ ] Load keys from environment variables (local dev, via a gitignored
#     .env file) or a managed secret manager (production) — never bake a
#     literal key into a deploy config or container image.
# [ ] Use separate, scoped keys per environment (dev / staging / prod) so a
#     leak in one doesn't compromise the others, and each can be revoked or
#     rotated independently without taking down unrelated environments.
# [ ] Apply least privilege: where the platform supports restricted/scoped
#     keys, use the narrowest scope that gets the job done rather than a
#     broad, all-access key "for convenience."
# [ ] Rotate keys on a routine schedule, and immediately upon any suspected
#     exposure (accidental commit, log leak, departing team member) —
#     practice the rotation procedure before you need it under pressure.
# [ ] Never log, print, or include secrets in error messages/stack traces —
#     not even partially. If you need to confirm a key is present, log
#     length or a boolean, never any substring of the actual value.
# [ ] Keep .env files (and any file containing real secrets) out of version
#     control via .gitignore; only commit a .env.example template with
#     placeholder values.


def run_smoke_test():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("SKIPPED: run_smoke_test (no ANTHROPIC_API_KEY set). "
              "Review good_get_client()'s logic by reading it instead.")
        return

    client = good_get_client()
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=20,
        messages=[{"role": "user", "content": "Reply with exactly: hygiene check ok"}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    print(f"PASS: client authenticated successfully. Model said: {text.strip()}")


def check_no_hardcoded_key_in_good_client():
    import inspect

    source = inspect.getsource(good_get_client)
    assert "sk-ant-" not in source, (
        "good_get_client() appears to contain a hardcoded key literal — "
        "load it from the environment instead."
    )
    print("PASS: check_no_hardcoded_key_in_good_client")


if __name__ == "__main__":
    check_no_hardcoded_key_in_good_client()
    run_smoke_test()
    print("\nAll checks completed.")
