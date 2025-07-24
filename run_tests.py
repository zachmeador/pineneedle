#!/usr/bin/env python3
"""
Simple script to run Pineneedle integration tests.

This script checks for API keys and runs the integration tests with appropriate configuration.
"""
import os
import subprocess
import sys
from pathlib import Path

def check_api_keys():
    """Check if required API keys are available."""
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    print("🔍 Checking API key availability...")
    
    if openai_key:
        print("✅ OPENAI_API_KEY found")
    else:
        print("❌ OPENAI_API_KEY not found")
    
    if anthropic_key:
        print("✅ ANTHROPIC_API_KEY found")
    else:
        print("❌ ANTHROPIC_API_KEY not found")
    
    if not openai_key and not anthropic_key:
        print("\n⚠️  No API keys found! Please set at least one:")
        print("   export OPENAI_API_KEY='your-key'")
        print("   export ANTHROPIC_API_KEY='your-key'")
        print("\nOr create a .env file in the project root.")
        return False
    
    return True

def load_env_file():
    """Load environment variables from .env file if it exists."""
    env_file = Path(".env")
    if env_file.exists():
        print(f"📁 Loading environment from {env_file}")
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
            return True
        except ImportError:
            print("⚠️  python-dotenv not installed, skipping .env file")
            return False
    return False

def run_tests(test_filter=None, verbose=True):
    """Run the integration tests."""
    cmd = ["python", "-m", "pytest", "tests/test_integration.py"]
    
    if verbose:
        cmd.append("-v")
    
    if test_filter:
        cmd.extend(["-k", test_filter])
    
    print(f"🚀 Running: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def main():
    """Main entry point."""
    print("🌲 Pineneedle Integration Test Runner")
    print("=" * 40)
    
    # Parse command line arguments first for help
    test_filter = None
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--help", "-h"]:
            print("Usage: python run_tests.py [test_filter]")
            print("\nExamples:")
            print("  python run_tests.py                    # Run all tests")
            print("  python run_tests.py openai             # Run OpenAI tests only")
            print("  python run_tests.py anthropic          # Run Anthropic tests only")
            print("  python run_tests.py parsing            # Run parsing tests only")
            print("  python run_tests.py generation         # Run generation tests only")
            print("  python run_tests.py workflow           # Run end-to-end tests only")
            sys.exit(0)
        else:
            test_filter = sys.argv[1]
            print(f"🎯 Running tests matching: {test_filter}")
    
    # Load .env file if available
    load_env_file()
    
    # Check API keys
    if not check_api_keys():
        sys.exit(1)
    
    print("\n" + "=" * 40)
    
    # Run tests
    success = run_tests(test_filter)
    
    print("\n" + "=" * 40)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed or were skipped")
        print("\n💡 Tips:")
        print("   - Make sure your API keys are valid")
        print("   - Check internet connection")
        print("   - Try running individual test classes")
        print("   - See tests/README.md for detailed instructions")
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 