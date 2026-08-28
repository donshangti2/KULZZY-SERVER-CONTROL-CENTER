#!/bin/bash

# =====================================================
# KULZZY DNS SOFTWARE INSTALLER
# VERSION 1.0
# =====================================================

set -e

BASE="/srv/kulzzy"

echo "=============================================="
echo "       KULZZY DNS INSTALLER"
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
# DETECT OPERATING SYSTEM
# =====================================================

if [ -f /etc/os-release ]; then
    . /etc/os-release
else
    echo "ERROR: Cannot identify operating system."
    exit 1
fi

echo "Operating system:"
echo "$PRETTY_NAME"
echo ""

# =====================================================
# DEBIAN / UBUNTU
# =====================================================

if [ "$ID" = "ubuntu" ] || \
   [ "$ID" = "debian" ] || \
   [ "$ID_LIKE" = "debian" ]; then

    echo "Installing DNS packages..."

    apt-get update

    apt-get install -y \
        bind9 \
        bind9-utils \
        dnsutils \
        curl

# =====================================================
# RHEL / ROCKY / ALMA
# =====================================================

elif [ "$ID" = "rocky" ] || \
     [ "$ID" = "almalinux" ] || \
     [ "$ID" = "rhel" ] || \
     [ "$ID_LIKE" = "rhel fedora" ]; then

    echo "Installing DNS packages..."

    dnf install -y \
        bind \
        bind-utils \
        curl

# =====================================================
# UNKNOWN OS
# =====================================================

else

    echo "ERROR: Unsupported operating system:"
    echo "$ID"

    exit 1

fi

# =====================================================
# VERIFY TOOLS
# =====================================================

echo ""
echo "Checking DNS tools..."

if command -v named-checkzone >/dev/null 2>&1; then

    echo "named-checkzone: OK"

else

    echo "ERROR: named-checkzone was not installed."

    exit 1

fi


if command -v dig >/dev/null 2>&1; then

    echo "dig: OK"

else

    echo "WARNING: dig was not found."

fi


if command -v nslookup >/dev/null 2>&1; then

    echo "nslookup: OK"

else

    echo "WARNING: nslookup was not found."

fi

# =====================================================
# CREATE DIRECTORIES
# =====================================================

mkdir -p \
    "$BASE/dns/zones"

# =====================================================
# PERMISSIONS
# =====================================================

chmod +x \
    "$BASE/dns/dns_server.py"

chmod +x \
    "$BASE/dns/set-public-ip.sh"

chmod +x \
    "$BASE/dns/validate-zone.sh"

chmod +x \
    "$BASE/dns/install-dns.sh"

# =====================================================
# SYSTEM INFORMATION
# =====================================================

echo ""
echo "DNS software installation complete."

echo ""
echo "Installed tools:"

command -v named-checkzone || true
command -v dig || true
command -v nslookup || true

echo ""
echo "=============================================="
echo "       KULZZY DNS SOFTWARE READY"
echo "=============================================="
