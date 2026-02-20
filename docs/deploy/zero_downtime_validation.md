# Zero-Downtime Deploy — Validation Checklist

How to confirm slot switch, deployed version, manual rollback, and how to inspect the deploy log.

## Confirm active slot

The running app is served from `/opt/parlaygorilla/current`, which is a symlink to either `blue` or `green`:

```bash
readlink -f /opt/parlaygorilla/current
# Example: /opt/parlaygorilla/releases/blue
```

Or:

```bash
ls -la /opt/parlaygorilla/current
# Should show: current -> releases/blue (or releases/green)
```

## Confirm deployed version (git SHA)

The `/ops/version` endpoint returns the deployed commit and service info:

```bash
curl -sS http://127.0.0.1:8000/ops/version
```

Example response:

```json
{
  "git_sha": "a1b2c3d",
  "build_time": "2025-02-20T12:00:00Z",
  "environment": "production",
  "service": "parlaygorilla-backend"
}
```

From outside the VM, use your public API URL (e.g. `https://api.example.com/ops/version`).

## Manual rollback

If a deploy went wrong and you need to revert to the previous slot without re-running the full script:

1. See which slot is current (e.g. `green`).
2. Switch the symlink to the other slot (e.g. `blue`) and restart the service:

   ```bash
   sudo ln -sfn /opt/parlaygorilla/releases/blue /opt/parlaygorilla/current
   sudo systemctl restart parlaygorilla-backend
   ```

3. Confirm health:

   ```bash
   curl -fsS http://127.0.0.1:8000/ops/version
   ```

## Inspect deploy log

All deploy steps are logged with timestamps:

```bash
cat /var/log/parlaygorilla/deploy.log
```

Or follow during a deploy:

```bash
tail -f /var/log/parlaygorilla/deploy.log
```

If the log directory is not writable by the deploy user, the script falls back to `/opt/parlaygorilla/deploy.log`.

## Lock file

Only one deploy runs at a time. The lock file is:

```bash
/opt/parlaygorilla/.deploy.lock
```

If a deploy was killed and the lock is stuck, remove it only when you are sure no other deploy is running:

```bash
rm -f /opt/parlaygorilla/.deploy.lock
```

## Quick health check

- **Liveness:** `curl -sS http://127.0.0.1:8000/healthz`
- **Version (deploy verification):** `curl -sS http://127.0.0.1:8000/ops/version`
