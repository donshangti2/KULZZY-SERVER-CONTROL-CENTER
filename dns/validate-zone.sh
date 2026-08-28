#!/bin/bash

# =====================================================
# KULZZY DNS ZONE VALIDATOR
# VERSION 1.0
# =====================================================

set -e

BASE="/srv/kulzzy"

ZONE="$BASE/dns/zones/kulzzyradio.com.zone"

echo "=============================================="
echo "       KULZZY DNS ZONE VALIDATOR"
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

    echo "ERROR: Zone file not found:"
    echo "$ZONE"

    exit 1

fi

# =====================================================
# CHECK REQUIRED SOFTWARE
# =====================================================

if ! command -v named-checkzone >/dev/null 2>&1; then

    echo "ERROR: named-checkzone is not installed."

    echo ""
    echo "Install the DNS validation tools first."

    exit 1

fi

# =====================================================
# VALIDATE
# =====================================================

echo "Validating:"
echo "$ZONE"
echo ""

named-checkzone \
    kulzzyradio.com \
    "$ZONE"

RESULT=$?

echo ""

# =====================================================
# RESULT
# =====================================================

if [ "$RESULT" -eq 0 ]; then

    echo "=============================================="
    echo "       DNS ZONE VALID"
    echo "=============================================="

else

    echo "=============================================="
    echo "       DNS ZONE INVALID"
    echo "=============================================="

    exit 1

fi
