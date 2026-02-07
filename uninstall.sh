#!/bin/bash
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "Uninstalling File Validator..."

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root: sudo ./uninstall.sh${NC}"
    exit 1
fi

systemctl stop file-validator 2>/dev/null
systemctl disable file-validator 2>/dev/null
rm -f /usr/local/bin/file-validator
rm -f /etc/systemd/system/file-validator.service
systemctl daemon-reload 2>/dev/null
rm -f /var/log/file-validator.log

echo -e "${GREEN}✅ Uninstalled successfully${NC}"
