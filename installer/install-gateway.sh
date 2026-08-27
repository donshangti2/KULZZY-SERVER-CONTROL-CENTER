#!/bin/bash

set -e

# =====================================================
# KULZZY GATEWAY INSTALLER
# VERSION 1.0
# =====================================================

PROJECT="/srv/kulzzy"

SYSTEM_DIR="$PROJECT/system"

NGINX_CONFIG="$SYSTEM_DIR/nginx.conf"

SERVICE_FILE="$SYSTEM_DIR/kulzzy-gateway.service"


echo ""
echo "=============================================="
echo "       KULZZY GATEWAY INSTALLER"
echo "=============================================="
echo ""


# =====================================================
# ROOT CHECK
# =====================================================

if [ "$EUID" -ne 0 ]; then

    echo "ERROR:"
    echo "Run this installer as root."

    exit 1

fi


# =====================================================
# PROJECT CHECK
# =====================================================

if [ ! -d "$PROJECT" ]; then

    echo "Creating Kulzzy project directory..."

    mkdir -p "$PROJECT"

fi


mkdir -p "$SYSTEM_DIR"


# =====================================================
# INSTALL NGINX
# =====================================================

echo "[1/8] Installing NGINX..."

apt-get update

apt-get install -y nginx


# =====================================================
# BACKUP EXISTING CONFIGURATION
# =====================================================

echo "[2/8] Backing up existing NGINX configuration..."

if [ -f /etc/nginx/nginx.conf ]; then

    cp \
        /etc/nginx/nginx.conf \
        /etc/nginx/nginx.conf.kulzzy-backup

fi


# =====================================================
# INSTALL KULZZY CONFIG
# =====================================================

echo "[3/8] Installing Kulzzy Gateway configuration..."

if [ ! -f "$NGINX_CONFIG" ]; then

    echo "ERROR:"
    echo "Kulzzy nginx.conf was not found."

    echo ""
    echo "Expected:"
    echo "$NGINX_CONFIG"

    exit 1

fi


cp \
    "$NGINX_CONFIG" \
    /etc/nginx/nginx.conf


# =====================================================
# TEST NGINX
# =====================================================

echo "[4/8] Testing NGINX configuration..."

nginx -t


# =====================================================
# INSTALL SERVICE
# =====================================================

echo "[5/8] Installing Kulzzy Gateway service..."

if [ ! -f "$SERVICE_FILE" ]; then

    echo "ERROR:"
    echo "Kulzzy gateway service was not found."

    exit 1

fi


cp \
    "$SERVICE_FILE" \
    /etc/systemd/system/kulzzy-gateway.service


# =====================================================
# SYSTEMD
# =====================================================

echo "[6/8] Reloading system services..."

systemctl daemon-reload

systemctl enable kulzzy-gateway


# =====================================================
# START GATEWAY
# =====================================================

echo "[7/8] Starting Kulzzy Gateway..."

systemctl restart kulzzy-gateway


# =====================================================
# VERIFY
# =====================================================

echo "[8/8] Verifying gateway..."

sleep 2

if systemctl is-active \
    --quiet \
    kulzzy-gateway; then

    echo ""
    echo "KULZZY GATEWAY: ONLINE"

else

    echo ""
    echo "KULZZY GATEWAY: FAILED"

    echo ""

    systemctl status \
        kulzzy-gateway \
        --no-pager

    exit 1

fi


# =====================================================
# LOCAL HEALTH TEST
# =====================================================

echo ""
echo "Testing local gateway..."

if curl \
    --silent \
    --fail \
    http://127.0.0.1/gateway-health \
    >/dev/null; then

    echo "Gateway health check: OK"

else

    echo "Gateway health check failed."

    exit 1

fi


# =====================================================
# SERVER INFORMATION
# =====================================================

IP_ADDRESS=$(
    hostname -I |
    awk '{print $1}'
)


echo ""
echo "=============================================="
echo "       KULZZY GATEWAY READY"
echo "=============================================="
echo ""

echo "Server IP:"
echo "$IP_ADDRESS"

echo ""

echo "Local gateway:"
echo "http://127.0.0.1"

echo ""

echo "Health:"
echo "http://$IP_ADDRESS/gateway-health"

echo ""

echo "Gateway service:"
echo "kulzzy-gateway"

echo ""

echo "=============================================="
echo "       INSTALLATION COMPLETE"
echo "=============================================="
echo ""
