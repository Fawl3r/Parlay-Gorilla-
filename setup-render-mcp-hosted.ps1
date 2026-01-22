# Quick Setup Script for Render MCP Server (Hosted Version)
# This uses Render's hosted MCP server - no build required!

$ErrorActionPreference = "Stop"

Write-Host "🚀 Setting up Render MCP Server (Hosted Version)..." -ForegroundColor Cyan

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
        $existingContent = Get-Content $cursorConfigPath -Raw
        $config = $existingContent | ConvertFrom-Json -AsHashtable
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

# Add or update Render MCP server configuration (hosted version)
$config["mcpServers"]["render"] = @{
    url = "https://mcp.render.com/mcp"
    headers = @{
        Authorization = "Bearer <YOUR_API_KEY>"
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
Write-Host "`n✨ Done! The hosted MCP server is ready to use (no build required)." -ForegroundColor Green
Write-Host "   Advantages: Always up-to-date, no local build needed!" -ForegroundColor Gray
