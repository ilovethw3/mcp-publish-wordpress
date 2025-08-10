"""Test runner script for MCP WordPress server."""

import subprocess
import sys
from pathlib import Path


def run_tests():
    """Run the complete test suite."""
    print("Running MCP WordPress Server Test Suite")
    print("=" * 50)
    
    # Ensure we're in the project directory
    project_root = Path(__file__).parent
    
    # Run pytest with coverage
    cmd = [
        sys.executable, "-m", "pytest",
        "mcp_wordpress/tests/",
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ]
    
    try:
        result = subprocess.run(cmd, cwd=project_root, check=True)
        print("\n✅ All tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return e.returncode
    except FileNotFoundError:
        print("❌ pytest not found. Please install test dependencies:")
        print("pip install pytest pytest-asyncio pytest-mock")
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())