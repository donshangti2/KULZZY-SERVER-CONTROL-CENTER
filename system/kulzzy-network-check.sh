#!/bin/bash

# =====================================================
# KULZZY NETWORK CHECK
# VERSION 1.0
# =====================================================

echo "=============================================="
echo "       KULZZY NETWORK CHECK"
echo "=============================================="

echo ""

echo "Hostname:"
hostname

echo ""

echo "Local IP addresses:"
hostname -I

echo ""

echo "Default route:"
ip route | grep default || true

echo ""

echo "Listening ports:"
ss -tulpn | grep -E ':53|:80|:443|:5000' || true

echo ""

echo "Internet connectivity:"

if ping -c 1 -W 3 1.1.1.1 >/dev/null 2>&1; then

    echo "ONLINE"

else

    echo "OFFLINE"

fi

echo ""

echo "DNS connectivity:"

if command -v dig >/dev/null 2>&1; then

    dig +short example.com

elif command -v nslookup >/dev/null 2>&1; then

    nslookup example.com

else

    echo "dig/nslookup not installed."

fi

echo ""

echo "=============================================="
echo "       NETWORK CHECK COMPLETE"
echo "=============================================="
