#!/usr/bin/env bash
set -Eeuo pipefail
# Prerequisite: The .ssh files must be mounted to ~/.sshtemplate before running this script.
#  "source=${localEnv:HOME}/.ssh,target=/home/container-user/.sshtemplate,type=bind,readonly,consistency=cached"
# Copy all SSH files from template to ~/.ssh and set permissions

TEMPLATE_DIR="${HOME}/.sshtemplate"
SSH_DIR="${HOME}/.ssh"

if command -v tree >/dev/null 2>&1; then
  tree "${TEMPLATE_DIR}" || true
else
  ls -la "${TEMPLATE_DIR}" || true
fi

if [ ! -d "${TEMPLATE_DIR}" ]; then
  echo "Template dir not found: ${TEMPLATE_DIR}"
  exit 1
fi

if [ ! -f "${TEMPLATE_DIR}/config" ]; then
  echo "Can't find your ./sshtemplate/config file"
  exit 1
fi

mkdir -p "${SSH_DIR}" || {
  echo "ERROR: creating SSH dir failed" >&2
  exit 1
}

# Copy entries individually, skipping "agent" (holds live SSH-agent socket
# files, e.g. from 1Password, that can be created/removed by the host between
# listing and copying). Sockets can't be usefully copied anyway, and letting
# one failed entry abort the whole cp meant permissions below never got set.
shopt -s dotglob nullglob
for entry in "${TEMPLATE_DIR}"/*; do
  name="$(basename "${entry}")"
  [ "${name}" = "." ] || [ "${name}" = ".." ] && continue
  [ "${name}" = "agent" ] && continue
  cp -rf "${entry}" "${SSH_DIR}/" 2>/dev/null || echo "WARNING: skipping ${name} (failed to copy)" >&2
done
shopt -u dotglob nullglob

if [ ! -f "${SSH_DIR}/config" ]; then
  echo "ERROR: copying SSH template failed" >&2
  exit 1
fi

chmod 700 "${SSH_DIR}"
find "${SSH_DIR}" -mindepth 1 -type d -exec chmod 700 {} + 2>/dev/null || true
find "${SSH_DIR}" -mindepth 1 -type f -exec chmod 600 {} + 2>/dev/null || true
echo "SSH files copied from .sshtemplate."
