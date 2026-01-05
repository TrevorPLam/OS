#!/usr/bin/env bash
set -euo pipefail

KEY_PATH="${DEPLOY_KEY_PATH:-$HOME/.ssh/os_deploy_key}"
REPO_SSH_URL="${1:-}"

if [[ ! -f "${KEY_PATH}" ]]; then
  mkdir -p "$(dirname "${KEY_PATH}")"
  ssh-keygen -t ed25519 -f "${KEY_PATH}" -C "os-deploy-key" -N ""
fi

echo ""
echo "Deploy key generated:"
echo "  Private key: ${KEY_PATH}"
echo "  Public key:  ${KEY_PATH}.pub"
echo ""
echo "Add the following public key to the GitHub repo as a deploy key with write access:"
echo ""
cat "${KEY_PATH}.pub"
echo ""

if [[ -n "${REPO_SSH_URL}" ]]; then
  if git remote get-url origin >/dev/null 2>&1; then
    echo "Origin remote already configured. Update it if needed:"
    echo "  git remote set-url origin ${REPO_SSH_URL}"
  else
    git remote add origin "${REPO_SSH_URL}"
    echo "Origin remote set to ${REPO_SSH_URL}"
  fi
  echo ""
  echo "Use the deploy key to push:"
  echo "  GIT_SSH_COMMAND=\"ssh -i ${KEY_PATH} -o IdentitiesOnly=yes\" git push -u origin HEAD"
fi
