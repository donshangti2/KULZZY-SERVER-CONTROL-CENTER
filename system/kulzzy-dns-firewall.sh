#!/bin/bash

# =====================================================
# KULZZY DNS FIREWALL
# VERSION 1.0
# =====================================================

set -e

echo "=============================================="
echo "       KULZZY DNS FIREWALL"
echo "=============================================="

# -----------------------------------------------------
# REQUIRE ROOT
# -----------------------------------------------------

if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root."
    exit 1
fi

# -----------------------------------------------------
# DETECT FIREWALL
# -----------------------------------------------------

if command -v ufw >/dev/null 2>&1; then

    echo "UFW detected."

    ufw allow 53/udp
    ufw allow 53/tcp

    echo "DNS ports opened."

elif command -v firewall-cmd >/dev/null 2>&1; then

    echo "Firewalld detected."

    firewall-cmd \
        --permanent \
        --add-service=dns

    firewall-cmd --reload

    echo "DNS ports opened."

else

    echo "No supported firewall manager detected."
    echo "You will need to configure ports 53 manually."
fi

echo ""
echo "DNS firewall configuration complete."
echo ""
