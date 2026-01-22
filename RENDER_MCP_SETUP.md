# Render MCP Server Setup Guide

This guide helps you build and configure the Render MCP (Model Context Protocol) server for use with Cursor.

## Prerequisites

1. **Go Programming Language** (version 1.24.1 or later)
   - Download: https://go.dev/dl/
   - Or install via winget: `winget install GoLang.Go`
   - Verify: `go version`

2. **Git** (for cloning the repository)
   - Usually pre-installed on Windows
   - Verify: `git --version`

3. **Render API Key**
   - Get from: https://dashboard.render.com/settings#api-keys
   - ⚠️ **Important**: API keys are broadly scoped and grant access to all workspaces and services

## Quick Setup

### Option 1: Automated Build Script (Recommended)

Run the PowerShell build script:

```powershell
.\build-render-mcp.ps1
```

This script will:
- Check for Go installation
- Clone the Render MCP server repository
- Build the executable
- Create/update Cursor MCP configuration

### Option 2: Manual Build

1. **Clone the repository:**
   ```powershell
   cd ..
   git clone https://github.com/render-oss/render-mcp-server.git
   cd render-mcp-server
   ```

2. **Build the executable:**
   ```powershell
   $env:GOOS = "windows"
   $env:GOARCH = "amd64"
   go build -o ..\F3 Parlay Gorilla\render-mcp-server.exe .
   ```

3. **Configure Cursor:**
   - Edit `~/.cursor/mcp.json` (or `%USERPROFILE%\.cursor\mcp.json`)
   - Add the following configuration:

   ```json
   {
     "mcpServers": {
       "render": {
         "command": "C:\\F3 Apps\\F3 Parlay Gorilla\\render-mcp-server.exe",
         "env": {
           "RENDER_API_KEY": "YOUR_API_KEY_HERE"
         }
       }
     }
   }
   ```

## Configuration

### Cursor MCP Configuration File

Location: `%USERPROFILE%\.cursor\mcp.json`

Example configuration:

```json
{
  "mcpServers": {
    "render": {
      "command": "C:\\F3 Apps\\F3 Parlay Gorilla\\render-mcp-server.exe",
      "env": {
        "RENDER_API_KEY": "rnd_xxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

### Using the Hosted MCP Server (Alternative)

Instead of building locally, you can use Render's hosted MCP server:

```json
{
  "mcpServers": {
    "render": {
      "url": "https://mcp.render.com/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY_HERE"
      }
    }
  }
}
```

**Advantages of hosted version:**
- Automatically updates with new capabilities
- No local build required
- Always uses the latest version

## Usage

After setup:

1. **Restart Cursor** to load the MCP server
2. **Set your workspace** with a prompt like:
   ```
   Set my Render workspace to [WORKSPACE_NAME]
   ```
3. **Start using MCP tools** with prompts like:
   - "List my Render services"
   - "Show me the logs for my backend service"
   - "Query my database for recent user signups"
   - "What's the CPU usage for my frontend service?"

## Troubleshooting

### Build Issues

**Error: "go: command not found"**
- Install Go from https://go.dev/dl/
- Restart your terminal after installation
- Verify with `go version`

**Error: "go version too old"**
- Update Go to version 1.24.1 or later
- Download from: https://go.dev/dl/

**Build fails with module errors**
- Run: `go mod download`
- Then: `go mod tidy`
- Try building again

### Configuration Issues

**MCP server not appearing in Cursor**
- Verify the config file path: `%USERPROFILE%\.cursor\mcp.json`
- Check JSON syntax is valid
- Restart Cursor completely
- Check Cursor logs for errors

**API Key Issues**
- Verify your API key is correct
- Ensure the key has proper permissions
- Get a new key from: https://dashboard.render.com/settings#api-keys

**Workspace not found**
- List workspaces: "List my Render workspaces"
- Set workspace: "Set my Render workspace to [NAME]"

## Available MCP Tools

The Render MCP server provides tools for:

- **Workspaces**: List, select, get details
- **Services**: Create, list, get details, update env vars
- **Deployments**: List deploy history, get deploy details
- **Logs**: Query logs with filters, list log label values
- **Metrics**: Get performance metrics (CPU, memory, requests, etc.)
- **Postgres**: Create databases, query databases, list instances
- **Key Value**: Create instances, list instances, get details

See the [official documentation](https://render.com/docs/mcp-server) for complete details.

## Security Notes

⚠️ **Important Security Considerations:**

- Render API keys are **broadly scoped** - they grant access to all workspaces and services
- The MCP server can modify environment variables (potentially destructive)
- Be cautious when sharing your API key
- Consider using the hosted MCP server for automatic security updates

## Next Steps

1. ✅ Build the MCP server (this guide)
2. ✅ Configure Cursor with your API key
3. ✅ Set your Render workspace
4. ✅ Start using MCP tools in Cursor!

For more information, see:
- [Render MCP Server Docs](https://render.com/docs/mcp-server)
- [GitHub Repository](https://github.com/render-oss/render-mcp-server)
- [Model Context Protocol](https://modelcontextprotocol.io/introduction)
