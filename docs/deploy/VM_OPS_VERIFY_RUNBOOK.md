# VM runbook: confirm backend.env and restart after env upload

Run these on the **Oracle VM** (host `147.224.172.113`). SSH from your **Windows** machine (where your key is):  
`ssh -i <path-to-your-private-key> ubuntu@147.224.172.113`  
(Do not SSH from another Linux host unless that host has the deploy key.)

---

## 0. If "Unit parlaygorilla-backend.service not found"

The systemd unit is not installed. One-time install on the Oracle VM:

**0a. Create user and ensure app dir exists (if not already done)**

```bash
sudo useradd -r -s /bin/false -d /opt/parlaygorilla parlaygorilla 2>/dev/null || true
sudo mkdir -p /opt/parlaygorilla/releases/blue /opt/parlaygorilla/releases/green
sudo chown -R parlaygorilla:parlaygorilla /opt/parlaygorilla
```

**0b. Get the service file onto the VM**

Either the repo is already on the VM at `/opt/parlaygorilla/current` (after a deploy). Then:

```bash
sudo cp /opt/parlaygorilla/current/docs/systemd/parlaygorilla-backend.service /etc/systemd/system/
```

Or from your **Windows** machine (repo root):

```powershell
scp -i <key> docs/systemd/parlaygorilla-backend.service ubuntu@147.224.172.113:/tmp/
```

Then on the VM:

```bash
sudo cp /tmp/parlaygorilla-backend.service /etc/systemd/system/
```

**0c. Reload and enable**

```bash
sudo systemctl daemon-reload
sudo systemctl enable parlaygorilla-backend
sudo systemctl start parlaygorilla-backend
sudo systemctl status parlaygorilla-backend --no-pager
```

If `/opt/parlaygorilla/current` does not exist or has no backend/venv yet, run a deploy first (GitHub Actions "Deploy Backend (Oracle Blue/Green)" or run `deploy_bluegreen.sh` on the VM).

---

## 1. Verify file placement

```bash
ls -l /etc/parlaygorilla/backend.env
```

Expected: file exists. For CI deploy to source it, it must be readable by the deploy user: `sudo chgrp ubuntu /etc/parlaygorilla/backend.env && sudo chmod 640 /etc/parlaygorilla/backend.env` (one-time if currently 600 root-only).

```bash
grep -q OPS_VERIFY_TOKEN /etc/parlaygorilla/backend.env && echo "OPS_VERIFY_TOKEN present" || echo "OPS_VERIFY_TOKEN missing"
```

Do not paste the token value.

## 2. Restart backend and check status

```bash
sudo systemctl restart parlaygorilla-backend
sudo systemctl status parlaygorilla-backend --no-pager
```

Expected: `active (running)`.

## 3. From your machine (with token in env)

```bash
curl -fsS -H "x-ops-token: $OPS_VERIFY_TOKEN" https://api.parlaygorilla.com/ops/verify
```

Expected: `{"ok":true,"git_sha":"<commit>"}`. If 403, token mismatch or service not restarted.
