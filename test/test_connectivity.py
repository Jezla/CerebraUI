#!/usr/bin/env python3
"""
Service Connectivity Test
Tests network connectivity and basic API responses for all microservices
"""

import requests
import socket
import time
import sys
from typing import Dict, Tuple, List
from datetime import datetime

# ANSI color codes for output
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

# Service configuration with test endpoints
SERVICES = {
    "Frontend": {
        "url": "http://localhost:3000",
        "expected_status": [200, 301, 302, 304],
        "description": "React Frontend UI"
    },
    "Backend": {
        "url": "http://localhost:8080/health",
        "expected_status": [200],
        "description": "Python Backend API"
    },
    "Redis": {
        "type": "tcp",
        "host": "localhost",
        "port": 6379,
        "description": "Redis Cache"
    },
    "Ollama": {
        "url": "http://localhost:11434/api/tags",
        "expected_status": [200],
        "description": "Ollama AI Model Service"
    },
    "Crawl4AI": {
        "url": "http://localhost:11235/health",
        "expected_status": [200],
        "description": "Web Crawling Service"
    },
    "Grafana": {
        "url": "http://localhost:3001",
        "expected_status": [200, 302],
        "description": "Grafana Monitoring"
    },
    "ComfyUI": {
        "url": "http://localhost:8188",
        "expected_status": [200],
        "description": "Image Generation Service"
    },
    "Langflow": {
        "url": "http://localhost:7860",
        "expected_status": [200],
        "description": "AI Workflow Builder"
    },
    "MCPO Server": {
        "url": "http://localhost:8000/health",
        "expected_status": [200, 404],
        "description": "MCP Protocol Server"
    }
}

def test_http_service(name: str, config: Dict) -> Tuple[bool, str, float]:
    """
    Test HTTP/HTTPS service connectivity and response

    Args:
        name: Service name
        config: Service configuration dict

    Returns:
        Tuple of (success, message, response_time)
    """
    start_time = time.time()

    try:
        response = requests.get(
            config["url"],
            timeout=10,
            allow_redirects=False,
            verify=False  # Skip SSL verification for local services
        )

        response_time = time.time() - start_time

        if response.status_code in config["expected_status"]:
            message = f"{Colors.GREEN}✓{Colors.NC} {name:15} | Status: {response.status_code} | Time: {response_time:.2f}s"
            return True, message, response_time
        else:
            message = f"{Colors.RED}✗{Colors.NC} {name:15} | Unexpected status: {response.status_code}"
            return False, message, response_time

    except requests.exceptions.ConnectionError:
        response_time = time.time() - start_time
        message = f"{Colors.RED}✗{Colors.NC} {name:15} | Connection refused (service may be down)"
        return False, message, response_time
    except requests.exceptions.Timeout:
        response_time = time.time() - start_time
        message = f"{Colors.RED}✗{Colors.NC} {name:15} | Request timeout (>{response_time:.1f}s)"
        return False, message, response_time
    except Exception as e:
        response_time = time.time() - start_time
        message = f"{Colors.RED}✗{Colors.NC} {name:15} | Error: {str(e)}"
        return False, message, response_time

def test_tcp_service(name: str, config: Dict) -> Tuple[bool, str, float]:
    """
    Test TCP service connectivity

    Args:
        name: Service name
        config: Service configuration dict

    Returns:
        Tuple of (success, message, response_time)
    """
    start_time = time.time()

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((config["host"], config["port"]))
        sock.close()

        response_time = time.time() - start_time

        if result == 0:
            message = f"{Colors.GREEN}✓{Colors.NC} {name:15} | Port {config['port']} open | Time: {response_time:.2f}s"
            return True, message, response_time
        else:
            message = f"{Colors.RED}✗{Colors.NC} {name:15} | Port {config['port']} closed or unreachable"
            return False, message, response_time
    except socket.timeout:
        response_time = time.time() - start_time
        message = f"{Colors.RED}✗{Colors.NC} {name:15} | Connection timeout"
        return False, message, response_time
    except Exception as e:
        response_time = time.time() - start_time
        message = f"{Colors.RED}✗{Colors.NC} {name:15} | Error: {str(e)}"
        return False, message, response_time

def main():
    """Main test execution function"""
    print("=" * 60)
    print("        Service Connectivity Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test results storage
    results: List[Tuple[str, bool, float, str]] = []
    failed_services: List[str] = []
    passed_services: List[str] = []
    total_response_time = 0.0

    print("Testing service connectivity...")
    print("-" * 60)

    # Run tests on all services
    for name, config in SERVICES.items():
        if config.get("type") == "tcp":
            success, message, response_time = test_tcp_service(name, config)
        else:
            success, message, response_time = test_http_service(name, config)

        print(message)
        results.append((name, success, response_time, config.get("description", "")))
        total_response_time += response_time

        if success:
            passed_services.append(name)
        else:
            failed_services.append(name)

        # Small delay to avoid overwhelming services
        time.sleep(0.3)

    # Calculate statistics
    total_tests = len(SERVICES)
    passed = len(passed_services)
    failed = len(failed_services)
    success_rate = (passed / total_tests * 100) if total_tests > 0 else 0
    avg_response_time = total_response_time / total_tests if total_tests > 0 else 0

    # Display summary
    print()
    print("=" * 60)
    print("           Connectivity Test Summary")
    print("=" * 60)
    print(f"Total Services:      {total_tests}")
    print(f"{Colors.GREEN}Passed:{Colors.NC}             {passed}")
    print(f"{Colors.RED}Failed:{Colors.NC}             {failed}")
    print(f"Success Rate:        {success_rate:.1f}%")
    print(f"Avg Response Time:   {avg_response_time:.2f}s")
    print()

    # Show failed services if any
    if failed_services:
        print(f"{Colors.RED}Failed Services:{Colors.NC}")
        print("-" * 60)
        for service in failed_services:
            config = SERVICES[service]
            desc = config.get("description", "")
            if config.get("type") == "tcp":
                endpoint = f"{config['host']}:{config['port']}"
            else:
                endpoint = config["url"]
            print(f"  • {service}: {desc}")
            print(f"    Endpoint: {endpoint}")
        print()

    # Show passed services summary
    if passed_services:
        print(f"{Colors.GREEN}Passed Services:{Colors.NC}")
        print("-" * 60)
        for service in passed_services:
            print(f"  ✓ {service}")
        print()

    print("=" * 60)

    # Exit with appropriate status code
    if failed > 0:
        print(f"{Colors.RED}✗ Connectivity test failed - {failed} service(s) unreachable{Colors.NC}")
        sys.exit(1)
    else:
        print(f"{Colors.GREEN}✓ All services are reachable{Colors.NC}")
        sys.exit(0)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.NC}")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Unexpected error: {str(e)}{Colors.NC}")
        sys.exit(1)