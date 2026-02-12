#!/usr/bin/env bash
# One-time Oracle (or Ubuntu) VM bootstrap: Docker, UFW, swap, app dir.
# Run as root or with sudo. Do not store secrets in this script.
set -e

echo "[bootstrap] Installing Docker..."
apt-get update
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "${VERSION_CODENAME:-$VERSION_NAME}") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "[bootstrap] UFW (allow 22, 80, 443)..."
ufw allow 22
ufw allow 80
ufw allow 443
ufw --force enable

echo "[bootstrap] Swap 4G (if no swap)..."
if [ ! -f /swapfile ]; then
  fallocate -l 4G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "[bootstrap] App dir /opt/parlaygorilla..."
mkdir -p /opt/parlaygorilla
chown -R "$(logname 2>/dev/null || echo root):" /opt/parlaygorilla 2>/dev/null || true

echo "[bootstrap] Done. Next: clone repo into /opt/parlaygorilla, add .env (DATABASE_URL, SUI_*, etc.), then run deploy via GitHub Actions or: cd /opt/parlaygorilla && bash scripts/deploy.sh"
