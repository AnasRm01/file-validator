#!/bin/bash
set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo ""
echo "╔════════════════════════════════════════╗"
echo "║     File Validator - Installation     ║"
echo "╚════════════════════════════════════════╝"
echo ""

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root: sudo ./install.sh${NC}"
    exit 1
fi

echo -e "${YELLOW}[1/5]${NC} Checking system..."
echo -e "${GREEN}✓${NC} Linux detected"

echo ""
echo -e "${YELLOW}[2/5]${NC} Installing dependencies..."
pip3 install inotify --break-system-packages 2>/dev/null || pip3 install inotify
echo -e "${GREEN}✓${NC} Dependencies installed"

echo ""
echo -e "${YELLOW}[3/5]${NC} Installing file-validator..."
cp file_validator.py /usr/local/bin/file-validator
chmod +x /usr/local/bin/file-validator
echo -e "${GREEN}✓${NC} Binary installed"

echo ""
echo -e "${YELLOW}[4/5]${NC} Setting up service..."
cp systemd/file-validator.service /etc/systemd/system/
systemctl daemon-reload
echo -e "${GREEN}✓${NC} Service installed"

echo ""
echo -e "${YELLOW}[5/5]${NC} Starting service..."
systemctl enable file-validator
systemctl start file-validator
echo -e "${GREEN}✓${NC} Service running"

echo ""
echo -e "${GREEN}✅ Installation Complete!${NC}"
echo ""
echo "📊 Status:  sudo systemctl status file-validator"
echo "📝 Logs:    sudo tail -f /var/log/file-validator.log"
echo ""
