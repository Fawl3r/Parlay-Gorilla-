# Quick Oracle VM health check via SSH.
# Uses: ORACLE_SSH_HOST, ORACLE_SSH_KEY_PATH, ORACLE_SSH_USER (optional).
# Defaults match docs/github-secrets-oracle.md (do not commit real keys; key path only).
$HostIP   = if ($env:ORACLE_SSH_HOST)   { $env:ORACLE_SSH_HOST }   else { "147.224.172.113" }
$KeyPath  = if ($env:ORACLE_SSH_KEY_PATH) { $env:ORACLE_SSH_KEY_PATH } else { "$env:USERPROFILE\.ssh\id_ed25519" }
$User     = if ($env:ORACLE_SSH_USER)   { $env:ORACLE_SSH_USER }   else { "ubuntu" }

if (-not (Test-Path -LiteralPath $KeyPath)) {
    Write-Host "Key not found: $KeyPath" -ForegroundColor Red
    Write-Host "Set ORACLE_SSH_KEY_PATH or use default id_ed25519 in .ssh" -ForegroundColor Yellow
    exit 1
}

$Remote = "${User}@${HostIP}"
Write-Host "Checking Oracle VM: $Remote" -ForegroundColor Cyan
Write-Host ""

# Prefer ssh in PATH; on Windows fall back to OpenSSH locations
$sshExe = $null
if (Get-Command ssh -ErrorAction SilentlyContinue) { $sshExe = "ssh" }
if (-not $sshExe) {
    foreach ($p in @("$env:ProgramFiles\OpenSSH\ssh.exe", "$env:SystemRoot\System32\OpenSSH\ssh.exe")) {
        if (Test-Path -LiteralPath $p) { $sshExe = $p; break }
    }
}
if (-not $sshExe) {
    Write-Host "ssh not found. Install OpenSSH or run this script from Git Bash." -ForegroundColor Red
    exit 1
}

$ScriptBlock = @'
set -e
echo '=== Docker containers ==='
sudo docker compose -f /opt/parlaygorilla/docker-compose.prod.yml ps 2>/dev/null || sudo docker ps -a
echo
echo '=== Health localhost:80 ==='
curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://localhost/health || echo 'curl failed'
echo
echo '=== UFW status ==='
sudo ufw status 2>/dev/null || true
echo
echo '=== Port 80/443 listener ==='
sudo ss -tlnp | grep -E ':80 |:443 ' || true
'@

try {
    $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($ScriptBlock))
    $remoteCmd = "echo $encoded | base64 -d | bash"
    & $sshExe -i $KeyPath -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new $Remote $remoteCmd
} catch {
    Write-Host "SSH failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Done. If health returned 200, API is up on the VM." -ForegroundColor Green
Write-Host "If api.parlaygorilla.com still fails, check DNS (A record to this IP) and Cloudflare SSL (Flexible)." -ForegroundColor Gray
