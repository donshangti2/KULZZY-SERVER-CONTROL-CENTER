#!/bin/bash

# =====================================================
# KULZZY DNS MANAGER
# VERSION 1.0
# =====================================================

set -e

BASE="/srv/kulzzy"

DNS_SERVICE="kulzzy-dns.service"

echo "=============================================="
echo "       KULZZY DNS MANAGER"
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
# CHECK DNS FILES
# =====================================================

if [ ! -f "$BASE/dns/dns_server.py" ]; then

    echo "ERROR:"
    echo "DNS server program not found."

    exit 1

fi


if [ ! -f "$BASE/dns/zones/kulzzyradio.com.zone" ]; then

    echo "ERROR:"
    echo "DNS zone file not found."

    exit 1

fi


if [ ! -f "$BASE/system/kulzzy-dns.service" ]; then

    echo "ERROR:"
    echo "DNS systemd service file not found."

    exit 1

fi


# =====================================================
# PERMISSIONS
# =====================================================

chmod +x \
    "$BASE/dns/dns_server.py"


chmod +x \
    "$BASE/system/start-kulzzy-dns.sh"


chmod +x \
    "$BASE/system/kulzzy-dns-firewall.sh"


chmod +x \
    "$BASE/system/kulzzy-network-check.sh"


# =====================================================
# SYSTEMD
# =====================================================

echo "Installing DNS systemd service..."

cp \
    "$BASE/system/kulzzy-dns.service" \
    "/etc/systemd/system/kulzzy-dns.service"


systemctl daemon-reload


# =====================================================
# FIREWALL
# =====================================================

echo ""
echo "Configuring DNS firewall..."

"$BASE/system/kulzzy-dns-firewall.sh"


# =====================================================
# ENABLE SERVICE
# =====================================================

echo ""
echo "Enabling Kulzzy DNS..."

systemctl enable \
    "$DNS_SERVICE"


# =====================================================
# STATUS
# =====================================================

echo ""
echo "Kulzzy DNS service status:"
echo ""

systemctl status \
    "$DNS_SERVICE" \
    --no-pager \
    || true


echo ""
echo "=============================================="
echo "       KULZZY DNS READY"
echo "=============================================="
echo ""
echo "Service:"
echo "  $DNS_SERVICE"
echo ""
echo "DNS zone:"
echo "  $BASE/dns/zones/kulzzyradio.com.zone"
echo ""
echo "DNS server:"
echo "  $BASE/dns/dns_server.py"
echo ""
echo "IMPORTANT:"
echo "The DNS service has been ENABLED."
echo "It has NOT been started automatically by this script."
echo ""
