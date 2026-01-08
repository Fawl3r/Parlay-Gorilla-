#!/usr/bin/env python3
"""
Run Alembic migrations on Render using the Render API.

This script uses the Render API to execute commands on your service.
Requires RENDER_API_KEY environment variable.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from typing import Dict, Any, Optional


RENDER_API_BASE = "https://api.render.com/v1"


def get_api_key() -> str:
    """Get Render API key from environment."""
    api_key = os.getenv("RENDER_API_KEY")
    if not api_key:
        print("❌ Error: RENDER_API_KEY environment variable not set")
        print("\nTo get your API key:")
        print("1. Go to https://dashboard.render.com")
        print("2. Click your profile → Account Settings → API Keys")
        print("3. Create a new API key")
        print("4. Set it: $env:RENDER_API_KEY='your-key-here' (PowerShell)")
        sys.exit(1)
    return api_key


def make_api_request(
    method: str, path: str, api_key: str, data: Optional[Dict] = None
) -> Dict[str, Any]:
    """Make a request to the Render API."""
    url = f"{RENDER_API_BASE}{path}"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    
    if data:
        headers["Content-Type"] = "application/json"
        req_data = json.dumps(data).encode()
    else:
        req_data = None
    
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        try:
            error_json = json.loads(error_body)
            error_msg = error_json.get("message", error_body)
        except:
            error_msg = error_body
        raise Exception(f"API Error {e.code}: {error_msg}")


def list_services(api_key: str) -> list:
    """List all services."""
    print("Fetching services...")
    services = make_api_request("GET", "/services", api_key)
    return services


def find_backend_service(api_key: str) -> Optional[Dict]:
    """Find the backend service."""
    services = list_services(api_key)
    
    for service in services:
        name = service.get("name", "").lower()
        if "backend" in name or "parlay-gorilla-backend" in name:
            return service
    
    # If not found by name, list all and let user choose
    print("\nAvailable services:")
    for i, service in enumerate(services):
        print(f"  {i+1}. {service.get('name')} ({service.get('type')})")
    
    return None


def run_shell_command(api_key: str, service_id: str, command: str) -> str:
    """
    Run a shell command on a Render service.
    
    Note: Render API doesn't directly support running shell commands.
    This is a placeholder - we'll need to use SSH or the dashboard.
    """
    print(f"\n⚠️  Render API doesn't support direct command execution.")
    print(f"   Use one of these methods instead:\n")
    print(f"   1. Render Dashboard → {service_id} → Shell")
    print(f"   2. Render CLI: render ssh {service_id}")
    print(f"   3. Manual deployment trigger\n")
    
    # Alternative: Trigger a deployment which will run migrations via start.sh
    print("Triggering deployment to run migrations via start.sh...")
    try:
        result = make_api_request("POST", f"/services/{service_id}/deploys", api_key, {})
        deploy_id = result.get("deploy", {}).get("id")
        print(f"✅ Deployment triggered: {deploy_id}")
        print(f"   Monitor at: https://dashboard.render.com/web/{service_id}/deploys/{deploy_id}")
        return deploy_id
    except Exception as e:
        print(f"❌ Failed to trigger deployment: {e}")
        return ""


def main():
    """Main function."""
    print("=" * 60)
    print("Render Migration Runner")
    print("=" * 60)
    print()
    
    api_key = get_api_key()
    
    # Find backend service
    print("Finding backend service...")
    service = find_backend_service(api_key)
    
    if not service:
        print("❌ Could not find backend service automatically")
        print("   Please run migrations manually via Render Dashboard Shell")
        return 1
    
    service_id = service.get("id")
    service_name = service.get("name")
    
    print(f"✅ Found service: {service_name} ({service_id})")
    
    # Since Render API doesn't support direct command execution,
    # we'll trigger a deployment which will run migrations via start.sh
    print("\n" + "=" * 60)
    print("Running Migrations")
    print("=" * 60)
    print("\nSince Render API doesn't support direct shell commands,")
    print("we'll trigger a new deployment which will run migrations")
    print("automatically via the start.sh script.\n")
    
    deploy_id = run_shell_command(api_key, service_id, "alembic upgrade head")
    
    if deploy_id:
        print("\n" + "=" * 60)
        print("Next Steps")
        print("=" * 60)
        print("1. Wait for deployment to complete (check Render dashboard)")
        print("2. Verify migrations ran by checking logs for:")
        print("   '[STARTUP] Running Alembic migrations...'")
        print("3. Test endpoints:")
        print("   python scripts/validate_production_migrations.py")
        return 0
    else:
        print("\n❌ Failed to trigger deployment")
        print("\nManual steps:")
        print("1. Go to https://dashboard.render.com")
        print(f"2. Navigate to service: {service_name}")
        print("3. Click 'Shell' tab")
        print("4. Run: alembic upgrade head")
        return 1


if __name__ == "__main__":
    sys.exit(main())



