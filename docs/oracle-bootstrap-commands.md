# Oracle VM: Bootstrap + Clone Commands

Run these on the Oracle VM after SSH (e.g. `ssh ubuntu@<PUBLIC_IP>`).

---

## Where to get the VM IP and SSH private key

**VM public IP**

- When the provision script (`oci-provision-a1-instance.ps1`) succeeded, it printed something like:
  - `Public IPv4:    129.146.x.x`
  - `SSH command:    ssh ubuntu@129.146.x.x`
- If you didn’t save it: **Oracle Cloud Console** → **Menu** → **Compute** → **Instances** → click your instance (`parlaygorilla-backend`) → under **Primary VNIC** you’ll see **Public IP address**.

**SSH private key**

- The provision script used the **public** key you set in `SSH_PUBLIC_KEY` (in `oci-provision-a1-instance.ps1`). You need the **matching private key** on your PC.
- Typical locations on Windows:
  - `C:\Users\<You>\.ssh\id_ed25519` (private) if you use the default ed25519 key
  - `C:\Users\<You>\.ssh\id_rsa` (private) if you use RSA
  - Or wherever you created the key pair whose `.pub` you pasted into the script
- You use it like: `ssh -i "C:\Users\Fawl3\.ssh\id_ed25519" ubuntu@129.146.x.x`

---

## 1. Clone, bootstrap, then fix ownership

```bash
# Install git, clone repo, run bootstrap (Docker, UFW, swap), then fix ownership
sudo apt-get update && sudo apt-get install -y git
sudo git clone https://github.com/Fawl3r/Parlay-Gorilla-.git /opt/parlaygorilla
sudo bash /opt/parlaygorilla/scripts/server_bootstrap.sh
sudo chown -R ubuntu:ubuntu /opt/parlaygorilla
```

If the repo is **private**, use an SSH URL and a deploy key, or clone on your machine and SCP the tree.

## 2. Create `.env` on the VM

```bash
cd /opt/parlaygorilla
nano .env
```

Paste your production `.env` (same as Render). **Add this line for OCI** so the Python verifier runs on the VM:

```bash
VERIFICATION_DELIVERY=db
```

Save (Ctrl+O, Enter, Ctrl+X).

## 3. Deploy

From your laptop (push to `main` with GitHub secrets set) or on the VM:

```bash
cd /opt/parlaygorilla
bash scripts/deploy.sh
```

Then check: `docker compose -f docker-compose.prod.yml ps` — you should see `api`, `verifier`, `nginx`.
