# GitHub Secrets for Oracle Push-to-Deploy

The **Deploy to Oracle** workflow (`.github/workflows/deploy-oracle.yml`) runs on every push to `main`. It needs these repository secrets.

## Steps

1. Open **GitHub** → your repo **Parlay-Gorilla-** → **Settings** → **Secrets and variables** → **Actions**.
2. Click **New repository secret** and add:

| Name | Value |
|------|--------|
| `ORACLE_SSH_HOST` | `147.224.172.113` |
| `ORACLE_SSH_KEY` | **Full contents** of your private key file: `C:\Users\Fawl3\.ssh\id_ed25519` (open in Notepad, copy everything including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`) |

3. (Optional) If you use a different SSH user than `ubuntu`, add:
   - Name: `ORACLE_SSH_USER`
   - Value: your username

4. Save. The next push to `main` will trigger the workflow and run `git pull` + `scripts/deploy.sh` on the VM.

## Manual deploy (without push)

SSH in and run:

```bash
cd /opt/parlaygorilla && git pull && bash scripts/deploy.sh
```

Or from PowerShell:

```powershell
ssh -i "C:\Users\Fawl3\.ssh\id_ed25519" ubuntu@147.224.172.113 "cd /opt/parlaygorilla && git pull && bash scripts/deploy.sh"
```
