#!/bin/bash

# =====================================================
# KULZZY DNS SERVICE LAUNCHER
# =====================================================

set -e

BASE="/srv/kulzzy"

echo "Starting Kulzzy DNS Server..."

exec /usr/bin/python3 \
    "$BASE/dns/dns_server.py"
