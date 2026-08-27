#!/bin/bash

set -e

PROJECT_DIR="/opt/kulzzy/server-control-center"
BACKUP_DIR="/srv/kulzzy/backups/deployments"

echo "========================================"
echo " KULZZY DEPLOYMENT ROLLBACK"
echo "========================================"
echo ""

LATEST_BACKUP=$(find "$BACKUP_DIR" \
    -mindepth 1 \
    -maxdepth 1 \
    -type d \
    | sort \
    | tail -n 1)

if [ -z "$LATEST_BACKUP" ]; then

    echo "No deployment backup found."

    exit 1

fi

echo "Using backup:"
echo "$LATEST_BACKUP"
echo ""

cd "$PROJECT_DIR"

echo "Stopping current service..."

docker compose down

echo "Restoring backup..."

cp -r \
    "$LATEST_BACKUP/api" \
    .

cp \
    "$LATEST_BACKUP/Dockerfile" \
    .

cp \
    "$LATEST_BACKUP/docker-compose.yml" \
    .

cp \
    "$LATEST_BACKUP/requirements.txt" \
    .

echo "Rebuilding..."

docker compose build

echo "Starting previous version..."

docker compose up -d

echo ""

echo "ROLLBACK COMPLETE"

docker compose ps
