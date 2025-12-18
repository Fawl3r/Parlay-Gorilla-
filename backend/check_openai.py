"""Quick script to check OpenAI configuration"""
import os
from dotenv import load_dotenv

load_dotenv('.env')

openai_key = os.getenv('OPENAI_API_KEY')
openai_enabled = os.getenv('OPENAI_ENABLED', 'true').lower() == 'true'

print(f"OPENAI_ENABLED: {openai_enabled}")
print(f"OPENAI_API_KEY: {'SET' if openai_key else 'MISSING'}")
if openai_key:
    print(f"OPENAI_API_KEY length: {len(openai_key)}")
    print(f"OPENAI_API_KEY prefix: {openai_key[:10]}...")

if not openai_key and openai_enabled:
    print("\n⚠️  WARNING: OpenAI is enabled but API key is missing!")
    print("   Analysis generation will fail. Set OPENAI_API_KEY in .env file.")
elif openai_key and openai_enabled:
    print("\n✅ OpenAI is configured and enabled")
else:
    print("\n⚠️  OpenAI is disabled - analysis generation will use fallbacks")

