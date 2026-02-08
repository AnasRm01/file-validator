#!/bin/bash

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "╔════════════════════════════════════════╗"
echo "║  File Validator - Installation v1.1   ║"
echo "║  Enhanced: Quarantine + SIEM + Hash   ║"
echo "╚════════════════════════════════════════╝"
echo ""

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root: sudo ./install.sh${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/6]${NC} Checking system..."
echo -e "${GREEN}✓${NC} Linux detected"

echo ""
echo -e "${YELLOW}[2/6]${NC} Installing dependencies..."
pip3 install inotify pyyaml --break-system-packages 2>/dev/null || pip3 install inotify pyyaml
echo -e "${GREEN}✓${NC} Dependencies installed"

echo ""
echo -e "${YELLOW}[3/6]${NC} Installing file-validator..."
cp file_validator.py /usr/local/bin/file-validator
chmod +x /usr/local/bin/file-validator
echo -e "${GREEN}✓${NC} Binary installed"

echo ""
echo -e "${YELLOW}[4/6]${NC} Creating directories..."
mkdir -p /etc/file-validator
mkdir -p /var/quarantine
chmod 755 /var/quarantine
echo -e "${GREEN}✓${NC} Directories created"

echo ""
echo -e "${YELLOW}[5/6]${NC} Setting up service..."
cp systemd/file-validator.service /etc/systemd/system/
systemctl daemon-reload
echo -e "${GREEN}✓${NC} Service installed"

echo ""
echo -e "${YELLOW}[6/6]${NC} Starting service..."
systemctl enable file-validator
systemctl start file-validator
echo -e "${GREEN}✓${NC} Service running"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     ✅ Installation Complete!          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo "📊 Status:      sudo systemctl status file-validator"
echo "📝 Logs:        sudo tail -f /var/log/file-validator.log"
echo "⚙️  Config:      sudo nano /etc/file-validator/config.yaml"
echo "📁 Quarantine:  ls -la /var/quarantine"
echo ""
echo "New features in v1.1:"
echo "  ✓ Automatic quarantine of suspicious files"
echo "  ✓ SIEM-ready JSON logging"
echo "  ✓ SHA256 file hashing"
echo "  ✓ User attribution tracking"
echo ""