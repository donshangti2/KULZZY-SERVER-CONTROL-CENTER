#!/bin/bash

set -e

echo "========================================"
echo "       KULZZY DEPLOYMENT ENGINE"
echo "========================================"

PROJECT="/srv/kulzzy"

cd "$PROJECT"

echo "[1/5] Pulling latest code..."

git pull origin main

echo "[2/5] Checking Docker..."

docker --version

echo "[3/5] Building Kulzzy services..."

docker compose build

echo "[4/5] Starting services..."

docker compose up -d

echo "[5/5] Checking service status..."

docker compose ps

echo ""
echo "========================================"
echo "       KULZZY DEPLOYMENT COMPLETE"
echo "========================================"
