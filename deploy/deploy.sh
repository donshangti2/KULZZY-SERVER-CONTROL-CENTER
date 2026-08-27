#!/bin/bash

set -e

PROJECT_DIR="/opt/kulzzy/server-control-center"
BACKUP_DIR="/srv/kulzzy/backups/deployments"
LOG_FILE="/srv/kulzzy/logs/deploy.log"

SERVICE_NAME="kulzzy-server-api"

mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

echo "========================================"
echo " KULZZY DEPLOYMENT ENGINE"
echo "========================================"
echo ""

echo "[1/7] Starting deployment..."

date '+%Y-%m-%d %H:%M:%S' \
    >> "$LOG_FILE"

echo "[2/7] Checking project..."

if [ ! -d "$PROJECT_DIR" ]; then

    echo "ERROR: Project directory not found."

    exit 1

fi

cd "$PROJECT_DIR"

echo "[3/7] Creating backup..."

BACKUP_NAME="backup-$(date '+%Y%m%d-%H%M%S')"

mkdir -p "$BACKUP_DIR/$BACKUP_NAME"

cp -r \
    api \
    Dockerfile \
    docker-compose.yml \
    requirements.txt \
    "$BACKUP_DIR/$BACKUP_NAME/" \
    2>/dev/null || true

echo "[4/7] Updating source code..."

if [ -d ".git" ]; then

    git fetch --all

    git pull --ff-only

else

    echo "WARNING: Git repository not detected."

fi

echo "[5/7] Building Kulzzy services..."

docker compose build

echo "[6/7] Starting services..."

docker compose up -d

echo "[7/7] Checking service..."

sleep 5

if docker compose ps | grep -q "$SERVICE_NAME"; then

    echo ""
    echo "DEPLOYMENT SUCCESSFUL"
    echo ""

    echo "Kulzzy Server API is running."

    echo ""

    docker compose ps

else

    echo ""
    echo "DEPLOYMENT FAILED"
    echo ""

    docker compose logs \
        --tail=100

    exit 1

fi

echo ""
echo "Deployment completed."
echo ""
