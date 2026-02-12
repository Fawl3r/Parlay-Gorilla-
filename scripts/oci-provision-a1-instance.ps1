#Requires -Version 5.1
<#
.SYNOPSIS
  Provisions ONE Oracle Always Free A1 instance (4 OCPU / 24 GB) via OCI CLI.
  Retries forever on out-of-capacity until success. No Terraform, no UI.
#>

# ============== EDIT ONLY THESE THREE ==============
$COMPARTMENT_OCID = "ocid1.tenancy.oc1..aaaaaaaagiopcp4ftczwdh7kelmvooznuibi5pwdrua5oz2sw7dv7evaypjq"
$SUBNET_OCID     = "ocid1.subnet.oc1.us-chicago-1.aaaaaaaapfx5po2o5qbp3n6lumbgglvqvplwnj2dmg77id7w4fxhm5iykpbq"
$SSH_PUBLIC_KEY  = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBkLJ2S+UO9+0rRgAW4Mgw1dIlEUEqMBJ6i0ZT/ay9ZD"
# =================================================

$ErrorActionPreference = "Stop"
# Disable pager so OCI CLI does not spawn a pager
$env:OCI_CLI_USE_PAGER = "false"
# Ensure OCI CLI can find powershell.exe (OCI CLI may spawn it; Cursor terminal often has no PowerShell on PATH)
$psDir = "C:\Windows\System32\WindowsPowerShell\v1.0"
if (Test-Path "$psDir\powershell.exe") {
    $env:Path = "$psDir;$env:Path"
}
# Ensure OCI CLI (pip install oci-cli) is on PATH
$ociPaths = @(
    "C:\Users\Fawl3\AppData\Local\Programs\Python\Python311\Scripts",
    "$env:LOCALAPPDATA\Programs\Python\Python311\Scripts"
)
foreach ($p in $ociPaths) {
    if (Test-Path "$p\oci.exe") {
        $env:Path = "$p;$env:Path"
        break
    }
}

if (-not (Get-Command oci -ErrorAction SilentlyContinue)) {
    Write-Error "OCI CLI not found. Install with: pip install oci-cli"
    exit 1
}
$DisplayName = "parlaygorilla-backend"
$Shape = "VM.Standard.A1.Flex"
$Ocpus = 4
$MemoryGB = 24
$RetrySleepSeconds = 300  # 5 minutes

function Write-Step { param([string]$Message) Write-Host ">>> $Message" -ForegroundColor Cyan }
function Write-OK   { param([string]$Message) Write-Host "OK: $Message" -ForegroundColor Green }
function Write-Warn { param([string]$Message) Write-Host "WARN: $Message" -ForegroundColor Yellow }

# Resolve latest Canonical Ubuntu 22.04 or 24.04 image (A1-compatible).
function Get-UbuntuImageId {
    Write-Step "Listing Canonical Ubuntu images (22.04 / 24.04)..."
    $raw = oci compute image list --compartment-id $COMPARTMENT_OCID `
        --operating-system "Canonical Ubuntu" `
        --limit 50 `
        --sort-order DESC `
        --output json 2>&1
    $parsed = $null
    try { $parsed = $raw | ConvertFrom-Json } catch { }
    $images = $parsed.data
    if (-not $images) {
        $raw = oci compute image list --all --compartment-id $COMPARTMENT_OCID --output json 2>&1
        try {
            $parsed = $raw | ConvertFrom-Json
            $images = $parsed.data | Where-Object { $_."operating-system" -match "Canonical Ubuntu" }
        } catch { }
    }
    if (-not $images) { throw "No Canonical Ubuntu images found. Check COMPARTMENT_OCID and OCI CLI access." }
    $match = $images | Where-Object { $_."display-name" -match "22\.04|24\.04" } | Select-Object -First 1
    if (-not $match) { throw "No Canonical Ubuntu 22.04/24.04 image found. List images in Console for your region." }
    Write-OK "Using image: $($match.'display-name') ($($match.id))"
    return $match.id
}

# Get availability domain names for the compartment.
function Get-AvailabilityDomains {
    Write-Step "Fetching Availability Domains..."
    $json = oci iam availability-domain list --compartment-id $COMPARTMENT_OCID --output json
    $ads = ($json | ConvertFrom-Json).data
    $names = $ads | ForEach-Object { $_.name }
    Write-OK "ADs: $($names -join ', ')"
    return $names
}

# Attempt to launch instance in one AD. Returns instance OCID on success; throws or returns $null on capacity error.
function Start-InstanceInAD {
    param([string]$AvailabilityDomain, [string]$ImageId)
    $launchJson = @{
        compartmentId   = $COMPARTMENT_OCID
        availabilityDomain = $AvailabilityDomain
        displayName      = $DisplayName
        shape            = $Shape
        shapeConfig      = @{ ocpus = $Ocpus; memoryInGBs = $MemoryGB }
        imageId          = $ImageId
        subnetId         = $SUBNET_OCID
        assignPublicIp   = $true
        metadata         = @{ "ssh_authorized_keys" = $SSH_PUBLIC_KEY }
    } | ConvertTo-Json -Depth 10 -Compress
    # Pass JSON inline; on Windows file:// and path often fail for --from-json
    $out = & oci compute instance launch --from-json $launchJson --output json 2>&1
    if ($LASTEXITCODE -ne 0) {
        $errText = "$out"
        if ($errText -match "capacity|OutOfHostCapacity|out of capacity|LimitExceeded|InsufficientCapacity") {
            return $null
        }
        throw "Launch failed: $errText"
    }
    $result = $out | ConvertFrom-Json
    return $result.data.id
}

# Wait until instance state is RUNNING; return instance details (including public IP).
function Wait-InstanceRunning {
    param([string]$InstanceId)
    Write-Step "Waiting for instance RUNNING..."
    $maxWait = 600
    $elapsed = 0
    while ($elapsed -lt $maxWait) {
        $json = oci compute instance get --instance-id $InstanceId --output json
        $inst = ($json | ConvertFrom-Json).data
        $state = $inst."lifecycle-state"
        if ($state -eq "RUNNING") {
            $publicIp = ""
            for ($v = 0; $v -lt 6; $v++) {
                $attachments = (oci compute instance list-vnic-attachments --compartment-id $COMPARTMENT_OCID --instance-id $InstanceId --output json | ConvertFrom-Json).data
                $vnicId = if ($attachments -and $attachments.Count -gt 0) { $attachments[0]."vnic-id" } else { $null }
                if ($vnicId) {
                    $vnic = (oci network vnic get --vnic-id $vnicId --output json | ConvertFrom-Json).data
                    $publicIp = $vnic."public-ip"
                    if ($publicIp) { break }
                }
                Start-Sleep -Seconds 5
            }
            return @{ Id = $InstanceId; PublicIp = $publicIp }
        }
        if ($state -match "TERMINAT|FAILED") { throw "Instance entered state: $state" }
        Start-Sleep -Seconds 15
        $elapsed += 15
    }
    throw "Instance did not reach RUNNING within $maxWait seconds."
}

# --- Main ---
Write-Host "Parlay Gorilla - Oracle A1 auto-provision (4 OCPU / 24 GB, Always Free)" -ForegroundColor White
Write-Host "Retry every $RetrySleepSeconds seconds on capacity errors. Ctrl+C to stop.`n" -ForegroundColor Gray

$imageId = Get-UbuntuImageId
$ads = Get-AvailabilityDomains
$instanceId = $null
$attempt = 0

while ($true) {
    $attempt++
    Write-Step "Attempt #$attempt - trying all Availability Domains..."
    foreach ($ad in $ads) {
        Write-Host "  Trying AD: $ad"
        try {
            $instanceId = Start-InstanceInAD -AvailabilityDomain $ad -ImageId $imageId
            if ($instanceId) { break }
        } catch {
            Write-Warn $_.Exception.Message
        }
    }
    if ($instanceId) { break }
    Write-Warn "No capacity in any AD. Sleeping $RetrySleepSeconds seconds..."
    Start-Sleep -Seconds $RetrySleepSeconds
}

$info = Wait-InstanceRunning -InstanceId $instanceId
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  PROVISIONED SUCCESSFULLY" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Instance OCID:  $($info.Id)"
Write-Host "Public IPv4:    $($info.PublicIp)"
Write-Host "SSH command:    ssh ubuntu@$($info.PublicIp)"
Write-Host ""
Write-Host "This instance is Always Free; \$0/month. Capacity errors will not return once created; it can run indefinitely." -ForegroundColor Gray
