"""
verify_setup.py — CCDV-F course, Module 00

Confirms that your local environment is ready for the rest of this course:
  1. Your ANTHROPIC_API_KEY is available (from the shell environment, or a
     local .env file loaded via python-dotenv).
  2. The `anthropic` package is installed and importable.
  3. You can actually reach the Claude API and get a response back.

Run it with:
    python verify_setup.py

Note: exact SDK method names/signatures (e.g. client.messages.create) are
correct as of this writing but the SDK evolves — if something here throws
an AttributeError or TypeError that doesn't match the hints below, check
docs.claude.com for what changed.
"""

import os
import sys


def load_env_file() -> None:
    """Load a local .env file if python-dotenv and a .env file are present.

    This is optional: if you've already exported ANTHROPIC_API_KEY in your
    shell, there's nothing for this to do. It only helps when you're using
    the .env-file approach described in README.md.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        # python-dotenv isn't installed. That's fine as long as the key is
        # already in the environment some other way (e.g. `export ...`).
        return

    if os.path.exists(".env"):
        load_dotenv(".env")


def main() -> int:
    load_env_file()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("FAILED: ANTHROPIC_API_KEY is not set.\n")
        print("Troubleshooting:")
        print("  - Did you export it in this shell? Try:")
        print('      export ANTHROPIC_API_KEY="sk-ant-...your-key..."')
        print("  - Or, if you're using a .env file, does it exist in this")
        print("    directory (copied from .env.example) and contain a real key?")
        print("  - Is python-dotenv installed? (pip install -r requirements.txt)")
        return 1

    try:
        import anthropic
    except ImportError:
        print("FAILED: the `anthropic` package is not installed.\n")
        print("Troubleshooting:")
        print("  - Activate your virtual environment, then run:")
        print("      pip install -r requirements.txt")
        return 1

    try:
        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=16,
            messages=[
                {"role": "user", "content": "Reply with the single word: ready"}
            ],
        )

        # The Messages API returns a list of content blocks; for a simple
        # text reply, the text lives on the first block.
        reply_text = response.content[0].text

        print("SUCCESS: got a response from the Claude API.\n")
        print(f"  Model responded: {reply_text!r}")
        print("\nYour environment is set up correctly. You're ready for the")
        print("rest of this course.")
        return 0

    except anthropic.AuthenticationError:
        print("FAILED: authentication error — your API key was rejected.\n")
        print("Troubleshooting:")
        print("  - Double-check the key was copied correctly (no extra spaces")
        print("    or missing characters) into your environment or .env file.")
        print("  - Has the key been revoked or deleted in the console? Create")
        print("    a fresh one at console.anthropic.com > API Keys.")
        return 1

    except anthropic.PermissionDeniedError:
        print("FAILED: permission denied.\n")
        print("Troubleshooting:")
        print("  - Your key may not have access to the requested model, or")
        print("    your organization may have restrictions in place. Check")
        print("    the console for details.")
        return 1

    except anthropic.RateLimitError:
        print("FAILED: rate limited.\n")
        print("Troubleshooting:")
        print("  - You've hit a rate or usage limit. Wait a bit and retry, or")
        print("    check usage/limits in the console's billing dashboard.")
        return 1

    except anthropic.APIConnectionError:
        print("FAILED: could not connect to the Claude API.\n")
        print("Troubleshooting:")
        print("  - Check your internet connection.")
        print("  - If you're behind a corporate proxy or firewall, make sure")
        print("    HTTPS access to api.anthropic.com is allowed, and that any")
        print("    required proxy environment variables (HTTPS_PROXY, etc.)")
        print("    are set correctly.")
        return 1

    except anthropic.APIStatusError as e:
        print(f"FAILED: the API returned an error (status {e.status_code}).\n")
        print("Troubleshooting:")
        print("  - Read the error detail below for specifics.")
        print("  - Check docs.claude.com or the console status page if this")
        print("    looks like a service-side issue rather than something in")
        print("    your request.")
        print(f"\n  Detail: {e}")
        return 1

    except Exception as e:  # noqa: BLE001 - deliberately broad, this is a diagnostic script
        print("FAILED: an unexpected error occurred.\n")
        print(f"  {type(e).__name__}: {e}")
        print("\nTroubleshooting:")
        print("  - If this mentions an unknown parameter or method, the SDK")
        print("    may have changed since this script was written — check")
        print("    docs.claude.com for the current API reference.")
        print("  - Otherwise, re-read the error message above; it usually")
        print("    names the specific problem.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
