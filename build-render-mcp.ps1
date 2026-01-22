# Build Script for Render MCP Server
# This script builds the Render MCP server from source and sets up Cursor configuration

$ErrorActionPreference = "Stop"

Write-Host "🚀 Building Render MCP Server..." -ForegroundColor Cyan

# Check if Go is installed
Write-Host "`n📋 Checking for Go installation..." -ForegroundColor Yellow
try {
    $goVersion = go version 2>&1
    if ($LASTEXITCODE -ne 0 -or $goVersion -match "error|not found") {
        throw "Go not found"
    }
} catch {
    $goVersion = $null
}

if (-not $goVersion) {
    Write-Host "❌ Go is not installed!" -ForegroundColor Red
    Write-Host "`n📥 Please install Go 1.24.1 or later:" -ForegroundColor Yellow
    Write-Host "   1. Download from: https://go.dev/dl/" -ForegroundColor White
    Write-Host "   2. Install the Windows installer" -ForegroundColor White
    Write-Host "   3. Restart your terminal and run this script again" -ForegroundColor White
    Write-Host "`n   Or use winget: winget install GoLang.Go" -ForegroundColor Cyan
    exit 1
}

Write-Host "✅ Go found: $goVersion" -ForegroundColor Green

# Check Go version (need 1.24.1+)
$goVersionOutput = go version
if ($goVersionOutput -match 'go(\d+)\.(\d+)') {
    $major = [int]$matches[1]
    $minor = [int]$matches[2]
    if ($major -lt 1 -or ($major -eq 1 -and $minor -lt 24)) {
        Write-Host "⚠️  Warning: Go version may be too old. Recommended: 1.24.1+" -ForegroundColor Yellow
    }
}

# Set paths
$repoPath = Join-Path $PSScriptRoot ".." "render-mcp-server"
$buildOutput = Join-Path $PSScriptRoot "render-mcp-server.exe"

# Check if repository exists
if (-not (Test-Path $repoPath)) {
    Write-Host "`n📦 Cloning Render MCP Server repository..." -ForegroundColor Yellow
    $parentDir = Split-Path $PSScriptRoot -Parent
    Push-Location $parentDir
    git clone https://github.com/render-oss/render-mcp-server.git
    Pop-Location
    if (-not (Test-Path $repoPath)) {
        Write-Host "❌ Failed to clone repository!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Repository cloned" -ForegroundColor Green
}

# Build the MCP server
Write-Host "`n🔨 Building MCP server..." -ForegroundColor Yellow
Push-Location $repoPath

# Clean previous builds
if (Test-Path "render-mcp-server.exe") {
    Remove-Item "render-mcp-server.exe" -Force
}

# Build for Windows
Write-Host "   Building for Windows (amd64)..." -ForegroundColor Gray
$env:GOOS = "windows"
$env:GOARCH = "amd64"
go build -o $buildOutput .

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed!" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location

if (Test-Path $buildOutput) {
    Write-Host "✅ Build successful!" -ForegroundColor Green
    Write-Host "   Output: $buildOutput" -ForegroundColor Gray
    
    # Get file size
    $fileSize = (Get-Item $buildOutput).Length / 1MB
    Write-Host "   Size: $([math]::Round($fileSize, 2)) MB" -ForegroundColor Gray
} else {
    Write-Host "❌ Build output not found!" -ForegroundColor Red
    exit 1
}

# Create Cursor MCP configuration
Write-Host "`n⚙️  Setting up Cursor MCP configuration..." -ForegroundColor Yellow

$cursorConfigPath = Join-Path $env:USERPROFILE ".cursor" "mcp.json"
$cursorConfigDir = Split-Path $cursorConfigPath -Parent

# Create .cursor directory if it doesn't exist
if (-not (Test-Path $cursorConfigDir)) {
    New-Item -ItemType Directory -Path $cursorConfigDir -Force | Out-Null
    Write-Host "   Created .cursor directory" -ForegroundColor Gray
}

# Read existing config or create new one
$config = @{}
if (Test-Path $cursorConfigPath) {
    try {
        $config = Get-Content $cursorConfigPath -Raw | ConvertFrom-Json -AsHashtable
        Write-Host "   Found existing MCP configuration" -ForegroundColor Gray
    } catch {
        Write-Host "   Warning: Could not parse existing config, creating new one" -ForegroundColor Yellow
        $config = @{}
    }
}

# Ensure mcpServers exists
if (-not $config.ContainsKey("mcpServers")) {
    $config["mcpServers"] = @{}
}

# Add or update Render MCP server configuration
$config["mcpServers"]["render"] = @{
    command = $buildOutput
    env = @{
        RENDER_API_KEY = "<YOUR_API_KEY>"
    }
}

# Save configuration
$configJson = $config | ConvertTo-Json -Depth 10
$configJson | Set-Content $cursorConfigPath -Encoding UTF8

Write-Host "✅ Cursor configuration created/updated!" -ForegroundColor Green
Write-Host "   Config path: $cursorConfigPath" -ForegroundColor Gray

Write-Host "`n📝 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Get your Render API key from: https://dashboard.render.com/settings#api-keys" -ForegroundColor White
Write-Host "   2. Edit $cursorConfigPath" -ForegroundColor White
Write-Host "   3. Replace <YOUR_API_KEY> with your actual API key" -ForegroundColor White
Write-Host "   4. Restart Cursor to load the MCP server" -ForegroundColor White
Write-Host "`n✨ Done! The MCP server is ready to use." -ForegroundColor Green
