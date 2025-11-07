#!/usr/bin/env python3
"""
Service Dependency Test
Tests inter-service dependencies and connectivity between microservices
Ensures Backend can properly connect to Redis, Ollama, Crawl4AI, and other services
"""

import requests
import sys
from typing import Tuple, List, Dict
from datetime import datetime

# ANSI color codes
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

# Try to import redis, but make it optional
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print(f"{Colors.YELLOW}Warning: redis module not installed. Redis tests will be skipped.{Colors.NC}")
    print(f"Install with: pip install redis\n")

def test_backend_to_redis() -> Tuple[bool, str]:
    """
    Test Backend to Redis connection
    Verifies Redis is accessible and responsive
    """
    print("Testing Backend -> Redis connection...")

    if not REDIS_AVAILABLE:
        return False, f"{Colors.YELLOW}⚠{Colors.NC} Redis module not installed - SKIPPED"

    try:
        r = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5
        )

        # Test basic operations
        r.ping()

        # Test set/get operations
        test_key = "_test_dependency_check"
        test_value = "test_value"
        r.set(test_key, test_value, ex=10)  # Expires in 10 seconds
        retrieved = r.get(test_key)
        r.delete(test_key)

        if retrieved == test_value:
            return True, f"{Colors.GREEN}✓{Colors.NC} Backend can connect to Redis (read/write OK)"
        else:
            return False, f"{Colors.RED}✗{Colors.NC} Redis connection issue: data mismatch"

    except redis.ConnectionError:
        return False, f"{Colors.RED}✗{Colors.NC} Cannot connect to Redis (connection refused)"
    except redis.TimeoutError:
        return False, f"{Colors.RED}✗{Colors.NC} Redis connection timeout"
    except Exception as e:
        return False, f"{Colors.RED}✗{Colors.NC} Backend -> Redis failed: {str(e)}"

def test_backend_to_ollama() -> Tuple[bool, str]:
    """
    Test Backend to Ollama connection
    Verifies Ollama API is accessible
    """
    print("Testing Backend -> Ollama connection...")

    try:
        # Test Ollama root endpoint
        response = requests.get("http://localhost:11434", timeout=10)

        if response.status_code == 200:
            # Try to get list of models
            try:
                tags_response = requests.get("http://localhost:11434/api/tags", timeout=10)
                if tags_response.status_code == 200:
                    models = tags_response.json().get('models', [])
                    model_count = len(models)
                    return True, f"{Colors.GREEN}✓{Colors.NC} Backend can connect to Ollama ({model_count} models available)"
                else:
                    return True, f"{Colors.GREEN}✓{Colors.NC} Backend can connect to Ollama (models endpoint unavailable)"
            except:
                return True, f"{Colors.GREEN}✓{Colors.NC} Backend can connect to Ollama"
        else:
            return False, f"{Colors.RED}✗{Colors.NC} Ollama returned status {response.status_code}"

    except requests.exceptions.ConnectionError:
        return False, f"{Colors.RED}✗{Colors.NC} Cannot connect to Ollama (connection refused)"
    except requests.exceptions.Timeout:
        return False, f"{Colors.RED}✗{Colors.NC} Ollama connection timeout"
    except Exception as e:
        return False, f"{Colors.RED}✗{Colors.NC} Backend -> Ollama failed: {str(e)}"

def test_backend_to_crawl4ai() -> Tuple[bool, str]:
    """
    Test Backend to Crawl4AI connection
    Verifies Crawl4AI service is accessible
    """
    print("Testing Backend -> Crawl4AI connection...")

    try:
        response = requests.get("http://localhost:11235/health", timeout=10)

        if response.status_code == 200:
            try:
                data = response.json()
                status = data.get('status', 'unknown')
                return True, f"{Colors.GREEN}✓{Colors.NC} Backend can access Crawl4AI (status: {status})"
            except:
                return True, f"{Colors.GREEN}✓{Colors.NC} Backend can access Crawl4AI"
        else:
            return False, f"{Colors.RED}✗{Colors.NC} Crawl4AI returned status {response.status_code}"

    except requests.exceptions.ConnectionError:
        return False, f"{Colors.RED}✗{Colors.NC} Cannot connect to Crawl4AI (connection refused)"
    except requests.exceptions.Timeout:
        return False, f"{Colors.RED}✗{Colors.NC} Crawl4AI connection timeout"
    except Exception as e:
        return False, f"{Colors.RED}✗{Colors.NC} Backend -> Crawl4AI failed: {str(e)}"

def test_backend_to_comfyui() -> Tuple[bool, str]:
    """
    Test Backend to ComfyUI connection
    Verifies ComfyUI image generation service is accessible
    """
    print("Testing Backend -> ComfyUI connection...")

    try:
        response = requests.get("http://localhost:8188", timeout=10)

        if response.status_code == 200:
            # Try to get system stats if available
            try:
                system_response = requests.get("http://localhost:8188/system_stats", timeout=5)
                if system_response.status_code == 200:
                    return True, f"{Colors.GREEN}✓{Colors.NC} Backend can access ComfyUI (system responsive)"
                else:
                    return True, f"{Colors.GREEN}✓{Colors.NC} Backend can access ComfyUI"
            except:
                return True, f"{Colors.GREEN}✓{Colors.NC} Backend can access ComfyUI"
        else:
            return False, f"{Colors.RED}✗{Colors.NC} ComfyUI returned status {response.status_code}"

    except requests.exceptions.ConnectionError:
        return False, f"{Colors.RED}✗{Colors.NC} Cannot connect to ComfyUI (connection refused)"
    except requests.exceptions.Timeout:
        return False, f"{Colors.RED}✗{Colors.NC} ComfyUI connection timeout"
    except Exception as e:
        return False, f"{Colors.RED}✗{Colors.NC} Backend -> ComfyUI failed: {str(e)}"

def test_backend_to_langflow() -> Tuple[bool, str]:
    """
    Test Backend to Langflow connection
    Verifies Langflow AI workflow service is accessible
    """
    print("Testing Backend -> Langflow connection...")

    try:
        response = requests.get("http://localhost:7860", timeout=10)

        if response.status_code == 200:
            return True, f"{Colors.GREEN}✓{Colors.NC} Backend can access Langflow"
        else:
            return False, f"{Colors.RED}✗{Colors.NC} Langflow returned status {response.status_code}"

    except requests.exceptions.ConnectionError:
        return False, f"{Colors.RED}✗{Colors.NC} Cannot connect to Langflow (connection refused)"
    except requests.exceptions.Timeout:
        return False, f"{Colors.RED}✗{Colors.NC} Langflow connection timeout"
    except Exception as e:
        return False, f"{Colors.RED}✗{Colors.NC} Backend -> Langflow failed: {str(e)}"

def test_backend_to_grafana() -> Tuple[bool, str]:
    """
    Test Backend to Grafana connection
    Verifies monitoring service is accessible
    """
    print("Testing Backend -> Grafana connection...")

    try:
        response = requests.get("http://localhost:3001", timeout=10, allow_redirects=False)

        if response.status_code in [200, 302]:
            return True, f"{Colors.GREEN}✓{Colors.NC} Backend can access Grafana"
        else:
            return False, f"{Colors.RED}✗{Colors.NC} Grafana returned status {response.status_code}"

    except requests.exceptions.ConnectionError:
        return False, f"{Colors.RED}✗{Colors.NC} Cannot connect to Grafana (connection refused)"
    except requests.exceptions.Timeout:
        return False, f"{Colors.RED}✗{Colors.NC} Grafana connection timeout"
    except Exception as e:
        return False, f"{Colors.RED}✗{Colors.NC} Backend -> Grafana failed: {str(e)}"

def main():
    """Main test execution function"""
    print("=" * 60)
    print("       Service Dependency Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Testing inter-service dependencies...")
    print("-" * 60)
    print()

    # Define test suite
    tests = [
        ("Backend -> Redis", test_backend_to_redis),
        ("Backend -> Ollama", test_backend_to_ollama),
        ("Backend -> Crawl4AI", test_backend_to_crawl4ai),
        ("Backend -> ComfyUI", test_backend_to_comfyui),
        ("Backend -> Langflow", test_backend_to_langflow),
        ("Backend -> Grafana", test_backend_to_grafana),
    ]

    results: List[Tuple[str, bool, str]] = []
    failed = 0
    passed = 0
    skipped = 0

    # Run all tests
    for test_name, test_func in tests:
        try:
            success, message = test_func()
            print(message)
            results.append((test_name, success, message))

            if "SKIPPED" in message:
                skipped += 1
            elif success:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            message = f"{Colors.RED}✗{Colors.NC} {test_name} failed with exception: {str(e)}"
            print(message)
            results.append((test_name, False, message))
            failed += 1

        print()

    # Display summary
    total = len(tests)
    print("=" * 60)
    print("        Dependency Test Summary")
    print("=" * 60)
    print(f"Total Tests:     {total}")
    print(f"{Colors.GREEN}Passed:{Colors.NC}         {passed}")
    print(f"{Colors.RED}Failed:{Colors.NC}         {failed}")
    if skipped > 0:
        print(f"{Colors.YELLOW}Skipped:{Colors.NC}        {skipped}")

    success_rate = (passed / (total - skipped) * 100) if (total - skipped) > 0 else 0
    print(f"Success Rate:    {success_rate:.1f}%")
    print()

    # Show failed tests details
    if failed > 0:
        print(f"{Colors.RED}Failed Dependencies:{Colors.NC}")
        print("-" * 60)
        for test_name, success, message in results:
            if not success and "SKIPPED" not in message:
                print(f"  • {test_name}")
        print()

    print("=" * 60)

    # Exit with appropriate status code
    if failed > 0:
        print(f"{Colors.RED}✗ Dependency test failed - {failed} connection(s) failed{Colors.NC}")
        return 1
    elif skipped == total:
        print(f"{Colors.YELLOW}⚠ All tests were skipped{Colors.NC}")
        return 1
    else:
        print(f"{Colors.GREEN}✓ All service dependencies are working correctly{Colors.NC}")
        return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.NC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.NC}")
        sys.exit(1)