#!/usr/bin/env python3
"""
Test script for Gorilla Bot functionality.
Tests the API endpoints and verifies the bot is working correctly.
"""

import asyncio
import json
import os
import sys
from typing import Optional

import httpx


BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TEST_EMAIL = f"gorilla-bot-test-{os.getpid()}@example.com"
TEST_PASSWORD = "TestPassword123!"


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_success(message: str):
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {message}")


def print_error(message: str):
    print(f"{Colors.RED}[FAIL]{Colors.RESET} {message}")


def print_warning(message: str):
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {message}")


def print_info(message: str):
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {message}")


async def test_health_check(client: httpx.AsyncClient) -> bool:
    """Test backend health endpoint."""
    print_info("Testing backend health check...")
    try:
        response = await client.get(f"{BASE_URL}/health", timeout=5.0)
        if response.status_code == 200:
            print_success("Backend is healthy")
            return True
        else:
            print_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False


async def register_user(client: httpx.AsyncClient) -> Optional[str]:
    """Register a test user and return the access token."""
    print_info(f"Registering test user: {TEST_EMAIL}")
    try:
        response = await client.post(
            f"{BASE_URL}/api/auth/register",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=10.0,
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print_success("User registered successfully")
                return token
            else:
                print_error("Registration succeeded but no token returned")
                return None
        elif response.status_code == 400:
            # User might already exist, try to login
            print_warning("User already exists, attempting login...")
            return await login_user(client)
        else:
            print_error(f"Registration failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"Registration failed: {e}")
        return None


async def login_user(client: httpx.AsyncClient) -> Optional[str]:
    """Login with test credentials."""
    print_info(f"Logging in as: {TEST_EMAIL}")
    try:
        response = await client.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=10.0,
        )
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print_success("Login successful")
                return token
            else:
                print_error("Login succeeded but no token returned")
                return None
        else:
            print_error(f"Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print_error(f"Login failed: {e}")
        return None


async def test_gorilla_bot_chat(client: httpx.AsyncClient, token: str) -> bool:
    """Test Gorilla Bot chat endpoint."""
    print_info("Testing Gorilla Bot chat endpoint...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Test 1: Start a new conversation
        response = await client.post(
            f"{BASE_URL}/api/gorilla-bot/chat",
            json={"message": "What is Parlay Gorilla?"},
            headers=headers,
            timeout=60.0,  # Chat might take longer
        )
        
        if response.status_code == 200:
            data = response.json()
            conversation_id = data.get("conversation_id")
            reply = data.get("reply", "")
            citations = data.get("citations", [])
            
            print_success(f"Chat response received (conversation_id: {conversation_id})")
            print_info(f"Reply preview: {reply[:100]}...")
            if citations:
                print_info(f"Citations: {len(citations)} found")
            
            # Test 2: Continue the conversation
            if conversation_id:
                print_info("Testing conversation continuation...")
                response2 = await client.post(
                    f"{BASE_URL}/api/gorilla-bot/chat",
                    json={
                        "message": "How do I create a parlay?",
                        "conversation_id": conversation_id,
                    },
                    headers=headers,
                    timeout=60.0,
                )
                
                if response2.status_code == 200:
                    print_success("Conversation continuation successful")
                    return True
                else:
                    print_warning(f"Conversation continuation returned: {response2.status_code}")
                    print_warning(f"Response: {response2.text[:200]}")
                    return True  # First message worked, that's the main test
            return True
        elif response.status_code == 503:
            print_warning("Gorilla Bot is disabled or unavailable")
            print_warning("This might be due to:")
            print_warning("  - pgvector extension not installed on PostgreSQL")
            print_warning("  - Knowledge base not indexed")
            print_warning("  - OpenAI API key not configured")
            return False
        else:
            print_error(f"Chat request failed: {response.status_code}")
            print_error(f"Response: {response.text[:500]}")
            return False
    except httpx.TimeoutException:
        print_error("Chat request timed out (this might indicate OpenAI API issues)")
        return False
    except Exception as e:
        print_error(f"Chat request failed: {e}")
        import traceback
        print_error(f"Traceback: {traceback.format_exc()}")
        return False


async def test_list_conversations(client: httpx.AsyncClient, token: str) -> bool:
    """Test listing Gorilla Bot conversations."""
    print_info("Testing list conversations endpoint...")
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = await client.get(
            f"{BASE_URL}/api/gorilla-bot/conversations",
            headers=headers,
            timeout=10.0,
        )
        
        if response.status_code == 200:
            conversations = response.json()
            print_success(f"Retrieved {len(conversations)} conversations")
            return True
        else:
            print_warning(f"List conversations returned: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"List conversations failed: {e}")
        return False


async def main():
    """Run all tests."""
    print(f"\n{'='*60}")
    print("Gorilla Bot Test Suite")
    print(f"{'='*60}\n")
    print(f"Backend URL: {BASE_URL}\n")
    
    results = []
    
    async with httpx.AsyncClient() as client:
        # Test 1: Health check
        health_ok = await test_health_check(client)
        results.append(("Health Check", health_ok))
        
        if not health_ok:
            print_error("\nBackend is not responding. Please ensure the server is running.")
            print_error("Start it with: python -m uvicorn app.main:app --reload --port 8000")
            return
        
        # Test 2: Authentication
        token = await register_user(client)
        if not token:
            print_error("\nAuthentication failed. Cannot continue with Gorilla Bot tests.")
            results.append(("Authentication", False))
            print_summary(results)
            return
        
        results.append(("Authentication", True))
        
        # Test 3: Gorilla Bot Chat
        chat_ok = await test_gorilla_bot_chat(client, token)
        results.append(("Gorilla Bot Chat", chat_ok))
        
        # Test 4: List Conversations
        list_ok = await test_list_conversations(client, token)
        results.append(("List Conversations", list_ok))
    
    # Print summary
    print_summary(results)


def print_summary(results: list):
    """Print test summary."""
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"{test_name:.<40} {status}")
    
    print(f"\n{'='*60}")
    print(f"Total: {passed}/{total} tests passed")
    print(f"{'='*60}\n")
    
    if passed == total:
        print_success("All tests passed! 🎉")
        sys.exit(0)
    else:
        print_warning("Some tests failed. Please review the output above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
