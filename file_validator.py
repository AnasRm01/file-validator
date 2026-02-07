#!/usr/bin/env python3
"""
File Magic Number Validator - Lightweight Background Monitor
"""

import os
import sys
import logging
from pathlib import Path

# Try to import inotify, install if missing
try:
    import inotify.adapters
except ImportError:
    print("Installing inotify...")
    os.system("pip3 install inotify --break-system-packages")
    import inotify.adapters

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/file-validator.log'),
        logging.StreamHandler()
    ]
)

# Common extension to magic number mappings
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
    'sh': [b'#!/bin/bash', b'#!/bin/sh'],
    'py': [b'#!/usr/bin/python', b'#!/usr/bin/env python'],
    'txt': [],  # Text files - skip magic check
}

class FileValidator:
    def __init__(self, watch_paths, excluded_paths=None):
        self.watch_paths = watch_paths
        self.excluded_paths = excluded_paths or ['/proc', '/sys', '/dev']
        
    def should_skip_path(self, filepath):
        """Check if path should be excluded from scanning"""
        for excluded in self.excluded_paths:
            if filepath.startswith(excluded):
                return True
        return False
    
    def read_file_header(self, filepath, bytes_count=16):
        """Read first bytes of file safely"""
        try:
            with open(filepath, 'rb') as f:
                return f.read(bytes_count)
        except (PermissionError, FileNotFoundError, OSError, IsADirectoryError) as e:
            logging.debug(f"Cannot read {filepath}: {e}")
            return None
    
    def check_magic_mismatch(self, filepath):
        """Check if file extension matches its magic number"""
        if self.should_skip_path(filepath):
            return False
        
        if not os.path.isfile(filepath):
            return False
        
        # Get file extension
        ext = Path(filepath).suffix.lower().lstrip('.')
        if not ext or ext not in MAGIC_SIGNATURES:
            return False  # Unknown extension, skip
        
        # Skip text files
        if ext == 'txt':
            return False
        
        # Read file header
        header = self.read_file_header(filepath)
        if not header:
            return False
        
        # Check if magic number matches extension
        expected_signatures = MAGIC_SIGNATURES[ext]
        if not expected_signatures:  # Empty list means skip check
            return False
            
        matches = any(header.startswith(sig) for sig in expected_signatures)
        
        if not matches:
            return True  # Mismatch detected
        
        return False
    
    def handle_suspicious_file(self, filepath):
        """Handle detected mismatch"""
        logging.warning(f"🚨 MISMATCH DETECTED: {filepath}")
        
        # Read header to show in log
        header = self.read_file_header(filepath, 32)
        if header:
            hex_header = ' '.join(f'{b:02x}' for b in header[:16])
            logging.warning(f"  File header: {hex_header}")
            logging.warning(f"  Extension: .{Path(filepath).suffix}")
        
        # Optional: uncomment to quarantine
        # self.quarantine_file(filepath)
    
    def quarantine_file(self, filepath):
        """Move suspicious file to quarantine directory"""
        quarantine_dir = "/var/quarantine"
        os.makedirs(quarantine_dir, exist_ok=True)
        
        try:
            import shutil
            dest = os.path.join(quarantine_dir, os.path.basename(filepath))
            shutil.move(filepath, dest)
            logging.info(f"  ✓ Quarantined to: {dest}")
        except Exception as e:
            logging.error(f"  ✗ Failed to quarantine: {e}")
    
    def monitor(self):
        """Start monitoring file system events"""
        logging.info(f"🔍 Starting file validator monitoring...")
        logging.info(f"📁 Watching paths: {self.watch_paths}")
        
        i = inotify.adapters.InotifyTrees(self.watch_paths)
        
        for event in i.event_gen(yield_nones=False):
            (_, type_names, path, filename) = event
            
            # Monitor only file creation and modification
            if 'IN_CLOSE_WRITE' in type_names or 'IN_MOVED_TO' in type_names:
                filepath = os.path.join(path, filename)
                
                if self.check_magic_mismatch(filepath):
                    self.handle_suspicious_file(filepath)

def main():
    # Paths to monitor (adjust as needed)
    watch_paths = [
        '/home',
        '/tmp',
    ]
    
    # Paths to exclude
    excluded_paths = [
        '/proc',
        '/sys',
        '/dev',
        '/run',
        '/snap'
    ]
    
    validator = FileValidator(watch_paths, excluded_paths)
    
    try:
        validator.monitor()
    except KeyboardInterrupt:
        logging.info("Stopping file validator...")
        sys.exit(0)

if __name__ == '__main__':
    main()
