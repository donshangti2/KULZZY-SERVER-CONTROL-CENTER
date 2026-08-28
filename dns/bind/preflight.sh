#!/bin/bash

# =====================================================
# KULZZY DNS PRE-FLIGHT CHECK
# VERSION 1.0
# =====================================================

echo "=============================================="
echo "       KULZZY DNS PRE-FLIGHT"
echo "=============================================="
echo ""

PASS=0
FAIL=0
WARN=0


# =====================================================
# CHECK COMMAND
# =====================================================

check_command() {

    NAME="$1"
    COMMAND="$2"

    if command -v "$COMMAND" >/dev/null 2>&1; then

        echo "[OK] $NAME"
        PASS=$((PASS + 1))

    else

        echo "[MISSING] $NAME"
        FAIL=$((FAIL + 1))

    fi
}


# =====================================================
# OPERATING SYSTEM
# =====================================================

echo "OPERATING SYSTEM"
echo "----------------------------------------------"

if [ -f /etc/os-release ]; then

    . /etc/os-release

    echo "OS: $PRETTY_NAME"

else

    echo "[WARNING] /etc/os-release not found"
    WARN=$((WARN + 1))

fi

echo ""


# =====================================================
# CPU
# =====================================================

echo "CPU"
echo "----------------------------------------------"

echo "Processor:"
grep -m1 "model name" /proc/cpuinfo 2>/dev/null \
    || echo "Unavailable"

echo ""

echo "CPU cores:"
nproc 2>/dev/null \
    || echo "Unavailable"

echo ""


# =====================================================
# MEMORY
# =====================================================

echo "MEMORY"
echo "----------------------------------------------"

free -h 2>/dev/null \
    || echo "Memory information unavailable"

echo ""


# =====================================================
# STORAGE
# =====================================================

echo "STORAGE"
echo "----------------------------------------------"

df -h /

echo ""


# =====================================================
# NETWORK
# =====================================================

echo "NETWORK"
echo "----------------------------------------------"

echo "Hostname:"
hostname

echo ""

echo "Local IP addresses:"
hostname -I

echo ""

echo "Default route:"
ip route 2>/dev/null \
    | grep default \
    || echo "No default route detected"

echo ""


# =====================================================
# INTERNET
# =====================================================

echo "INTERNET CONNECTIVITY"
echo "----------------------------------------------"

if ping \
    -c 1 \
    -W 3 \
    1.1.1.1 \
    >/dev/null 2>&1
then

    echo "[OK] Internet connectivity"
    PASS=$((PASS + 1))

else

    echo "[FAIL] Internet connectivity"
    FAIL=$((FAIL + 1))

fi

echo ""


# =====================================================
# DNS SOFTWARE
# =====================================================

echo "DNS SOFTWARE"
echo "----------------------------------------------"

check_command \
    "BIND named" \
    "named"

check_command \
    "named-checkconf" \
    "named-checkconf"

check_command \
    "named-checkzone" \
    "named-checkzone"

check_command \
    "dig" \
    "dig"

echo ""


# =====================================================
# KULZZY FILES
# =====================================================

echo "KULZZY DNS FILES"
echo "----------------------------------------------"

FILES=(

    "/srv/kulzzy/dns/dns_server.py"

    "/srv/kulzzy/dns/install-dns.sh"

    "/srv/kulzzy/dns/set-public-ip.sh"

    "/srv/kulzzy/dns/validate-zone.sh"

    "/srv/kulzzy/dns/preflight.sh"

    "/srv/kulzzy/dns/bind/kulzzyradio.com.conf"

    "/srv/kulzzy/dns/bind/named.conf.options"

    "/srv/kulzzy/dns/bind/install-bind.sh"

    "/srv/kulzzy/dns/zones/kulzzyradio.com.zone"

)

for FILE in "${FILES[@]}"; do

    if [ -f "$FILE" ]; then

        echo "[OK] $FILE"
        PASS=$((PASS + 1))

    else

        echo "[MISSING] $FILE"
        FAIL=$((FAIL + 1))

    fi

done

echo ""


# =====================================================
# DNS PORT
# =====================================================

echo "PORT 53"
echo "----------------------------------------------"

if ss -lun 2>/dev/null \
    | grep -q ':53 '
then

    echo "[INFO] UDP port 53 is currently listening."

else

    echo "[INFO] UDP port 53 is not listening yet."

fi


if ss -ltn 2>/dev/null \
    | grep -q ':53 '
then

    echo "[INFO] TCP port 53 is currently listening."

else

    echo "[INFO] TCP port 53 is not listening yet."

fi

echo ""


# =====================================================
# PUBLIC IP
# =====================================================

echo "PUBLIC IP"
echo "----------------------------------------------"

if command -v curl >/dev/null 2>&1; then

    PUBLIC_IP="$(
        curl \
            -4 \
            -fsS \
            --max-time 5 \
            https://api.ipify.org \
            2>/dev/null \
            || true
    )


    if [ -n "$PUBLIC_IP" ]; then

        echo "Detected public IPv4:"
        echo "$PUBLIC_IP"

    else

        echo "[WARNING] Could not detect public IPv4."
        WARN=$((WARN + 1))

    fi

else

    echo "[WARNING] curl is not installed."
    WARN=$((WARN + 1))

fi

echo ""


# =====================================================
# SUMMARY
# =====================================================

echo "=============================================="
echo "       PRE-FLIGHT SUMMARY"
echo "=============================================="

echo ""
echo "PASSED : $PASS"
echo "FAILED : $FAIL"
echo "WARNINGS: $WARN"
echo ""


if [ "$FAIL" -eq 0 ]; then

    echo "RESULT: READY FOR NEXT DNS CONFIGURATION STEP."

else

    echo "RESULT: NOT READY."
    echo "Fix the missing requirements before activation."

fi

echo ""
echo "=============================================="
