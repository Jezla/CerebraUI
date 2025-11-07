#!/bin/bash

# CerebraUI Microservices Test Suite
# This script runs all test suites and generates a comprehensive test report
#
# Usage:
#   ./run_all_tests.sh                    # Run all tests (including resilience)
#   ./run_all_tests.sh --skip-resilience  # Skip resilience test (no service disruption)

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test configuration
COMPOSE_FILE="../docker-compose.microservices.yaml"
REPORT_DIR="./test_reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
REPORT_FILE="$REPORT_DIR/test_report_${TIMESTAMP}.txt"
JSON_REPORT="$REPORT_DIR/test_report_${TIMESTAMP}.json"
DETAIL_DIR="$REPORT_DIR/details_${TIMESTAMP}"

# Create report directories
mkdir -p "$REPORT_DIR"
mkdir -p "$DETAIL_DIR"

# Initialize report
echo "======================================"
echo "  CerebraUI Microservices Test Suite"
echo "======================================"
echo "Test started at: $(date)"
echo ""

# Optional: Start services if not running
# Uncomment below if you want to automatically start services
# echo "Starting services..."
# docker compose -f $COMPOSE_FILE up -d
# echo "Waiting for services to be ready..."
# sleep 30

# Check if --skip-resilience flag is provided
SKIP_RESILIENCE=false
if [ "$1" == "--skip-resilience" ]; then
    SKIP_RESILIENCE=true
    echo -e "${YELLOW}⚠ Skipping resilience test (no service disruption)${NC}"
    echo ""
fi

# Test tracking arrays
if [ "$SKIP_RESILIENCE" = true ]; then
    declare -a test_names=("Container Health" "Connectivity" "Dependencies" "Performance" "Network")
    declare -a test_scripts=("test_container_health.sh" "test_connectivity.py" "test_dependencies.py" "test_performance.sh" "test_network.sh")
else
    declare -a test_names=("Container Health" "Connectivity" "Dependencies" "Performance" "Network" "Resilience")
    declare -a test_scripts=("test_container_health.sh" "test_connectivity.py" "test_dependencies.py" "test_performance.sh" "test_network.sh" "test_resilience.sh")
fi
declare -a test_results=()
declare -a test_durations=()
declare -a test_outputs=()

# Function to run a test and capture output
run_test() {
    local name=$1
    local script=$2
    local index=$3

    echo -e "\n${BLUE}[$(($index+1))/${#test_names[@]}] Running $name Tests...${NC}"
    echo "=========================================="

    local start_time=$(date +%s)
    local result=0
    local output_file="$DETAIL_DIR/${index}_${script}.log"

    # Run the test script and capture output
    if [[ $script == *.py ]]; then
        python3 "$script" 2>&1 | tee "$output_file"
        result=${PIPESTATUS[0]}
    else
        bash "$script" 2>&1 | tee "$output_file"
        result=${PIPESTATUS[0]}
    fi

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    test_results[$index]=$result
    test_durations[$index]=$duration
    test_outputs[$index]="$output_file"

    echo ""
    if [ $result -eq 0 ]; then
        echo -e "${GREEN}✓ $name tests PASSED${NC} (Duration: ${duration}s)"
    else
        echo -e "${RED}✗ $name tests FAILED${NC} (Duration: ${duration}s)"
    fi
}

# Run all tests
total_start=$(date +%s)
for i in "${!test_names[@]}"; do
    run_test "${test_names[$i]}" "${test_scripts[$i]}" "$i"
done
total_end=$(date +%s)
total_duration=$((total_end - total_start))

# Calculate statistics
total_tests=${#test_names[@]}
failed_count=0
passed_count=0

for result in "${test_results[@]}"; do
    if [ $result -eq 0 ]; then
        ((passed_count++))
    else
        ((failed_count++))
    fi
done

# Generate summary
echo ""
echo "======================================"
echo "         TEST SUMMARY REPORT"
echo "======================================"
echo "Test completed at: $(date)"
echo "Total duration: ${total_duration}s"
echo ""
echo "Test Suites:    $total_tests"
echo -e "Passed:         ${GREEN}$passed_count${NC}"
echo -e "Failed:         ${RED}$failed_count${NC}"
# Calculate success rate using bc for better compatibility
if command -v bc > /dev/null 2>&1; then
    success_rate=$(echo "scale=2; ($passed_count * 100) / $total_tests" | bc)
else
    # Fallback to integer arithmetic if bc not available
    success_rate=$((passed_count * 100 / total_tests))
fi
echo "Success Rate:   ${success_rate}%"
echo ""

# Detailed results with test output summaries
echo "Detailed Results:"
echo "--------------------------------------"
for i in "${!test_names[@]}"; do
    if [ ${test_results[$i]} -eq 0 ]; then
        echo -e "  ${GREEN}✓${NC} ${test_names[$i]}: PASSED (${test_durations[$i]}s)"
    else
        echo -e "  ${RED}✗${NC} ${test_names[$i]}: FAILED (${test_durations[$i]}s)"
    fi

    # Show summary from test output
    if [ -f "${test_outputs[$i]}" ]; then
        echo -e "    ${CYAN}Summary:${NC}"

        # Extract summary information from each test
        case "${test_scripts[$i]}" in
            "test_container_health.sh")
                grep -E "(Total Containers:|Healthy:|Failed:)" "${test_outputs[$i]}" | sed 's/^/      /'
                ;;
            "test_connectivity.py")
                grep -E "(Total Services:|Passed:|Failed:|Success Rate:)" "${test_outputs[$i]}" | sed 's/^/      /'
                ;;
            "test_dependencies.py")
                grep -E "(Total Tests:|Passed:|Failed:)" "${test_outputs[$i]}" | sed 's/^/      /'
                ;;
            "test_performance.sh")
                grep -E "(Total Tests:|Passed:|Failed:|Skipped:)" "${test_outputs[$i]}" | sed 's/^/      /'
                ;;
            "test_network.sh")
                grep -E "(Total Tests:|Passed:|Failed:)" "${test_outputs[$i]}" | sed 's/^/      /'
                ;;
            "test_resilience.sh")
                grep -E "(Total Tests:|Passed:|Failed:)" "${test_outputs[$i]}" | sed 's/^/      /'
                ;;
        esac
        echo ""
    fi
done
echo "======================================"

# Generate text report
{
    echo "======================================"
    echo "  CerebraUI Microservices Test Report"
    echo "======================================"
    echo "Generated: $(date)"
    echo "Total Duration: ${total_duration}s"
    echo ""
    echo "Summary:"
    echo "  Total Test Suites: $total_tests"
    echo "  Passed: $passed_count"
    echo "  Failed: $failed_count"
    echo "  Success Rate: ${success_rate}%"
    echo ""
    echo "Detailed Results:"
    for i in "${!test_names[@]}"; do
        if [ ${test_results[$i]} -eq 0 ]; then
            echo "  ✓ ${test_names[$i]}: PASSED (${test_durations[$i]}s)"
        else
            echo "  ✗ ${test_names[$i]}: FAILED (${test_durations[$i]}s)"
        fi
    done
    echo ""
    echo "======================================"
} > "$REPORT_FILE"

# Generate JSON report
{
    echo "{"
    echo "  \"timestamp\": \"$(date -Iseconds)\","
    echo "  \"total_duration\": $total_duration,"
    echo "  \"summary\": {"
    echo "    \"total\": $total_tests,"
    echo "    \"passed\": $passed_count,"
    echo "    \"failed\": $failed_count,"
    echo "    \"success_rate\": $success_rate"
    echo "  },"
    echo "  \"tests\": ["
    for i in "${!test_names[@]}"; do
        echo "    {"
        echo "      \"name\": \"${test_names[$i]}\","
        echo "      \"status\": \"$([ ${test_results[$i]} -eq 0 ] && echo 'passed' || echo 'failed')\","
        echo "      \"duration\": ${test_durations[$i]}"
        echo -n "    }"
        [ $i -lt $((${#test_names[@]}-1)) ] && echo "," || echo ""
    done
    echo "  ]"
    echo "}"
} > "$JSON_REPORT"

echo ""
echo "Reports generated:"
echo "  - Text report: $REPORT_FILE"
echo "  - JSON report: $JSON_REPORT"
echo "  - Detail logs: $DETAIL_DIR/"

# Show usage hint if skipping resilience test
if [ "$SKIP_RESILIENCE" = true ]; then
    echo ""
    echo -e "${YELLOW}ℹ${NC} Resilience test was skipped"
    echo "  To run with resilience test (will restart services):"
    echo "  ./run_all_tests.sh"
fi

# Show failed test details if any
if [ $failed_count -gt 0 ]; then
    echo ""
    echo -e "${RED}Failed Test Details:${NC}"
    echo "--------------------------------------"
    for i in "${!test_names[@]}"; do
        if [ ${test_results[$i]} -ne 0 ]; then
            echo -e "${RED}✗ ${test_names[$i]}${NC}"
            echo "  Log file: ${test_outputs[$i]}"
            echo "  Last 10 lines:"
            tail -10 "${test_outputs[$i]}" | sed 's/^/    /'
            echo ""
        fi
    done
fi

# Final exit status
if [ $failed_count -eq 0 ]; then
    echo -e "\n${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}✗ $failed_count test suite(s) failed!${NC}"
    echo -e "Check detailed logs in: ${DETAIL_DIR}/"
    exit 1
fi