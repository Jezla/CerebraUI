# Quick Start Guide - CerebraUI Test Suite

## ✅ All Issues Fixed!

The test suite has been fully optimized and is now working correctly on your system.

## Quick Test

Run all tests including resilience:

```bash
cd test
./run_all_tests.sh
```

Skip resilience test (no service disruption):

```bash
./run_all_tests.sh --skip-resilience
```

## What Was Fixed

### 1. ✅ Bash 3.2 Compatibility
- Scripts now work with macOS default Bash (3.2.57)
- Converted associative arrays to indexed arrays
- No need to upgrade Bash!

### 2. ✅ Network Auto-Detection
- Automatically detects your Docker network name
- Works with any project directory name
- No manual configuration needed

### 3. ✅ macOS AWK Compatibility
- Fixed calculation errors on macOS
- Uses `bc` for floating point math
- Fallback to integer arithmetic if needed

### 4. ✅ Service Name Fixes
- Fixed array key syntax errors
- Proper service-to-container mapping
- All 9 services detected correctly

## Current Test Results

```
✅ Container Health:   9/9 passed
✅ Connectivity:       9/9 passed
✅ Dependencies:       6/6 passed
✅ Network:           9/9 passed
✅ Performance:       4/4 passed
⚠️ Resilience:        Skipped (stops services temporarily)
```

## Individual Tests

Run tests separately:

```bash
# Safe tests (can run anytime)
./test_container_health.sh      # Check all containers are healthy
python3 test_connectivity.py     # Test service connectivity
python3 test_dependencies.py     # Test inter-service dependencies
./test_network.sh                # Test Docker network
./test_performance.sh            # Performance benchmarks

# Disruptive test (run during maintenance windows only)
./test_resilience.sh             # Resilience test (restarts services)
```

## Test Reports

After running tests, check reports:

```bash
# View latest report
cat test_reports/test_report_*.txt | tail -30

# View all reports
ls -lt test_reports/
```

Reports include:
- **Text format** (`*.txt`) - Human-readable summary
- **JSON format** (`*.json`) - Machine-readable for CI/CD

## System Requirements

### ✅ You Have (Already Installed)

- Docker & Docker Compose
- Bash 3.2+ (macOS default)
- Python 3.x
- Services running correctly

### 📦 Optional Tools (For Enhanced Testing)

```bash
# macOS
brew install apache2-utils redis wrk

# Ubuntu/Debian
sudo apt-get install apache2-utils redis-tools
```

### 🐍 Python Dependencies

```bash
# Recommended: Use virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install requests redis
```

## Troubleshooting

### Services Not Running?

```bash
cd /path/to/CerebraUI
docker compose -f docker-compose.microservices.yaml up -d
# Wait 30-60 seconds for startup
```

### Check Service Status

```bash
docker compose -f docker-compose.microservices.yaml ps
```

### View Logs

```bash
# All services
docker compose -f docker-compose.microservices.yaml logs

# Specific service
docker compose -f docker-compose.microservices.yaml logs backend
```

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
- name: Run Tests
  run: |
    cd test
    chmod +x *.sh
    ./run_all_tests.sh

- name: Upload Reports
  uses: actions/upload-artifact@v2
  with:
    name: test-reports
    path: test/test_reports/
```

## Need Help?

1. Check `README.md` for detailed documentation
2. Check service logs: `docker compose -f ../docker-compose.microservices.yaml logs`

Just run `./run_all_tests.sh` and you're good to go!
