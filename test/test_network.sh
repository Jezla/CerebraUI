#!/bin/bash

# Network Connectivity Test
# Tests Docker network configuration and inter-container communication

echo "=========================================="
echo "    Network Connectivity Test"
echo "=========================================="

# Color definitions
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
COMPOSE_FILE="../docker-compose.microservices.yaml"

# Counter for failed tests
failed=0
passed=0

echo ""
echo "1. Checking Docker network existence..."
echo "------------------------------------------"

# Auto-detect network name by finding the network containing cerebraui containers
NETWORK_NAME=$(docker inspect cerebraui-backend 2>/dev/null | grep -o '"NetworkMode": "[^"]*"' | cut -d'"' -f4)

if [ -z "$NETWORK_NAME" ]; then
    # Fallback: search for networks containing cerebraui
    NETWORK_NAME=$(docker network ls --format '{{.Name}}' | grep -i cerebraui | head -n1)
fi

if [ -z "$NETWORK_NAME" ]; then
    # Final fallback
    NETWORK_NAME="cerebraui_cerebraui-network"
fi

echo "Detected network: $NETWORK_NAME"

# Check if network exists
if docker network inspect "$NETWORK_NAME" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Network '$NETWORK_NAME' exists"
    ((passed++))

    # Get container count in network
    container_count=$(docker network inspect "$NETWORK_NAME" --format '{{len .Containers}}')
    echo "  Containers in network: $container_count"

    # List all containers in the network
    echo ""
    echo "  Containers:"
    docker network inspect "$NETWORK_NAME" --format '{{range .Containers}}  - {{.Name}} ({{.IPv4Address}})
{{end}}'
else
    echo -e "${RED}✗${NC} Network '$NETWORK_NAME' does not exist"
    ((failed++))
    echo ""
    echo "Please ensure services are running with:"
    echo "  docker compose -f $COMPOSE_FILE up -d"
    exit 1
fi

echo ""
echo "2. Testing inter-container communication..."
echo "------------------------------------------"

# Function to test container connectivity
test_connection() {
    local source_container=$1
    local target_host=$2
    local target_port=$3
    local description=$4

    echo -n "Testing $description... "

    # Check if source container is running
    if ! docker ps --format '{{.Names}}' | grep -q "^${source_container}$"; then
        echo -e "${YELLOW}⚠${NC} Source container '$source_container' not running - SKIPPED"
        return 2
    fi

    # Try netcat first, fall back to wget/curl if nc not available
    if docker exec "$source_container" sh -c "command -v nc > /dev/null 2>&1" 2>/dev/null; then
        # Use netcat
        if docker exec "$source_container" sh -c "nc -zv -w 3 $target_host $target_port" 2>&1 | grep -qE "(open|succeeded)"; then
            echo -e "${GREEN}✓ PASSED${NC}"
            return 0
        else
            echo -e "${RED}✗ FAILED${NC}"
            return 1
        fi
    else
        # Fallback: try to connect using timeout and /dev/tcp
        if docker exec "$source_container" sh -c "timeout 3 bash -c 'cat < /dev/null > /dev/tcp/$target_host/$target_port' 2>/dev/null"; then
            echo -e "${GREEN}✓ PASSED${NC} (fallback method)"
            return 0
        else
            echo -e "${YELLOW}⚠${NC} Cannot verify (nc not available in container)"
            return 2
        fi
    fi
}

# Test Backend connectivity to other services
echo ""
echo "Backend Service Connectivity:"
test_connection "cerebraui-backend" "cerebraui-redis" "6379" "Backend -> Redis"
result=$?
if [ $result -eq 0 ]; then
    ((passed++))
elif [ $result -eq 1 ]; then
    ((failed++))
fi

test_connection "cerebraui-backend" "ollama" "11434" "Backend -> Ollama"
result=$?
if [ $result -eq 0 ]; then
    ((passed++))
elif [ $result -eq 1 ]; then
    ((failed++))
fi

test_connection "cerebraui-backend" "crawl4ai" "11235" "Backend -> Crawl4AI"
result=$?
if [ $result -eq 0 ]; then
    ((passed++))
elif [ $result -eq 1 ]; then
    ((failed++))
fi

test_connection "cerebraui-backend" "comfyui" "8188" "Backend -> ComfyUI"
result=$?
if [ $result -eq 0 ]; then
    ((passed++))
elif [ $result -eq 1 ]; then
    ((failed++))
fi

test_connection "cerebraui-backend" "langflow" "7860" "Backend -> Langflow"
result=$?
if [ $result -eq 0 ]; then
    ((passed++))
elif [ $result -eq 1 ]; then
    ((failed++))
fi

test_connection "cerebraui-backend" "lgtm" "3000" "Backend -> Grafana"
result=$?
if [ $result -eq 0 ]; then
    ((passed++))
elif [ $result -eq 1 ]; then
    ((failed++))
fi

echo ""
echo "Frontend Service Connectivity:"
test_connection "cerebraui-frontend" "cerebraui-backend" "8080" "Frontend -> Backend"
result=$?
if [ $result -eq 0 ]; then
    ((passed++))
elif [ $result -eq 1 ]; then
    ((failed++))
fi

echo ""
echo "3. Checking network isolation..."
echo "------------------------------------------"

# Verify containers are not on default bridge
default_bridge_containers=$(docker network inspect bridge --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null | grep -c "cerebraui\|ollama\|langflow\|comfyui\|crawl4ai")

if [ "$default_bridge_containers" -eq 0 ]; then
    echo -e "${GREEN}✓${NC} No CerebraUI containers on default bridge network (good)"
    ((passed++))
else
    echo -e "${YELLOW}⚠${NC} Found $default_bridge_containers CerebraUI container(s) on default bridge"
    echo "  This may indicate network misconfiguration"
fi

# Summary
echo ""
echo "=========================================="
echo "        Network Test Summary"
echo "=========================================="
echo "Total Tests:     $((passed + failed))"
echo -e "${GREEN}Passed:${NC}         $passed"
echo -e "${RED}Failed:${NC}         $failed"

if [ $failed -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ All network tests passed${NC}"
    echo "=========================================="
    exit 0
else
    echo ""
    echo -e "${RED}✗ Some network tests failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Ensure all services are running:"
    echo "     docker compose -f $COMPOSE_FILE ps"
    echo "  2. Check container logs for errors:"
    echo "     docker compose -f $COMPOSE_FILE logs"
    echo "  3. Restart services if needed:"
    echo "     docker compose -f $COMPOSE_FILE restart"
    echo "=========================================="
    exit 1
fi