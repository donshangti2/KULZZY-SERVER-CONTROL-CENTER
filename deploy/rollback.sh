#!/bin/bash

set -e

echo "========================================"
echo "          KULZZY ROLLBACK"
echo "========================================"

PROJECT="/srv/kulzzy"

cd "$PROJECT"

echo "[1/4] Finding previous version..."

git checkout HEAD~1

echo "[2/4] Rebuilding services..."

docker compose build

echo "[3/4] Restarting services..."

docker compose up -d

echo "[4/4] Checking services..."

docker compose ps

echo ""
echo "========================================"
echo "          ROLLBACK COMPLETE"
echo "========================================"
