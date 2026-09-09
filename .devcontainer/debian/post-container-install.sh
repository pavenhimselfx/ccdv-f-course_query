#!/usr/bin/env bash
# Runs once per container creation (devcontainer.json postCreateCommand).
#
# Only things that cannot be baked into the image belong here: files in
# $HOME, mounted volumes, and downloads too large for an image layer.
# Anything installable as a root apt package belongs in Dockerfile.debian.
set -u

export NVM_DIR="$HOME/.nvm"
# shellcheck disable=SC1091
[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

SCRIPTS_DIR="/xyz/.devcontainer/scripts"

# Docker creates fresh volumes owned by root, which leaves the tools that own
# these directories unable to write to them. Must run before the steps below
# that write into ~/.ssh and ~/.config/gh.
sudo chown -R container-user:container-user \
  "$HOME/.claude" \
  "$HOME/.claude-json" \
  "$HOME/.continue" \
  "$HOME/.gemini" \
  "$HOME/.copilot" \
  "$HOME/.gh" \
  "$HOME/.ssh" \
  "$HOME/.sshtemplate" 2>/dev/null || true


git config --global --add safe.directory /xyz || true

bash "$SCRIPTS_DIR/copy-ssh-files.sh"
bash "$SCRIPTS_DIR/remove-userkeychain.sh" "$HOME/.ssh/config"
bash "$SCRIPTS_DIR/install-global-npm-tools.sh"

echo "Post container install script done running"
