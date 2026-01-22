# Test Script for Render MCP Server Configuration
# This script validates the MCP server configuration

$ErrorActionPreference = "Stop"

Write-Host "🧪 Testing Render MCP Server Configuration..." -ForegroundColor Cyan

# Check configuration file
$configPath = Join-Path $env:USERPROFILE ".cursor" "mcp.json"
Write-Host "`n📋 Checking configuration file..." -ForegroundColor Yellow

if (-not (Test-Path $configPath)) {
    Write-Host "❌ Configuration file not found: $configPath" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Configuration file exists" -ForegroundColor Green

# Parse configuration
try {
    $config = Get-Content $configPath -Raw | ConvertFrom-Json
    Write-Host "✅ Configuration file is valid JSON" -ForegroundColor Green
} catch {
    Write-Host "❌ Invalid JSON in configuration file: $_" -ForegroundColor Red
    exit 1
}

# Check for Render MCP server
if (-not $config.mcpServers.render) {
    Write-Host "❌ Render MCP server not found in configuration" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Render MCP server configuration found" -ForegroundColor Green

$renderConfig = $config.mcpServers.render

# Check configuration type (hosted or local)
if ($renderConfig.url) {
    Write-Host "✅ Using hosted MCP server" -ForegroundColor Green
    Write-Host "   URL: $($renderConfig.url)" -ForegroundColor Gray
    
    if ($renderConfig.headers.Authorization -match "<YOUR_API_KEY>") {
        Write-Host "⚠️  API key not configured (still has placeholder)" -ForegroundColor Yellow
        Write-Host "   Please update the API key in: $configPath" -ForegroundColor Gray
    } elseif ($renderConfig.headers.Authorization -match "Bearer\s+") {
        Write-Host "✅ API key appears to be configured" -ForegroundColor Green
    } else {
        Write-Host "⚠️  API key format may be incorrect" -ForegroundColor Yellow
    }
} elseif ($renderConfig.command) {
    Write-Host "✅ Using local MCP server" -ForegroundColor Green
    Write-Host "   Command: $($renderConfig.command)" -ForegroundColor Gray
    
    if (Test-Path $renderConfig.command) {
        Write-Host "✅ Executable exists" -ForegroundColor Green
    } else {
        Write-Host "❌ Executable not found: $($renderConfig.command)" -ForegroundColor Red
    }
    
    if ($renderConfig.env.RENDER_API_KEY -match "<YOUR_API_KEY>") {
        Write-Host "⚠️  API key not configured (still has placeholder)" -ForegroundColor Yellow
    } elseif ($renderConfig.env.RENDER_API_KEY) {
        Write-Host "✅ API key appears to be configured" -ForegroundColor Green
    }
} else {
    Write-Host "❌ Invalid Render MCP server configuration" -ForegroundColor Red
    Write-Host "   Must have either 'url' (hosted) or 'command' (local)" -ForegroundColor Gray
    exit 1
}

# Test network connectivity (for hosted version)
if ($renderConfig.url) {
    Write-Host "`n🌐 Testing network connectivity..." -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri $renderConfig.url -Method GET -TimeoutSec 5 -ErrorAction Stop
        Write-Host "✅ Can reach MCP server endpoint" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Could not reach MCP server endpoint: $_" -ForegroundColor Yellow
        Write-Host "   This might be normal - the server may require authentication" -ForegroundColor Gray
    }
}

# Summary
Write-Host "`n📊 Configuration Summary:" -ForegroundColor Cyan
Write-Host "   Config file: $configPath" -ForegroundColor Gray
Write-Host "   Type: $(if ($renderConfig.url) { 'Hosted' } else { 'Local' })" -ForegroundColor Gray
Write-Host "   Status: $(if ($renderConfig.headers.Authorization -match '<YOUR_API_KEY>' -or $renderConfig.env.RENDER_API_KEY -match '<YOUR_API_KEY>') { '⚠️  Needs API key' } else { '✅ Ready' })" -ForegroundColor $(if ($renderConfig.headers.Authorization -match '<YOUR_API_KEY>' -or $renderConfig.env.RENDER_API_KEY -match '<YOUR_API_KEY>') { 'Yellow' } else { 'Green' })

Write-Host "`n📝 Next Steps:" -ForegroundColor Cyan
if ($renderConfig.headers.Authorization -match "<YOUR_API_KEY>" -or $renderConfig.env.RENDER_API_KEY -match "<YOUR_API_KEY>") {
    Write-Host "   1. Get your Render API key from: https://dashboard.render.com/settings#api-keys" -ForegroundColor White
    Write-Host "   2. Update $configPath with your API key" -ForegroundColor White
    Write-Host "   3. Restart Cursor" -ForegroundColor White
    Write-Host "   4. Test in Cursor: 'List my Render workspaces'" -ForegroundColor White
} else {
    Write-Host "   1. Restart Cursor to load the MCP server" -ForegroundColor White
    Write-Host "   2. Set your workspace: 'Set my Render workspace to [NAME]'" -ForegroundColor White
    Write-Host "   3. Test with: 'List my Render services'" -ForegroundColor White
}

Write-Host "`n✨ Configuration test complete!" -ForegroundColor Green
