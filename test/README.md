# CerebraUI Microservices Test Suite

Comprehensive testing suite for CerebraUI microservices architecture. This suite validates container health, service connectivity, dependencies, network configuration, performance, and resilience.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Test Suites](#test-suites)
- [Running Tests](#running-tests)
- [Test Reports](#test-reports)
- [Troubleshooting](#troubleshooting)

## Overview

This test suite provides comprehensive validation for the CerebraUI microservices deployment:

- **Container Health Tests** - Validates all Docker containers are running and healthy
- **Connectivity Tests** - Checks network connectivity and API responses
- **Dependency Tests** - Verifies inter-service dependencies
- **Network Tests** - Tests Docker network configuration and inter-container communication
- **Performance Tests** - Measures response times and throughput
- **Resilience Tests** - Tests service recovery and restart capabilities

## Prerequisites

### Required

- Docker and Docker Compose installed
- CerebraUI services running via `docker-compose.microservices.yaml`
- Bash shell (for shell scripts)
  - **Note:** Scripts are compatible with Bash 3.2+ (including macOS default bash)
  - Uses indexed arrays for maximum compatibility
- Python 3.x (for Python tests)

### Python Dependencies

```bash
# Navigate to test directory
cd test

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install requests
pip install redis  # Optional, for Redis dependency tests
```

### Optional Tools (for complete performance testing)

```bash
# Ubuntu/Debian
sudo apt-get install apache2-utils redis-tools

# macOS
brew install apache2-utils redis wrk

# wrk (advanced load testing)
# Visit: https://github.com/wg/wrk
```

## Quick Start

### 1. Start Services

```bash
cd /path/to/CerebraUI
docker compose -f docker-compose.microservices.yaml up -d
```

Wait 30-60 seconds for all services to initialize.

### 2. Run All Tests

```bash
cd test
chmod +x *.sh  # Make scripts executable
./run_all_tests.sh
```

### 3. View Test Reports

Reports are automatically generated in `test_reports/`:
- `test_report_YYYYMMDD_HHMMSS.txt` - Human-readable report
- `test_report_YYYYMMDD_HHMMSS.json` - Machine-readable JSON report

## Test Suites

### 1. Container Health Check (`test_container_health.sh`)

Validates that all containers are running and healthy.

**Tested Services:**
- Frontend (cerebraui-frontend)
- Backend (cerebraui-backend)
- Redis (cerebraui-redis)
- Ollama (ollama)
- Crawl4AI (crawl4ai)
- Grafana (lgtm)
- ComfyUI (comfyui)
- Langflow (langflow)
- MCPO Server (mcpo-server)

**Run Individually:**
```bash
./test_container_health.sh
```

### 2. Connectivity Test (`test_connectivity.py`)

Tests HTTP/TCP connectivity for all services.

**Checks:**
- HTTP endpoints responding
- Correct status codes
- Response times
- Port availability

**Run Individually:**
```bash
python3 test_connectivity.py
```

### 3. Dependency Test (`test_dependencies.py`)

Verifies inter-service dependencies.

**Tests:**
- Backend → Redis
- Backend → Ollama
- Backend → Crawl4AI
- Backend → ComfyUI
- Backend → Langflow
- Backend → Grafana

**Run Individually:**
```bash
python3 test_dependencies.py
```

### 4. Network Test (`test_network.sh`)

Validates Docker network configuration and inter-container communication.

**Checks:**
- Network existence
- Container network membership
- Inter-container connectivity
- Network isolation

**Run Individually:**
```bash
./test_network.sh
```

### 5. Performance Test (`test_performance.sh`)

Measures service performance and load handling.

**Tests:**
- Frontend response time
- Backend health endpoint performance
- Redis operations performance
- Load testing (with concurrent requests)

**Run Individually:**
```bash
./test_performance.sh
```

**Note:** Some tests require optional tools (ab, wrk, redis-benchmark). The script will use fallback methods if these are unavailable.

### 6. Resilience Test (`test_resilience.sh`)

Tests service recovery and restart capabilities.

**Tests:**
- Service stop/start cycles
- Health check recovery
- System stability after restarts
- Dependent service functionality

**Run Individually:**
```bash
./test_resilience.sh
```

**Warning:** This test temporarily stops and restarts services. Run during maintenance windows only.

## Running Tests

### Run All Tests

Run all tests including resilience:
```bash
./run_all_tests.sh
```

Skip resilience test (no service disruption):
```bash
./run_all_tests.sh --skip-resilience
```

**Note:** The script now displays detailed summaries for each test suite in the final report.

### Run Specific Test Suite

```bash
# Bash scripts
./test_container_health.sh
./test_network.sh
./test_performance.sh
./test_resilience.sh

# Python scripts
python3 test_connectivity.py
python3 test_dependencies.py
```

### Run Tests in Sequence

```bash
./test_container_health.sh && \
python3 test_connectivity.py && \
python3 test_dependencies.py && \
./test_network.sh && \
./test_performance.sh && \
./test_resilience.sh
```

## Test Reports

### Report Location

All reports are saved in the `test_reports/` directory:

```
test_reports/
├── test_report_20250105_143022.txt       # Human-readable summary
├── test_report_20250105_143022.json      # Machine-readable JSON
├── details_20250105_143022/              # Detailed logs for each test
│   ├── 0_test_container_health.sh.log
│   ├── 1_test_connectivity.py.log
│   ├── 2_test_dependencies.py.log
│   ├── 3_test_performance.sh.log
│   ├── 4_test_network.sh.log
│   └── 5_test_resilience.sh.log
└── ...
```

### Report Format

#### Text Report Example

```
======================================
         TEST SUMMARY REPORT
======================================
Test completed at: Fri  7 Nov 2025 16:26:45 AEDT
Total duration: 38s

Test Suites:    5
Passed:         5
Failed:         0
Success Rate:   100.00%

Detailed Results:
--------------------------------------
  ✓ Container Health: PASSED (1s)
    Summary:
      Total Containers:    9
      Healthy:             9
      Failed:              0

  ✓ Connectivity: PASSED (3s)
    Summary:
      Total Services:      9
      Passed:              9
      Failed:              0
      Success Rate:        100.0%

  ✓ Dependencies: PASSED (0s)
    Summary:
      Total Tests:     6
      Passed:          6
      Failed:          0

  ✓ Performance: PASSED (33s)
    Summary:
      Total Tests:     4
      Passed:          4
      Failed:          0
      Skipped:         0

  ✓ Network: PASSED (1s)
    Summary:
      Total Tests:     9
      Passed:          9
      Failed:          0

======================================
```

#### JSON Report Example

```json
{
  "timestamp": "2025-01-05T14:30:22-05:00",
  "total_duration": 125,
  "summary": {
    "total": 6,
    "passed": 6,
    "failed": 0,
    "success_rate": 100.00
  },
  "tests": [
    {
      "name": "Container Health",
      "status": "passed",
      "duration": 8
    },
    ...
  ]
}
```

## Compatibility Notes

### Bash Version Compatibility

These test scripts are designed to work with **Bash 3.2+**, which is the default on macOS and older Linux systems. The scripts use indexed arrays instead of associative arrays for maximum compatibility.

**Check your Bash version:**
```bash
bash --version
```

### macOS Specific Notes

- macOS ships with Bash 3.2 by default (for licensing reasons)
- All scripts are tested and working on macOS with Bash 3.2
- If you prefer to use Bash 5+, you can install it via Homebrew:
  ```bash
  brew install bash
  ```

### Network Name Auto-Detection

The network test script automatically detects your Docker network name. Docker Compose creates network names by prefixing your project directory name, so:
- Project in `CerebraUI/` → Network: `cerebraui_cerebraui-network`
- Project in `myproject/` → Network: `myproject_cerebraui-network`

The script will automatically detect the correct network name.

## Troubleshooting

### Common Issues

#### 1. Services Not Running

**Error:** Connection refused or containers not found

**Solution:**
```bash
cd /path/to/CerebraUI
docker compose -f docker-compose.microservices.yaml up -d
# Wait 30-60 seconds
docker compose -f docker-compose.microservices.yaml ps
```

#### 2. Health Checks Failing

**Error:** Containers starting but health checks timeout

**Solution:**
```bash
# Check container logs
docker compose -f docker-compose.microservices.yaml logs [service-name]

# Restart specific service
docker compose -f docker-compose.microservices.yaml restart [service-name]

# Wait longer for services to initialize (some services need 1-2 minutes)
```

#### 3. Port Conflicts

**Error:** Port already in use

**Solution:**
```bash
# Check which process is using the port
lsof -i :3000  # Replace with your port

# Stop conflicting service or change ports in docker-compose.microservices.yaml
```

#### 4. Python Dependencies Missing

**Error:** `ModuleNotFoundError: No module named 'requests'`

**Solution:**
```bash
pip install requests redis
```

#### 5. Performance Tests Skipped

**Warning:** Testing tools not available

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install apache2-utils redis-tools

# macOS
brew install apache2-utils redis wrk
```

#### 6. Permission Denied on Scripts

**Error:** `bash: ./run_all_tests.sh: Permission denied`

**Solution:**
```bash
chmod +x *.sh
```

### Viewing Service Logs

```bash
# All services
docker compose -f ../docker-compose.microservices.yaml logs

# Specific service
docker compose -f ../docker-compose.microservices.yaml logs backend

# Follow logs
docker compose -f ../docker-compose.microservices.yaml logs -f backend
```

### Restarting Services

```bash
# Restart all services
docker compose -f ../docker-compose.microservices.yaml restart

# Restart specific service
docker compose -f ../docker-compose.microservices.yaml restart backend

# Full restart (stop + start)
docker compose -f ../docker-compose.microservices.yaml down
docker compose -f ../docker-compose.microservices.yaml up -d
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Microservices Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Start services
        run: docker compose -f docker-compose.microservices.yaml up -d

      - name: Wait for services
        run: sleep 60

      - name: Install test dependencies
        run: |
          pip install requests redis
          sudo apt-get install -y apache2-utils redis-tools

      - name: Run tests
        run: |
          cd test
          chmod +x *.sh
          ./run_all_tests.sh

      - name: Upload test reports
        uses: actions/upload-artifact@v2
        if: always()
        with:
          name: test-reports
          path: test/test_reports/
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [ApacheBench Documentation](https://httpd.apache.org/docs/2.4/programs/ab.html)
- [wrk Load Testing Tool](https://github.com/wg/wrk)

## Contributing

When adding new tests:

1. Follow the existing naming convention: `test_*.sh` or `test_*.py`
2. Include comprehensive error handling
3. Provide clear output with color coding
4. Update `run_all_tests.sh` to include your new test
5. Update this README with test documentation

## License

This test suite is part of the CerebraUI project.
