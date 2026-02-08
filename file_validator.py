#!/usr/bin/env python3
"""
File Validator - Linux Edition v1.1
Real-time file extension validation with quarantine and SIEM logging
"""

import os
import sys
import json
import logging
import hashlib
import time
import shutil
import pwd
from pathlib import Path
from datetime import datetime

# Install dependencies if missing
try:
    import inotify.adapters
    import yaml
except ImportError:
    print("Installing required libraries...")
    os.system("pip3 install inotify pyyaml --break-system-packages")
    import inotify.adapters
    import yaml

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_CONFIG = {
    'monitoring': {
        'paths': [
            '/home',
            '/tmp'
        ],
        'excluded_paths': [
            '/proc',
            '/sys',
            '/dev',
            '/run',
            '/snap'
        ]
    },
    'quarantine': {
        'enabled': True,
        'path': '/var/quarantine',
        'keep_original': False  # If True, copy instead of move
    },
    'logging': {
        'log_file': '/var/log/file-validator.log',
        'log_level': 'INFO',
        'siem_format': True,  # Use JSON format for SIEM
        'console_output': True
    },
    'detection': {
        'calculate_hash': True,
        'get_file_owner': True,
        'max_file_size_mb': 100
    }
}

# Magic number signatures
MAGIC_SIGNATURES = {
    'pdf': [b'%PDF'],
    'png': [b'\x89PNG\r\n\x1a\n'],
    'jpg': [b'\xff\xd8\xff'],
    'jpeg': [b'\xff\xd8\xff'],
    'gif': [b'GIF87a', b'GIF89a'],
    'zip': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],
    'exe': [b'MZ'],
    'elf': [b'\x7fELF'],
    'doc': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],
    'docx': [b'PK\x03\x04'],
    'xlsx': [b'PK\x03\x04'],
    'pptx': [b'PK\x03\x04'],
    'sh': [b'#!/bin/bash', b'#!/bin/sh', b'#!/usr/bin/env bash'],
    'py': [b'#!/usr/bin/python', b'#!/usr/bin/env python'],
    'rar': [b'Rar!\x1a\x07'],
    '7z': [b'7z\xbc\xaf\x27\x1c'],
    'iso': [b'CD001'],
    'tar': [b'ustar'],
    'gz': [b'\x1f\x8b'],
    'bz2': [b'BZ'],
}

# ============================================================================
# SIEM-READY JSON LOGGER
# ============================================================================

class SIEMLogger:
    """Formats logs as JSON for SIEM ingestion (Splunk, ELK, Wazuh)"""
    
    def __init__(self, log_file, siem_format=True, console_output=True):
        self.log_file = log_file
        self.siem_format = siem_format
        self.console_output = console_output
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    def log_event(self, event_type, severity, data):
        """Log event in SIEM-compatible JSON format"""
        if self.siem_format:
            # JSON format for SIEM
            event = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'event_type': event_type,
                'severity': severity,
                'source': 'file-validator-linux',
                'version': '1.1',
                'hostname': os.uname().nodename,
                'data': data
            }
            
            log_line = json.dumps(event)
        else:
            # Plain text format
            log_line = f"{datetime.now().isoformat()} - {severity} - {event_type}: {data}"
        
        # Write to log file
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_line + '\n')
        except PermissionError:
            print(f"ERROR: Cannot write to {self.log_file}. Run as root or check permissions.")
        
        # Console output
        if self.console_output:
            if severity in ['HIGH', 'CRITICAL']:
                print(f"🚨 {event_type}: {data.get('filepath', 'N/A')}")
            elif severity == 'WARNING':
                print(f"⚠️  {event_type}")
            else:
                print(f"ℹ️  {event_type}")

# ============================================================================
# FILE VALIDATOR WITH QUARANTINE
# ============================================================================

class FileValidator:
    """Enhanced file validator with quarantine and SIEM logging"""
    
    def __init__(self, config, siem_logger):
        self.config = config
        self.siem = siem_logger
        self.watch_paths = config['monitoring']['paths']
        self.excluded_paths = config['monitoring']['excluded_paths']
        self.quarantine_dir = config['quarantine']['path']
        
        # Create quarantine directory
        if config['quarantine']['enabled']:
            try:
                os.makedirs(self.quarantine_dir, exist_ok=True)
                self.siem.log_event('SYSTEM_START', 'INFO', {
                    'quarantine_enabled': True,
                    'quarantine_path': self.quarantine_dir
                })
            except PermissionError:
                print(f"WARNING: Cannot create quarantine directory. Run as root.")
                self.config['quarantine']['enabled'] = False
    
    def should_skip_path(self, filepath):
        """Check if path should be excluded from scanning"""
        for excluded in self.excluded_paths:
            if filepath.startswith(excluded):
                return True
        return False
    
    def get_file_size(self, filepath):
        """Get file size in MB"""
        try:
            return os.path.getsize(filepath) / (1024 * 1024)
        except:
            return 0
    
    def read_file_header(self, filepath, bytes_count=16):
        """Read first bytes of file safely"""
        try:
            with open(filepath, 'rb') as f:
                return f.read(bytes_count)
        except (PermissionError, FileNotFoundError, OSError, IsADirectoryError) as e:
            logging.debug(f"Cannot read {filepath}: {e}")
            return None
    
    def calculate_hash(self, filepath):
        """Calculate SHA256 hash of file"""
        if not self.config['detection']['calculate_hash']:
            return None
        
        try:
            sha256 = hashlib.sha256()
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logging.debug(f"Hash calculation failed: {e}")
            return None
    
    def get_file_owner(self, filepath):
        """Get username who owns the file"""
        if not self.config['detection']['get_file_owner']:
            return 'unknown'
        
        try:
            stat_info = os.stat(filepath)
            uid = stat_info.st_uid
            return pwd.getpwuid(uid).pw_name
        except Exception as e:
            return 'unknown'
    
    def identify_file_type(self, header):
        """Identify actual file type from magic number"""
        for file_type, signatures in MAGIC_SIGNATURES.items():
            for sig in signatures:
                if header.startswith(sig):
                    return file_type
        return 'unknown'
    
    def quarantine_file(self, filepath, metadata):
        """Move file to quarantine with metadata"""
        if not self.config['quarantine']['enabled']:
            return None
        
        try:
            # Create timestamped quarantine subfolder
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            quarantine_folder = os.path.join(self.quarantine_dir, timestamp)
            os.makedirs(quarantine_folder, exist_ok=True)
            
            # Determine destination
            filename = os.path.basename(filepath)
            dest_file = os.path.join(quarantine_folder, filename)
            
            # Move or copy file
            if self.config['quarantine']['keep_original']:
                shutil.copy2(filepath, dest_file)
            else:
                shutil.move(filepath, dest_file)
            
            # Save metadata as JSON
            metadata_file = os.path.join(quarantine_folder, 'metadata.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            return dest_file
        except Exception as e:
            logging.error(f"Quarantine failed: {e}")
            return None
    
    def check_magic_mismatch(self, filepath):
        """Check if file extension matches its magic number"""
        # Skip excluded paths
        if self.should_skip_path(filepath):
            return False
        
        # Skip if not a file
        if not os.path.isfile(filepath):
            return False
        
        # Check file size limit
        file_size_mb = self.get_file_size(filepath)
        max_size = self.config['detection']['max_file_size_mb']
        if file_size_mb > max_size:
            logging.debug(f"Skipping large file: {filepath} ({file_size_mb:.2f}MB)")
            return False
        
        # Get file extension
        ext = Path(filepath).suffix.lower().lstrip('.')
        if not ext or ext not in MAGIC_SIGNATURES:
            return False
        
        # Skip text files (no strict magic number)
        if ext == 'txt':
            return False
        
        # Read file header
        header = self.read_file_header(filepath, 32)
        if not header:
            return False
        
        # Check if magic number matches extension
        expected_signatures = MAGIC_SIGNATURES[ext]
        if not expected_signatures:
            return False
        
        matches = any(header.startswith(sig) for sig in expected_signatures)
        
        if not matches:
            # MISMATCH DETECTED!
            self.handle_detection(filepath, ext, header)
            return True
        
        return False
    
    def handle_detection(self, filepath, claimed_ext, header):
        """Handle detected mismatch - SIEM logging + quarantine"""
        
        # Gather detailed metadata
        actual_type = self.identify_file_type(header)
        file_hash = self.calculate_hash(filepath)
        file_owner = self.get_file_owner(filepath)
        file_size = os.path.getsize(filepath)
        
        metadata = {
            'filepath': filepath,
            'filename': os.path.basename(filepath),
            'claimed_extension': claimed_ext,
            'actual_type': actual_type,
            'file_size_bytes': file_size,
            'file_hash_sha256': file_hash,
            'file_owner': file_owner,
            'magic_number_hex': header[:16].hex(),
            'detection_time': datetime.utcnow().isoformat() + 'Z',
            'hostname': os.uname().nodename
        }
        
        # Log to SIEM
        self.siem.log_event(
            'FILE_EXTENSION_MISMATCH',
            'HIGH',
            metadata
        )
        
        # Quarantine file
        if self.config['quarantine']['enabled']:
            quarantine_path = self.quarantine_file(filepath, metadata)
            if quarantine_path:
                self.siem.log_event(
                    'FILE_QUARANTINED',
                    'INFO',
                    {
                        'original_path': filepath,
                        'quarantine_path': quarantine_path,
                        'file_hash': file_hash
                    }
                )
                print(f"   ✓ Quarantined to: {quarantine_path}")
            else:
                print(f"   ✗ Quarantine failed (file remains at original location)")
        
        # Console output
        print(f"   Extension: .{claimed_ext} | Actual: {actual_type}")
        print(f"   Owner: {file_owner}")
        print(f"   SHA256: {file_hash[:16]}..." if file_hash else "   SHA256: N/A")
    
    def monitor(self):
        """Start monitoring file system events"""
        self.siem.log_event('MONITORING_START', 'INFO', {
            'watched_paths': self.watch_paths,
            'excluded_paths': self.excluded_paths
        })
        
        print(f"🔍 Starting file validator monitoring...")
        print(f"📁 Watching paths: {self.watch_paths}")
        print(f"🚫 Excluded paths: {self.excluded_paths}")
        print(f"📊 Quarantine: {'Enabled' if self.config['quarantine']['enabled'] else 'Disabled'}")
        print()
        
        i = inotify.adapters.InotifyTrees(self.watch_paths)
        
        for event in i.event_gen(yield_nones=False):
            (_, type_names, path, filename) = event
            
            # Monitor only file creation and modification
            if 'IN_CLOSE_WRITE' in type_names or 'IN_MOVED_TO' in type_names:
                filepath = os.path.join(path, filename)
                self.check_magic_mismatch(filepath)

# ============================================================================
# CONFIGURATION LOADER
# ============================================================================

def load_config():
    """Load configuration from file or use defaults"""
    config_path = '/etc/file-validator/config.yaml'
    
    # Use defaults if config doesn't exist
    if not os.path.exists(config_path):
        return DEFAULT_CONFIG
    
    # Load existing config
    try:
        with open(config_path, 'r') as f:
            user_config = yaml.safe_load(f)
            # Merge with defaults
            config = DEFAULT_CONFIG.copy()
            config.update(user_config)
            return config
    except Exception as e:
        print(f"Warning: Could not load config file: {e}")
        return DEFAULT_CONFIG

def save_default_config():
    """Save default config for user to customize"""
    config_path = '/etc/file-validator/config.yaml'
    
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False)
        print(f"✓ Created default config: {config_path}")
    except PermissionError:
        print(f"Note: Run as root to create config file at {config_path}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 70)
    print("     File Validator - Linux Edition v1.1 (Production)")
    print("     Real-time Detection | Quarantine | SIEM Logging")
    print("=" * 70)
    print()
    
    # Check if running as root
    if os.geteuid() != 0:
        print("⚠️  WARNING: Not running as root")
        print("   Some features may not work (quarantine, system-wide monitoring)")
        print()
    
    # Load configuration
    config = load_config()
    
    # Save default config if doesn't exist
    if not os.path.exists('/etc/file-validator/config.yaml'):
        save_default_config()
    
    # Setup SIEM logger
    siem_logger = SIEMLogger(
        config['logging']['log_file'],
        config['logging']['siem_format'],
        config['logging']['console_output']
    )
    
    # Display configuration
    print(f"📄 Log file: {config['logging']['log_file']}")
    print(f"📁 Quarantine: {config['quarantine']['path']}")
    print(f"   Enabled: {config['quarantine']['enabled']}")
    print()
    print("Features enabled:")
    print(f"   {'✓' if config['detection']['calculate_hash'] else '✗'} File hashing (SHA256)")
    print(f"   {'✓' if config['detection']['get_file_owner'] else '✗'} User attribution")
    print(f"   {'✓' if config['logging']['siem_format'] else '✗'} SIEM-ready JSON logging")
    print(f"   {'✓' if config['quarantine']['enabled'] else '✗'} Automatic quarantine")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 70)
    print()
    
    # Start validator
    validator = FileValidator(config, siem_logger)
    
    try:
        validator.monitor()
    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print("Stopping file validator...")
        siem_logger.log_event('SYSTEM_STOP', 'INFO', {'reason': 'user_interrupt'})
        sys.exit(0)

if __name__ == '__main__':
    main()