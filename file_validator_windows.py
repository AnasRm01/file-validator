#!/usr/bin/env python3
"""
File Validator - Windows Edition v1.1
Real-time file extension validation with quarantine and SIEM logging
"""

import os
import sys
import json
import logging
import hashlib
import time
import shutil
from pathlib import Path
from datetime import datetime

# Install dependencies if missing
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    import yaml
except ImportError:
    print("Installing required libraries...")
    os.system("pip install watchdog pyyaml")
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    import yaml

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_CONFIG = {
    'monitoring': {
        'auto_detect_paths': True,  # Automatically monitor Downloads, Desktop, Documents
        'custom_paths': [
            'C:\\Temp',
            'C:\\Users\\Public'
        ],
        'excluded_paths': [
            'C:\\Windows',
            'C:\\Program Files',
            'C:\\Program Files (x86)',
            'C:\\ProgramData\\Microsoft',
            'C:\\$Recycle.Bin'
        ]
    },
    'quarantine': {
        'enabled': True,
        'path': None,  # Will default to C:\Users\[USER]\file-validator-quarantine
        'keep_original': False  # If True, copy instead of move
    },
    'logging': {
        'log_file': None,  # Will default to user profile
        'log_level': 'INFO',
        'siem_format': True,  # Use JSON format for SIEM
        'console_output': True
    },
    'detection': {
        'calculate_hash': True,
        'get_file_owner': True,
        'max_file_size_mb': 100  # Skip files larger than this
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
    'dll': [b'MZ'],
    'doc': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],
    'docx': [b'PK\x03\x04'],
    'xlsx': [b'PK\x03\x04'],
    'pptx': [b'PK\x03\x04'],
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
    """Formats logs as JSON for SIEM ingestion"""
    
    def __init__(self, log_file, console_output=True):
        self.log_file = log_file
        self.console_output = console_output
        
        # Ensure log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    def log_event(self, event_type, severity, data):
        """Log event in SIEM-compatible JSON format"""
        event = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'event_type': event_type,
            'severity': severity,
            'source': 'file-validator-windows',
            'version': '1.1',
            'hostname': os.getenv('COMPUTERNAME', 'unknown'),
            'username': os.getenv('USERNAME', 'unknown'),
            'data': data
        }
        
        # Write to log file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event) + '\n')
        
        # Console output
        if self.console_output:
            if severity in ['HIGH', 'CRITICAL']:
                print(f"🚨 {event_type}: {data.get('filepath', 'N/A')}")
            else:
                print(f"ℹ️  {event_type}")

# ============================================================================
# FILE VALIDATOR WITH QUARANTINE
# ============================================================================

class FileValidator(FileSystemEventHandler):
    """Enhanced file validator with quarantine and SIEM logging"""
    
    def __init__(self, config, siem_logger):
        self.config = config
        self.siem = siem_logger
        self.excluded_paths = config['monitoring']['excluded_paths']
        self.recently_checked = {}
        self.quarantine_dir = config['quarantine']['path']
        
        # Create quarantine directory
        if config['quarantine']['enabled']:
            os.makedirs(self.quarantine_dir, exist_ok=True)
            self.siem.log_event('SYSTEM_START', 'INFO', {
                'quarantine_enabled': True,
                'quarantine_path': self.quarantine_dir
            })
    
    def should_skip_path(self, filepath):
        """Check if path should be excluded"""
        filepath_upper = filepath.upper()
        for excluded in self.excluded_paths:
            if filepath_upper.startswith(excluded.upper()):
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
        except Exception as e:
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
        """Get file owner (Windows username)"""
        if not self.config['detection']['get_file_owner']:
            return 'unknown'
        
        try:
            import win32security
            import win32api
            
            sd = win32security.GetFileSecurity(
                filepath, win32security.OWNER_SECURITY_INFORMATION
            )
            owner_sid = sd.GetSecurityDescriptorOwner()
            name, domain, type = win32security.LookupAccountSid(None, owner_sid)
            return f"{domain}\\{name}"
        except:
            # Fallback if win32 not available
            return os.getenv('USERNAME', 'unknown')
    
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
            
            # Save metadata
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
        
        # Avoid duplicate checks
        current_time = time.time()
        if filepath in self.recently_checked:
            if current_time - self.recently_checked[filepath] < 5:
                return False
        self.recently_checked[filepath] = current_time
        
        # Get file extension
        ext = Path(filepath).suffix.lower().lstrip('.')
        if not ext or ext not in MAGIC_SIGNATURES:
            return False
        
        # Read file header
        header = self.read_file_header(filepath, 32)
        if not header:
            return False
        
        # Check if magic number matches extension
        expected_signatures = MAGIC_SIGNATURES[ext]
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
            'hostname': os.getenv('COMPUTERNAME', 'unknown'),
            'username': os.getenv('USERNAME', 'unknown')
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
        
        # Console output for admin
        print(f"   Extension: .{claimed_ext} | Actual: {actual_type}")
        print(f"   Owner: {file_owner}")
        print(f"   SHA256: {file_hash[:16]}..." if file_hash else "   SHA256: N/A")
    
    def on_created(self, event):
        """Called when a file is created"""
        if not event.is_directory:
            time.sleep(0.1)  # Small delay
            self.check_magic_mismatch(event.src_path)
    
    def on_modified(self, event):
        """Called when a file is modified"""
        if not event.is_directory:
            self.check_magic_mismatch(event.src_path)

# ============================================================================
# CONFIGURATION LOADER
# ============================================================================

def load_config():
    """Load configuration from file or use defaults"""
    config_path = os.path.join(
        os.getenv('USERPROFILE', 'C:\\Users\\Public'),
        'file-validator-config.yaml'
    )
    
    # Use defaults if config doesn't exist
    if not os.path.exists(config_path):
        config = DEFAULT_CONFIG.copy()
        
        # Set default paths based on user profile
        user_profile = os.getenv('USERPROFILE', 'C:\\Users\\Public')
        config['quarantine']['path'] = os.path.join(
            user_profile, 'file-validator-quarantine'
        )
        config['logging']['log_file'] = os.path.join(
            user_profile, 'file-validator.log'
        )
        
        # Save default config for user to customize
        try:
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            print(f"✓ Created default config: {config_path}")
        except:
            pass
        
        return config
    
    # Load existing config
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except:
        return DEFAULT_CONFIG

# ============================================================================
# MAIN
# ============================================================================

def print_banner():
    """Print startup banner"""
    print("=" * 70)
    print("     File Validator - Windows Edition v1.1 (Production)")
    print("     Real-time Detection | Quarantine | SIEM Logging")
    print("=" * 70)
    print()

def get_watch_paths(config):
    """Determine which paths to monitor"""
    paths = []
    
    # Auto-detect user folders
    if config['monitoring']['auto_detect_paths']:
        user_profile = os.getenv('USERPROFILE', 'C:\\Users\\Public')
        auto_paths = [
            os.path.join(user_profile, 'Downloads'),
            os.path.join(user_profile, 'Desktop'),
            os.path.join(user_profile, 'Documents'),
        ]
        paths.extend([p for p in auto_paths if os.path.exists(p)])
    
    # Add custom paths
    paths.extend([p for p in config['monitoring']['custom_paths'] if os.path.exists(p)])
    
    return list(set(paths))  # Remove duplicates

def main():
    print_banner()
    
    # Load configuration
    config = load_config()
    
    # Setup SIEM logger
    siem_logger = SIEMLogger(
        config['logging']['log_file'],
        config['logging']['console_output']
    )
    
    # Get paths to monitor
    watch_paths = get_watch_paths(config)
    
    if not watch_paths:
        print("ERROR: No valid paths to monitor!")
        print("Please check configuration file")
        sys.exit(1)
    
    # Display configuration
    print(f"📄 Log file: {config['logging']['log_file']}")
    print(f"📁 Quarantine: {config['quarantine']['path']}")
    print(f"   Enabled: {config['quarantine']['enabled']}")
    print(f"🔍 Monitoring {len(watch_paths)} location(s):")
    for path in watch_paths:
        print(f"   ✓ {path}")
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
    
    # Log startup
    siem_logger.log_event('SYSTEM_START', 'INFO', {
        'monitored_paths': watch_paths,
        'config': config
    })
    
    # Start monitoring
    event_handler = FileValidator(config, siem_logger)
    observer = Observer()
    
    for path in watch_paths:
        try:
            observer.schedule(event_handler, path, recursive=True)
            print(f"✓ Now monitoring: {path}")
        except Exception as e:
            print(f"✗ Failed to monitor {path}: {e}")
    
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print("Stopping File Validator...")
        siem_logger.log_event('SYSTEM_STOP', 'INFO', {'reason': 'user_interrupt'})
        observer.stop()
    
    observer.join()
    print("✓ File Validator stopped")
    print(f"Check logs: {config['logging']['log_file']}")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        print(f"\nFATAL ERROR: {e}")
        print("Please report this issue on GitHub")
        sys.exit(1)
