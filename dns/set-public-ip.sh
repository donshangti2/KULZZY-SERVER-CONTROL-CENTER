#!/bin/bash

# =====================================================
# KULZZY DNS PUBLIC IP CONFIGURATOR
# VERSION 1.0
# =====================================================

set -e

BASE="/srv/kulzzy"

ZONE="$BASE/dns/zones/kulzzyradio.com.zone"

echo "=============================================="
echo "       KULZZY DNS IP CONFIGURATOR"
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
# CHECK ZONE
# =====================================================

if [ ! -f "$ZONE" ]; then

    echo "ERROR:"
    echo "DNS zone file not found."

    echo "$ZONE"

    exit 1

fi

# =====================================================
# DETECT PUBLIC IP
# =====================================================

echo "Detecting public IP..."

PUBLIC_IP=""

for SERVICE in \
    "https://api.ipify.org" \
    "https://ifconfig.me/ip" \
    "https://icanhazip.com"
do

    if command -v curl >/dev/null 2>&1; then

        PUBLIC_IP="$(
            curl \
                -4 \
                -fsS \
                --max-time 5 \
                "$SERVICE" \
                2>/dev/null \
                || true
        )"

    fi

    if [ -n "$PUBLIC_IP" ]; then
        break
    fi

done

# =====================================================
# VALIDATE IP
# =====================================================

if [ -z "$PUBLIC_IP" ]; then

    echo ""
    echo "ERROR: Could not detect public IP."
    echo ""
    echo "You can manually provide it:"
    echo ""
    echo "PUBLIC_IP=YOUR_SERVER_IP"
    echo ""
    exit 1

fi

echo ""
echo "Detected public IP:"
echo "$PUBLIC_IP"
echo ""

# =====================================================
# VALIDATE IPv4
# =====================================================

if ! echo "$PUBLIC_IP" | \
    grep -Eq \
    '^[0-9]{1,3}(\.[0-9]{1,3}){3}$'
then

    echo "ERROR: Invalid IPv4 address."

    exit 1

fi

# =====================================================
# BACKUP
# =====================================================

BACKUP="$ZONE.backup.$(
    date +%Y%m%d%H%M%S
)"

cp \
    "$ZONE" \
    "$BACKUP"

echo "Backup created:"
echo "$BACKUP"

# =====================================================
# REPLACE SERVER_IP
# =====================================================

sed -i \
    "s/SERVER_IP/$PUBLIC_IP/g" \
    "$ZONE"

# =====================================================
# DISPLAY RESULT
# =====================================================

echo ""
echo "DNS zone updated."
echo ""

grep \
    -E \
    '^(ns1|ns2|@|www|api|control|code|radio|storage)' \
    "$ZONE" \
    || true

echo ""

echo "=============================================="
echo "       KULZZY DNS IP CONFIGURED"
echo "=============================================="
