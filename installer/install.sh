#!/bin/bash

set -e

# =====================================================
# KULZZY SERVER INSTALLER
# VERSION 1.0
# =====================================================

PROJECT="/srv/kulzzy"

echo ""
echo "=============================================="
echo "       KULZZY SERVER INSTALLER"
echo "=============================================="
echo ""
echo "Installing Kulzzy Server..."
echo ""


# =====================================================
# ROOT CHECK
# =====================================================

if [ "$EUID" -ne 0 ]; then

    echo "ERROR:"
    echo "Please run this installer as root."
    exit 1

fi


# =====================================================
# OPERATING SYSTEM
# =====================================================

echo "[1/10] Checking operating system..."

if [ -f /etc/os-release ]; then

    . /etc/os-release

    echo "OS: $PRETTY_NAME"

else

    echo "Unable to identify operating system."

fi


# =====================================================
# SYSTEM UPDATE
# =====================================================

echo ""
echo "[2/10] Updating system..."

apt-get update

apt-get upgrade -y


# =====================================================
# BASIC SOFTWARE
# =====================================================

echo ""
echo "[3/10] Installing required software..."

apt-get install -y \
    git \
    curl \
    wget \
    unzip \
    python3 \
    python3-pip \
    python3-venv \
    ca-certificates \
    gnupg \
    lsb-release \
    ufw


# =====================================================
# DOCKER
# =====================================================

echo ""
echo "[4/10] Installing Docker..."

if command -v docker >/dev/null 2>&1; then

    echo "Docker already installed."

else

    install -m 0755 -d /etc/apt/keyrings

    curl -fsSL \
        https://download.docker.com/linux/ubuntu/gpg \
        -o /etc/apt/keyrings/docker.asc

    chmod a+r \
        /etc/apt/keyrings/docker.asc

    echo \
"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
        > /etc/apt/sources.list.d/docker.list

    apt-get update

    apt-get install -y \
        docker-ce \
        docker-ce-cli \
        containerd.io \
        docker-buildx-plugin \
        docker-compose-plugin

fi


# =====================================================
# ENABLE DOCKER
# =====================================================

echo ""
echo "[5/10] Enabling Docker..."

systemctl enable docker

systemctl start docker


# =====================================================
# KULZZY DIRECTORIES
# =====================================================

echo ""
echo "[6/10] Creating Kulzzy directories..."

mkdir -p "$PROJECT"

mkdir -p "$PROJECT/api"

mkdir -p "$PROJECT/config"

mkdir -p "$PROJECT/deploy"

mkdir -p "$PROJECT/services"

mkdir -p "$PROJECT/storage"

mkdir -p "$PROJECT/backups"

mkdir -p "$PROJECT/logs"


# =====================================================
# STORAGE DIRECTORIES
# =====================================================

echo ""
echo "[7/10] Creating Kulzzy storage..."

mkdir -p /kulzzy/audio

mkdir -p /kulzzy/celebrants

mkdir -p /kulzzy/websites

mkdir -p /kulzzy/repositories

mkdir -p /kulzzy/uploads

mkdir -p /kulzzy/backups


# =====================================================
# PYTHON ENVIRONMENT
# =====================================================

echo ""
echo "[8/10] Creating Python environment..."

python3 -m venv \
    "$PROJECT/venv"

"$PROJECT/venv/bin/pip" install \
    --upgrade pip

"$PROJECT/venv/bin/pip" install \
    flask \
    psutil


# =====================================================
# FIREWALL
# =====================================================

echo ""
echo "[9/10] Configuring firewall..."

ufw allow OpenSSH

ufw allow 5000/tcp

ufw --force enable


# =====================================================
# PERMISSIONS
# =====================================================

echo ""
echo "[10/10] Setting permissions..."

chmod +x \
    "$PROJECT/deploy/deploy.sh" \
    2>/dev/null || true

chmod +x \
    "$PROJECT/deploy/rollback.sh" \
    2>/dev/null || true

chmod +x \
    "$PROJECT/deploy/health-check.sh" \
    2>/dev/null || true


# =====================================================
# SYSTEM INFORMATION
# =====================================================

HOSTNAME_VALUE=$(hostname)

IP_ADDRESS=$(hostname -I | awk '{print $1}')


# =====================================================
# INSTALLATION COMPLETE
# =====================================================

echo ""
echo "=============================================="
echo "       KULZZY SERVER READY"
echo "=============================================="
echo ""

echo "Hostname:"
echo "$HOSTNAME_VALUE"

echo ""

echo "Server IP:"
echo "$IP_ADDRESS"

echo ""

echo "Project:"
echo "$PROJECT"

echo ""

echo "Storage:"
echo "/kulzzy"

echo ""

echo "API:"
echo "http://$IP_ADDRESS:5000"

echo ""

echo "Docker:"
docker --version

echo ""

echo "=============================================="
echo "       INSTALLATION COMPLETE"
echo "=============================================="
echo ""
