#!/bin/bash

echo "========================================"
echo "        KULZZY HEALTH CHECK"
echo "========================================"

PROJECT="/srv/kulzzy"

cd "$PROJECT"

echo ""
echo "Docker:"
docker --version

echo ""
echo "Containers:"
docker compose ps

echo ""
echo "API:"
curl -fsS http://127.0.0.1:5000/ || {
    echo "API OFFLINE"
    exit 1
}

echo ""
echo ""
echo "========================================"
echo "        KULZZY SERVER HEALTHY"
echo "========================================"
