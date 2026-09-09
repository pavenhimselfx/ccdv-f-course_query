#!/usr/bin/env bash
set -euo pipefail

# Default global tools. You can override by passing package names as arguments.
PACKAGES=(
	"typescript@7.0.2"
	"@github/copilot"
)

if ! command -v npm >/dev/null 2>&1; then
	echo "Error: npm is not installed or not on PATH." >&2
	exit 1
fi

if [[ $# -gt 0 ]]; then
	PACKAGES=("$@")
fi

echo "Installing global npm tools..."
for pkg in "${PACKAGES[@]}"; do
	echo " - $pkg"
	npm install -g "$pkg"
done

# echo "Installing Claude Code..."
# npm install -g --allow-scripts="@anthropic-ai/claude-code" "@anthropic-ai/claude-code"

echo "Global npm tool installation complete."
