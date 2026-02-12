# Oracle A1 (4 OCPU / 24 GB) Auto-Provision — CLI Only

Hands-off provisioning of **one** Always Free Ampere A1 instance using OCI CLI and infinite retry until capacity is available. No Terraform, no UI, no fallback sizes.

---

## 1. OCI CLI install (Windows)

```powershell
winget install Oracle.CloudInfrastructureCLI
```

Close and reopen PowerShell, then verify:

```powershell
oci --version
```

---

## 2. OCI config setup

Create the config file and key directory:

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.oci"
notepad "$env:USERPROFILE\.oci\config"
```

**Where to fill everything in:** one file only:

**`C:\Users\Fawl3\.oci\config`**

Open it in Notepad (or run `notepad "$env:USERPROFILE\.oci\config"` in PowerShell). It should look like this — replace the angle-bracket placeholders with your real values:

```ini
[DEFAULT]
user=ocid1.user.oc1..aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
fingerprint=12:34:56:78:9a:bc:de:f0:12:34:56:78:9a:bc:de:f0
tenancy=ocid1.tenancy.oc1..aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
region=us-ashburn-1
key_file=C:\Users\Fawl3\.oci\fawl3r85@gmail.com-2026-02-08T01_19_32.365Z.pem
```

**Where to get each value (Oracle Cloud Console):**

1. **Tenancy OCID**  
   - Click your **Profile icon** (top-right, circle with your initial).  
   - In the dropdown, click the line that says **Tenancy:** followed by your tenancy name (that opens Tenancy Details; do not click your username).  
   - On the **Tenancy Details** page, under **Tenancy Information**, find **OCID** → click **Show**, then **Copy**.

2. **User OCID and fingerprint**  
   - Click **Profile icon** (top-right) → **User Settings**.  
   - In the **left sidebar**, click **API Keys**. You’ll see your key(s) and a **Fingerprint** column (e.g. `aa:bb:cc:dd:...`). Copy that fingerprint.  
   - Your **User OCID** is on the same User Settings page (top of the main area, or in the left sidebar under your name). Copy the **OCID** that starts with `ocid1.user.oc1..`  
   - **Easier:** Next to your API key, open the **Actions** menu (⋮) → **View configuration file**. Oracle shows a snippet with `user`, `fingerprint`, `tenancy`, and `region` already filled in. Copy that into your `config` file, then set `key_file` to your private `.pem` path (the one above).

3. **region**  
   - Use the same region as in the Console (e.g. `us-ashburn-1`, `us-phoenix-1`, `eu-frankfurt-1`). It’s in the region dropdown (top of the Console) or in the config snippet from “View configuration file”.

4. **key_file**  
   - Already set above. Leave it as your private `.pem` path.

Save the file, then test: `oci iam region list --output table`

**If you need to create a new key:** Generate with OpenSSL, then upload the public key in Console (Profile → User Settings → API Keys → Add API Key):

```powershell
openssl genrsa -out "$env:USERPROFILE\.oci\oci_api_key.pem" -aes128 2048
openssl rsa -pubout -in "$env:USERPROFILE\.oci\oci_api_key.pem" -out "$env:USERPROFILE\.oci\oci_api_key_public.pem"
```

Test the CLI:

```powershell
oci iam region list --output table
```

---

## 3. Run the auto-provision script

**Edit only these three variables** at the top of `scripts/oci-provision-a1-instance.ps1`:

| Variable | Where to get it |
|----------|------------------|
| `COMPARTMENT_OCID` | Oracle Console → Identity → Compartments → your compartment → OCID |
| `SUBNET_OCID` | Networking → Virtual Cloud Networks → your VCN → Subnets → public subnet → OCID |
| `SSH_PUBLIC_KEY` | Full contents of your `id_rsa.pub` (or equivalent), single line |

Then run:

```powershell
cd "c:\F3 Apps\F3 Parlay Gorilla"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
.\scripts\oci-provision-a1-instance.ps1
```

The script will:

- Use **VM.Standard.A1.Flex** with **4 OCPU and 24 GB RAM** only.
- Use Canonical Ubuntu 22.04 or 24.04.
- Try every Availability Domain in your region; on “out of capacity” it sleeps **5 minutes** and retries forever.
- Assign a **public IPv4** and your **SSH public key**.
- When launch succeeds, wait until the instance is **RUNNING**, then print Instance OCID, Public IP, and SSH command and exit.

---

## 4. Post-success output (what the script prints)

When provisioning succeeds, the script prints something like:

```
Instance OCID:     ocid1.instance.oc1....
Public IPv4:       129.146.x.x
SSH command:       ssh ubuntu@129.146.x.x
```

- This instance is **Always Free**; there is **$0/month** cost.
- Once created, capacity errors do not recur for this instance.
- The instance can run indefinitely within Always Free limits.

**Next steps:** Open ports 22, 80, 443 in the VCN security list, then follow `docs/setup-oracle-and-cloudflare.md` (SSH, bootstrap, `.env`, deploy).
