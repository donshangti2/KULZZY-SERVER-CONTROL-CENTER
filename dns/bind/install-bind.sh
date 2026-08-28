#!/bin/bash

# =====================================================
# KULZZY BIND CONFIGURATION INSTALLER
# VERSION 1.0
# =====================================================

set -e

BASE="/srv/kulzzy"

ZONE_CONF="$BASE/dns/bind/kulzzyradio.com.conf"
OPTIONS_CONF="$BASE/dns/bind/named.conf.options"

echo "=============================================="
echo "       KULZZY BIND INSTALLER"
echo "=============================================="
echo ""

# =====================================================
# REQUIRE ROOT
# =====================================================

if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Run this script as root."
    exit 1
fi

# =====================================================
# CHECK FILES
# =====================================================

if [ ! -f "$ZONE_CONF" ]; then

    echo "ERROR: Zone configuration not found:"
    echo "$ZONE_CONF"

    exit 1

fi

if [ ! -f "$OPTIONS_CONF" ]; then

    echo "ERROR: Options configuration not found:"
    echo "$OPTIONS_CONF"

    exit 1

fi

# =====================================================
# CHECK BIND
# =====================================================

if ! command -v named-checkconf >/dev/null 2>&1; then

    echo "ERROR: BIND is not installed."

    echo ""
    echo "Run first:"
    echo "$BASE/dns/install-dns.sh"

    exit 1

fi

# =====================================================
# BACKUP EXISTING CONFIG
# =====================================================

BACKUP_DIR="/root/kulzzy-bind-backup-$(date +%Y%m%d%H%M%S)"

mkdir -p "$BACKUP_DIR"

if [ -f /etc/bind/named.conf.options ]; then
    cp /etc/bind/named.conf.options "$BACKUP_DIR/"
fi

if [ -f /etc/bind/named.conf.local ]; then
    cp /etc/bind/named.conf.local "$BACKUP_DIR/"
fi

echo "Backup created:"
echo "$BACKUP_DIR"
echo ""

# =====================================================
# INSTALL OPTIONS
# =====================================================

echo "Installing BIND options..."

cp \
    "$OPTIONS_CONF" \
    /etc/bind/named.conf.options

# =====================================================
# INSTALL ZONE CONFIGURATION
# =====================================================

echo "Installing Kulzzy zone configuration..."

cat \
    "$ZONE_CONF" \
    >> /etc/bind/named.conf.local

# =====================================================
# FIX ZONE PERMISSIONS
# =====================================================

if [ -f "$BASE/dns/zones/kulzzyradio.com.zone" ]; then

    chown root:bind \
        "$BASE/dns/zones/kulzzyradio.com.zone"

    chmod 640 \
        "$BASE/dns/zones/kulzzyradio.com.zone"

fi

# =====================================================
# CHECK CONFIGURATION
# =====================================================

echo ""
echo "Checking BIND configuration..."

named-checkconf

echo "BIND configuration: VALID"

# =====================================================
# CHECK ZONE
# =====================================================

echo ""
echo "Checking Kulzzy DNS zone..."

named-checkzone \
    kulzzyradio.com \
    "$BASE/dns/zones/kulzzyradio.com.zone"

echo ""
echo "=============================================="
echo "       KULZZY BIND CONFIGURATION READY"
echo "=============================================="
echo ""
echo "BIND has been configured."
echo ""
echo "The DNS service has NOT been restarted yet."
echo ""
echo "Backup:"
echo "$BACKUP_DIR"
echo ""
