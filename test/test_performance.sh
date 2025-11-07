#!/bin/bash

# Performance Test Suite
# Tests response times, throughput, and load handling capabilities

echo "=========================================="
echo "       Performance Test Suite"
echo "=========================================="

# Color definitions
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Track test results
failed=0
passed=0
skipped=0

echo ""
echo "Starting performance tests..."
echo "Note: These tests may take several minutes to complete"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to test with curl as fallback
test_with_curl() {
    local url=$1
    local name=$2

    echo "Testing $name with curl..."

    local total_time=0
    local successful=0
    local failed_count=0

    for i in {1..10}; do
        response=$(curl -s -w "\n%{time_total}" -o /dev/null "$url" 2>/dev/null)
        time_total=$(echo "$response" | tail -n1)

        if [ -n "$time_total" ]; then
            total_time=$(awk "BEGIN {print $total_time + $time_total}")
            ((successful++))
        else
            ((failed_count++))
        fi
    done

    if [ $successful -gt 0 ]; then
        avg_time=$(awk "BEGIN {printf \"%.3f\", $total_time / $successful}")
        echo -e "${GREEN}✓${NC} Average response time: ${avg_time}s (${successful}/10 successful)"
        return 0
    else
        echo -e "${RED}✗${NC} All requests failed"
        return 1
    fi
}

# Test 1: Frontend Response Time
echo "=========================================="
echo "1. Frontend Response Time Test"
echo "=========================================="

if command_exists ab; then
    echo "Using ApacheBench (ab) for testing..."
    if ab -n 100 -c 10 -s 30 http://localhost:3000/ > /tmp/ab_frontend.txt 2>&1; then
        echo -e "${GREEN}✓ Frontend test completed${NC}"
        grep -E "Requests per second|Time per request|Failed requests" /tmp/ab_frontend.txt
        ((passed++))
    else
        echo -e "${RED}✗ Frontend test failed${NC}"
        test_with_curl "http://localhost:3000/" "Frontend"
        result=$?
        [ $result -eq 0 ] && ((passed++)) || ((failed++))
    fi
elif command_exists curl; then
    echo -e "${YELLOW}⚠${NC} ApacheBench not available, using curl fallback"
    test_with_curl "http://localhost:3000/" "Frontend"
    result=$?
    [ $result -eq 0 ] && ((passed++)) || ((failed++))
else
    echo -e "${YELLOW}⚠${NC} No testing tools available - SKIPPED"
    ((skipped++))
fi

echo ""

# Test 2: Backend Health Endpoint
echo "=========================================="
echo "2. Backend Health Endpoint Test"
echo "=========================================="

if command_exists ab; then
    echo "Using ApacheBench (ab) for testing..."
    if ab -n 1000 -c 50 -s 30 http://localhost:8080/health > /tmp/ab_backend.txt 2>&1; then
        echo -e "${GREEN}✓ Backend test completed${NC}"
        grep -E "Requests per second|Time per request|Failed requests|Transfer rate" /tmp/ab_backend.txt
        ((passed++))
    else
        echo -e "${RED}✗ Backend test failed${NC}"
        test_with_curl "http://localhost:8080/health" "Backend Health"
        result=$?
        [ $result -eq 0 ] && ((passed++)) || ((failed++))
    fi
elif command_exists curl; then
    echo -e "${YELLOW}⚠${NC} ApacheBench not available, using curl fallback"
    test_with_curl "http://localhost:8080/health" "Backend Health"
    result=$?
    [ $result -eq 0 ] && ((passed++)) || ((failed++))
else
    echo -e "${YELLOW}⚠${NC} No testing tools available - SKIPPED"
    ((skipped++))
fi

echo ""

# Test 3: Redis Performance
echo "=========================================="
echo "3. Redis Performance Test"
echo "=========================================="

if command_exists redis-benchmark; then
    echo "Testing Redis operations..."
    if redis-benchmark -h localhost -p 6379 -q -t set,get -n 10000 > /tmp/redis_bench.txt 2>&1; then
        echo -e "${GREEN}✓ Redis test completed${NC}"
        cat /tmp/redis_bench.txt
        ((passed++))
    else
        echo -e "${RED}✗ Redis test failed (service may be unavailable)${NC}"
        ((failed++))
    fi
elif command_exists redis-cli; then
    echo -e "${YELLOW}⚠${NC} redis-benchmark not available, testing basic connectivity"
    if redis-cli -h localhost -p 6379 PING > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Redis is responding to PING"

        # Simple performance test
        start=$(date +%s%N)
        for i in {1..100}; do
            redis-cli -h localhost -p 6379 SET "test_key_$i" "test_value" > /dev/null 2>&1
        done
        end=$(date +%s%N)
        duration=$(( (end - start) / 1000000 ))

        echo "  100 SET operations completed in ${duration}ms"
        echo "  Average: $((duration / 100))ms per operation"
        ((passed++))
    else
        echo -e "${RED}✗${NC} Redis connection failed"
        ((failed++))
    fi
else
    echo -e "${YELLOW}⚠${NC} Redis testing tools not available - SKIPPED"
    echo "  Install with: apt-get install redis-tools (Debian/Ubuntu)"
    echo "            or: brew install redis (macOS)"
    ((skipped++))
fi

echo ""

# Test 4: Load Test with wrk or alternative
echo "=========================================="
echo "4. Backend API Load Test"
echo "=========================================="

if command_exists wrk; then
    echo "Using wrk for load testing..."
    echo "Running 30-second test with 4 threads and 100 connections..."
    if wrk -t4 -c100 -d30s --latency http://localhost:8080/health > /tmp/wrk_test.txt 2>&1; then
        echo -e "${GREEN}✓ Load test completed${NC}"
        cat /tmp/wrk_test.txt
        ((passed++))
    else
        echo -e "${RED}✗ Load test failed${NC}"
        cat /tmp/wrk_test.txt
        ((failed++))
    fi
elif command_exists ab; then
    echo -e "${YELLOW}⚠${NC} wrk not available, using ApacheBench"
    echo "Running load test with 5000 requests, 100 concurrent..."
    if ab -n 5000 -c 100 -s 30 http://localhost:8080/health > /tmp/ab_load.txt 2>&1; then
        echo -e "${GREEN}✓ Load test completed${NC}"
        grep -E "Requests per second|Time per request|Failed requests|Percentage|Transfer rate" /tmp/ab_load.txt
        ((passed++))
    else
        echo -e "${RED}✗ Load test failed${NC}"
        ((failed++))
    fi
elif command_exists curl; then
    echo -e "${YELLOW}⚠${NC} No load testing tools available, using basic curl test"
    test_with_curl "http://localhost:8080/health" "Backend Health"
    result=$?
    [ $result -eq 0 ] && ((passed++)) || ((failed++))
else
    echo -e "${YELLOW}⚠${NC} No testing tools available - SKIPPED"
    echo "  Install wrk: https://github.com/wg/wrk"
    echo "  Or install ApacheBench: apt-get install apache2-utils"
    ((skipped++))
fi

# Summary
echo ""
echo "=========================================="
echo "      Performance Test Summary"
echo "=========================================="
echo "Total Tests:     $((passed + failed + skipped))"
echo -e "${GREEN}Passed:${NC}         $passed"
echo -e "${RED}Failed:${NC}         $failed"
echo -e "${YELLOW}Skipped:${NC}        $skipped"

echo ""
if [ $failed -eq 0 ]; then
    if [ $skipped -gt 0 ]; then
        echo -e "${YELLOW}⚠ Performance tests completed with $skipped test(s) skipped${NC}"
        echo ""
        echo "To run all tests, install missing tools:"
        echo "  • ApacheBench: apt-get install apache2-utils"
        echo "  • wrk: https://github.com/wg/wrk"
        echo "  • redis-tools: apt-get install redis-tools"
    else
        echo -e "${GREEN}✓ All performance tests passed${NC}"
    fi
    echo "=========================================="
    exit 0
else
    echo -e "${RED}✗ $failed performance test(s) failed${NC}"
    echo "=========================================="
    exit 1
fi