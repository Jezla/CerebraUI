#!/bin/bash

# Container Health Check Test
# Tests if all containers are running and healthy

echo "=========================================="
echo "    Container Health Check Test"
echo "=========================================="

# Color definitions
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function for container health
test_container_health() {
    local service=$1
    local container=$2

    echo -n "Testing $service ($container)... "

    # Check if container is running
    if docker ps --filter "name=$container" --format "{{.Names}}" | grep -q "^${container}$"; then
        # Check health status if healthcheck is defined
        health=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "$container" 2>/dev/null)

        # Get container state
        state=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null)

        if [ "$health" == "healthy" ]; then
            echo -e "${GREEN}✓ PASSED${NC} (Status: $state, Health: $health)"
            return 0
        elif [ "$health" == "no-healthcheck" ] && [ "$state" == "running" ]; then
            echo -e "${GREEN}✓ PASSED${NC} (Status: $state, Health: N/A)"
            return 0
        elif [ "$health" == "starting" ]; then
            echo -e "${YELLOW}⚠ WARNING${NC} (Status: $state, Health: $health - still initializing)"
            return 1
        else
            echo -e "${RED}✗ FAILED${NC} (Status: $state, Health: $health)"
            return 1
        fi
    else
        echo -e "${RED}✗ FAILED${NC} (Container not running)"
        return 1
    fi
}

# Test function to get container uptime
get_container_uptime() {
    local container=$1
    local started=$(docker inspect --format='{{.State.StartedAt}}' "$container" 2>/dev/null)

    if [ -n "$started" ]; then
        echo "$started"
    else
        echo "N/A"
    fi
}

# Define all services and their container names (using indexed arrays for compatibility)
services_names=(
    "Frontend"
    "Backend"
    "Redis"
    "Ollama"
    "Crawl4AI"
    "Grafana"
    "ComfyUI"
    "Langflow"
    "MCPO-Server"
)

services_containers=(
    "cerebraui-frontend"
    "cerebraui-backend"
    "cerebraui-redis"
    "ollama"
    "crawl4ai"
    "lgtm"
    "comfyui"
    "langflow"
    "mcpo-server"
)

echo ""
echo "Running health checks on all containers..."
echo "------------------------------------------"

# Run tests on all services
failed=0
passed=0
warning=0

for i in "${!services_names[@]}"; do
    if test_container_health "${services_names[$i]}" "${services_containers[$i]}"; then
        ((passed++))
    else
        # Check if it's a warning (starting) or failure
        health=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no-healthcheck{{end}}' "${services_containers[$i]}" 2>/dev/null)
        if [ "$health" == "starting" ]; then
            ((warning++))
        else
            ((failed++))
        fi
    fi
done

# Display detailed summary
echo ""
echo "=========================================="
echo "           Health Check Summary"
echo "=========================================="
echo "Total Containers:    ${#services_names[@]}"
echo -e "Healthy:             ${GREEN}$passed${NC}"
if [ $warning -gt 0 ]; then
    echo -e "Starting:            ${YELLOW}$warning${NC}"
fi
echo -e "Failed:              ${RED}$failed${NC}"
echo ""

# Show container details if there are failures
if [ $failed -gt 0 ] || [ $warning -gt 0 ]; then
    echo "Container Details:"
    echo "------------------------------------------"
    for i in "${!services_names[@]}"; do
        service="${services_names[$i]}"
        container="${services_containers[$i]}"
        if docker ps -a --filter "name=$container" --format "{{.Names}}" | grep -q "^${container}$"; then
            state=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null)
            uptime=$(get_container_uptime "$container")
            echo "  $service ($container):"
            echo "    State: $state"
            echo "    Started: $uptime"
        else
            echo "  $service ($container): NOT FOUND"
        fi
    done
    echo "=========================================="
fi

# Exit with appropriate status code
if [ $failed -gt 0 ]; then
    echo -e "${RED}✗ Health check failed${NC}"
    exit 1
elif [ $warning -gt 0 ]; then
    echo -e "${YELLOW}⚠ Some containers are still starting${NC}"
    exit 1
else
    echo -e "${GREEN}✓ All containers are healthy${NC}"
    exit 0
fi