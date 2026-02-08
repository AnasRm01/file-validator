#!/bin/bash
#
# File Validator - Bulletproof Installer
# Works on: Ubuntu, Debian, CentOS, RHEL, Fedora, Rocky Linux, AlmaLinux
#

set -e  # Exit on any error

# ============================================================================
# COLORS AND FORMATTING
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# FUNCTIONS
# ============================================================================

print_banner() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                                                        ║${NC}"
    echo -e "${BLUE}║          File Validator - Production Installer        ║${NC}"
    echo -e "${BLUE}║          v1.1 - Works on All Linux Distros             ║${NC}"
    echo -e "${BLUE}║                                                        ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# ============================================================================
# OS DETECTION
# ============================================================================

detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si | tr '[:upper:]' '[:lower:]')
        VER=$(lsb_release -sr)
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
    
    print_info "Detected OS: $OS $VER"
}

# ============================================================================
# PACKAGE MANAGER DETECTION
# ============================================================================

get_package_manager() {
    if command -v apt-get >/dev/null 2>&1; then
        PKG_MANAGER="apt"
        PKG_UPDATE="apt-get update -qq"
        PKG_INSTALL="apt-get install -y"
    elif command -v yum >/dev/null 2>&1; then
        PKG_MANAGER="yum"
        PKG_UPDATE="yum check-update || true"
        PKG_INSTALL="yum install -y"
    elif command -v dnf >/dev/null 2>&1; then
        PKG_MANAGER="dnf"
        PKG_UPDATE="dnf check-update || true"
        PKG_INSTALL="dnf install -y"
    else
        print_error "No supported package manager found (apt, yum, or dnf)"
        exit 1
    fi
    
    print_info "Package manager: $PKG_MANAGER"
}

# ============================================================================
# PYTHON INSTALLATION
# ============================================================================

install_python() {
    echo ""
    echo -e "${YELLOW}[1/8]${NC} Checking Python3..."
    
    if command -v python3 >/dev/null 2>&1; then
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        print_success "Python3 already installed: $PYTHON_VERSION"
    else
        print_warning "Python3 not found, installing..."
        
        case $PKG_MANAGER in
            apt)
                $PKG_UPDATE
                $PKG_INSTALL python3 python3-pip python3-dev
                ;;
            yum|dnf)
                $PKG_INSTALL python3 python3-pip python3-devel
                ;;
        esac
        
        if command -v python3 >/dev/null 2>&1; then
            print_success "Python3 installed successfully"
        else
            print_error "Failed to install Python3"
            exit 1
        fi
    fi
}

# ============================================================================
# PIP INSTALLATION
# ============================================================================

install_pip() {
    echo ""
    echo -e "${YELLOW}[2/8]${NC} Checking pip3..."
    
    if command -v pip3 >/dev/null 2>&1; then
        print_success "pip3 already installed"
    else
        print_warning "pip3 not found, installing..."
        
        case $PKG_MANAGER in
            apt)
                $PKG_INSTALL python3-pip
                ;;
            yum|dnf)
                $PKG_INSTALL python3-pip
                ;;
        esac
        
        # Alternative: install pip using get-pip.py
        if ! command -v pip3 >/dev/null 2>&1; then
            print_warning "Installing pip via get-pip.py..."
            curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
            python3 /tmp/get-pip.py
            rm /tmp/get-pip.py
        fi
        
        if command -v pip3 >/dev/null 2>&1; then
            print_success "pip3 installed successfully"
        else
            print_error "Failed to install pip3"
            exit 1
        fi
    fi
}

# ============================================================================
# PYTHON DEPENDENCIES
# ============================================================================

install_python_deps() {
    echo ""
    echo -e "${YELLOW}[3/8]${NC} Installing Python dependencies..."
    
    # Try multiple methods to install dependencies
    
    # Method 1: pip with --break-system-packages (Python 3.11+)
    if pip3 install --break-system-packages inotify pyyaml >/dev/null 2>&1; then
        print_success "Dependencies installed (method 1)"
        return 0
    fi
    
    # Method 2: Regular pip install
    if pip3 install inotify pyyaml >/dev/null 2>&1; then
        print_success "Dependencies installed (method 2)"
        return 0
    fi
    
    # Method 3: pip with --user flag
    if pip3 install --user inotify pyyaml >/dev/null 2>&1; then
        print_success "Dependencies installed (method 3)"
        return 0
    fi
    
    # Method 4: Install via package manager (Ubuntu/Debian)
    if [ "$PKG_MANAGER" = "apt" ]; then
        print_warning "Trying system packages..."
        $PKG_INSTALL python3-inotify python3-yaml 2>/dev/null || true
    fi
    
    # Verify installation
    if python3 -c "import inotify; import yaml" 2>/dev/null; then
        print_success "Dependencies verified"
    else
        print_error "Failed to install Python dependencies"
        print_info "Please install manually: pip3 install inotify pyyaml"
        exit 1
    fi
}

# ============================================================================
# INSTALL PROGRAM
# ============================================================================

install_program() {
    echo ""
    echo -e "${YELLOW}[4/8]${NC} Installing File Validator..."
    
    # Check if file exists locally first
    if [ ! -f "file_validator.py" ]; then
        print_warning "Downloading File Validator from GitHub..."
        
        # Download from GitHub
        curl -sSL https://raw.githubusercontent.com/AnasRm01/file-validator/main/file_validator.py -o /tmp/file_validator.py
        
        if [ ! -f /tmp/file_validator.py ]; then
            print_error "Failed to download file_validator.py"
            print_info "Please check your internet connection"
            exit 1
        fi
        
        # Use downloaded file
        cp /tmp/file_validator.py /usr/local/bin/file-validator
        rm /tmp/file_validator.py
    else
        # Use local file
        cp file_validator.py /usr/local/bin/file-validator
    fi
    
    chmod +x /usr/local/bin/file-validator
    
    # Make it executable with proper shebang
    sed -i '1s|^.*$|#!/usr/bin/env python3|' /usr/local/bin/file-validator
    
    print_success "Program installed to /usr/local/bin/file-validator"
}
# ============================================================================
# CREATE DIRECTORIES
# ============================================================================

create_directories() {
    echo ""
    echo -e "${YELLOW}[5/8]${NC} Creating directories..."
    
    # Config directory
    mkdir -p /etc/file-validator
    chmod 755 /etc/file-validator
    
    # Quarantine directory
    mkdir -p /var/quarantine
    chmod 755 /var/quarantine
    
    # Log directory (ensure it exists)
    mkdir -p /var/log
    touch /var/log/file-validator.log
    chmod 644 /var/log/file-validator.log
    
    print_success "Directories created"
}

# ============================================================================
# INSTALL SYSTEMD SERVICE
# ============================================================================

install_service() {
    echo ""
    echo -e "${YELLOW}[6/8]${NC} Installing systemd service..."
    
    # Check if systemd exists
    if ! command -v systemctl >/dev/null 2>&1; then
        print_warning "systemd not detected, skipping service installation"
        print_info "You can run manually: /usr/local/bin/file-validator"
        return 0
    fi
    
    # Create service file
    cat > /etc/systemd/system/file-validator.service << 'EOF'
[Unit]
Description=File Validator - Real-time File Extension Validation
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/file-validator
Restart=on-failure
RestartSec=10s
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    # Reload systemd
    systemctl daemon-reload
    
    print_success "Service installed"
}

# ============================================================================
# START SERVICE
# ============================================================================

start_service() {
    echo ""
    echo -e "${YELLOW}[7/8]${NC} Starting File Validator..."
    
    if ! command -v systemctl >/dev/null 2>&1; then
        print_warning "Starting manually (no systemd)..."
        /usr/local/bin/file-validator &
        sleep 2
        print_success "File Validator started in background"
        return 0
    fi
    
    # Enable and start service
    systemctl enable file-validator >/dev/null 2>&1
    systemctl start file-validator
    
    # Wait a moment
    sleep 2
    
    # Check if running
    if systemctl is-active --quiet file-validator; then
        print_success "Service is running"
    else
        print_error "Service failed to start"
        print_info "Check logs: journalctl -u file-validator -n 20"
        print_info "Or run manually: /usr/local/bin/file-validator"
        exit 1
    fi
}

# ============================================================================
# VERIFY INSTALLATION
# ============================================================================

verify_installation() {
    echo ""
    echo -e "${YELLOW}[8/8]${NC} Verifying installation..."
    
    # Check if program exists
    if [ ! -f /usr/local/bin/file-validator ]; then
        print_error "Program not found"
        exit 1
    fi
    
    # Check if Python dependencies work
    if ! python3 -c "import inotify; import yaml" 2>/dev/null; then
        print_error "Python dependencies not working"
        exit 1
    fi
    
    # Check if log file exists
    if [ ! -f /var/log/file-validator.log ]; then
        print_warning "Log file not created yet (will be created on first event)"
    fi
    
    print_success "Installation verified"
}

# ============================================================================
# MAIN INSTALLATION
# ============================================================================

main() {
    # Check root
    if [ "$EUID" -ne 0 ]; then 
        echo -e "${RED}Error: This script must be run as root${NC}"
        echo "Usage: sudo $0"
        exit 1
    fi
    
    print_banner
    
    # Run installation steps
    detect_os
    get_package_manager
    install_python
    install_pip
    install_python_deps
    install_program
    create_directories
    install_service
    start_service
    verify_installation
    
    # Success message
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                        ║${NC}"
    echo -e "${GREEN}║              ✅ Installation Complete!                 ║${NC}"
    echo -e "${GREEN}║                                                        ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📊 Check status:${NC}      systemctl status file-validator"
    echo -e "${BLUE}📝 View logs:${NC}         tail -f /var/log/file-validator.log"
    echo -e "${BLUE}⚙️  Configuration:${NC}    /etc/file-validator/config.yaml"
    echo -e "${BLUE}📁 Quarantine:${NC}       /var/quarantine"
    echo ""
    echo -e "${BLUE}🧪 Test detection:${NC}"
    echo -e "   ${YELLOW}echo '%PDF-1.4 fake' > /tmp/test.jpg${NC}"
    echo -e "   ${YELLOW}tail /var/log/file-validator.log${NC}"
    echo ""
    echo -e "${GREEN}⭐ Star us on GitHub:${NC} https://github.com/AnasRm01/file-validator"
    echo ""
}

# Run main function
main "$@"
