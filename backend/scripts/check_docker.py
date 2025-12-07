"""
Quick script to check if Docker is running
"""
import subprocess
import sys

def check_docker():
    """Check if Docker is running"""
    try:
        result = subprocess.run(
            ["docker", "ps"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            print("✅ Docker is running!")
            return True
        else:
            print("❌ Docker is not running")
            print("Error:", result.stderr)
            return False
    except FileNotFoundError:
        print("❌ Docker is not installed or not in PATH")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Docker command timed out - Docker may not be running")
        return False
    except Exception as e:
        print(f"❌ Error checking Docker: {e}")
        return False

if __name__ == "__main__":
    if check_docker():
        print("\n✅ You can now run: docker-compose up -d postgres")
        sys.exit(0)
    else:
        print("\n❌ Please start Docker Desktop first")
        print("   Then run: docker-compose up -d postgres")
        sys.exit(1)

