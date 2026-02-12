# Run OCI region list. Installs oci-cli via pip if needed.
$python = 'C:\Users\Fawl3\AppData\Local\Programs\Python\Python311\python.exe'
$oci = Join-Path (Split-Path $python) 'Scripts\oci.exe'

if (-not (Test-Path $oci)) {
    Write-Host "Installing OCI CLI (one-time)..."
    & $python -m pip install oci-cli --quiet
    $oci = Join-Path (Split-Path $python) 'Scripts\oci.exe'
}

if (Test-Path $oci) {
    & $oci iam region list --output table
} else {
    Write-Host "Trying 'oci' from PATH..."
    oci iam region list --output table
}
