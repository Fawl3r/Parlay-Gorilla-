#!/usr/bin/env bash
# Upload backend/.env to Oracle VM so the backend has the same env as local (e.g. Stripe test API).
# Usage (from repo root):
#   ORACLE_HOST=your-vm.example.com ./backend/scripts/upload_env_to_oracle.sh
#   ORACLE_HOST=your-vm.example.com ORACLE_SSH_KEY_PATH=~/.ssh/oracle_deploy ./backend/scripts/upload_env_to_oracle.sh
#
# After upload, SSH to the VM and apply (backup, replace, restart). See script output.

set -euo pipefail

HOST="${ORACLE_HOST:-${ORACLE_SSH_HOST:-}}"
USER="${ORACLE_USER:-ubuntu}"
KEY_PATH="${ORACLE_SSH_KEY_PATH:-}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
ENV_PATH="$BACKEND_DIR/.env"

if [[ ! -f "$ENV_PATH" ]]; then
  echo "ERROR: backend/.env not found at: $ENV_PATH" >&2
  exit 1
fi

if [[ -z "$HOST" ]]; then
  echo "ERROR: Set ORACLE_HOST or ORACLE_SSH_HOST (e.g. your VM hostname or IP)." >&2
  exit 1
fi

DEST="${USER}@${HOST}:/tmp/backend.env.uploaded"
echo "Uploading $ENV_PATH to $DEST ..."

if [[ -n "$KEY_PATH" ]] && [[ -f "$KEY_PATH" ]]; then
  scp -o StrictHostKeyChecking=accept-new -i "$KEY_PATH" "$ENV_PATH" "$DEST"
else
  scp -o StrictHostKeyChecking=accept-new "$ENV_PATH" "$DEST"
fi

echo ""
echo "Upload done. Run the next steps ON THE ORACLE VM (SSH in first):"
echo "  ssh $USER@$HOST   (add -i <key> if needed)"
echo ""
echo "Then on the VM run:"
echo "  sudo cp /etc/parlaygorilla/backend.env /etc/parlaygorilla/backend.env.bak"
echo "  sudo cp /tmp/backend.env.uploaded /etc/parlaygorilla/backend.env"
echo "  sudo systemctl restart parlaygorilla-backend   # or parlaygorilla-api if that is what you have"
echo "  # If 'Unit not found': install the systemd unit (see docs/deploy/VM_OPS_VERIFY_RUNBOOK.md, section 0)"
echo ""
echo "If your local .env has different DATABASE_URL or REDIS_URL, do NOT replace;"
echo "instead merge only needed vars (e.g. STRIPE_*) into /etc/parlaygorilla/backend.env"
