# 🪟 File Validator - Windows Edition v1.1

**Production-ready file extension validation with quarantine and SIEM integration**

## ✨ Features

- ⚡ **Real-time monitoring** using Windows file system events
- 🔒 **Automatic quarantine** of suspicious files
- 📊 **SIEM-ready JSON logging** (Splunk, ELK, QRadar compatible)
- 🔐 **SHA256 file hashing** for malware analysis
- 👤 **User attribution** (track who created the file)
- ⚙️ **YAML configuration** for easy customization
- 🪶 **Lightweight** (<20MB memory, <1% CPU)

## 🚀 Quick Install
```cmd
git clone https://github.com/AnasRm01/file-validator.git
cd file-validator
install-windows.bat
```

## 📋 Requirements

- Windows 7/8/10/11 or Windows Server 2012+
- Python 3.6 or newer
- 20MB disk space

## 🎯 Usage

### Start Monitoring
```cmd
python file_validator_windows.py
```

### Configuration

Edit: `C:\Users\[YourUser]\file-validator-config.yaml`
```yaml
monitoring:
  auto_detect_paths: true  # Monitor Downloads, Desktop, Documents
  custom_paths:
    - C:\Temp
    - C:\inetpub\uploads  # Web server uploads

quarantine:
  enabled: true
  path: C:\Users\[User]\file-validator-quarantine
  keep_original: false  # true = copy, false = move

logging:
  siem_format: true  # JSON format for SIEM
  log_level: INFO

detection:
  calculate_hash: true  # SHA256 hashing
  get_file_owner: true  # Track user
  max_file_size_mb: 100  # Skip huge files
```

## 📊 SIEM Integration

### Log Format (JSON)
```json
{
  "timestamp": "2026-02-08T10:30:45Z",
  "event_type": "FILE_EXTENSION_MISMATCH",
  "severity": "HIGH",
  "source": "file-validator-windows",
  "hostname": "WORKSTATION01",
  "username": "jsmith",
  "data": {
    "filepath": "C:\\Users\\jsmith\\Downloads\\invoice.pdf",
    "claimed_extension": "pdf",
    "actual_type": "exe",
    "file_hash_sha256": "abc123...",
    "file_owner": "DOMAIN\\jsmith",
    "file_size_bytes": 524288
  }
}
```

### Splunk Integration
```conf
[monitor://C:\Users\*\file-validator.log]
sourcetype = json
index = security
```

### ELK Stack (Filebeat)
```yaml
filebeat.inputs:
- type: log
  paths:
    - C:\Users\*\file-validator.log
  json.keys_under_root: true
  json.add_error_key: true
```

### QRadar

Import as JSON log source, map fields:
- `timestamp` → Event Time
- `severity` → Severity
- `data.filepath` → File Path

## 🧪 Testing
```cmd
# Create test file (PDF disguised as JPG)
cd %USERPROFILE%\Downloads
echo %PDF-1.4 fake content > malware.jpg

# Check detection
notepad %USERPROFILE%\file-validator.log

# Check quarantine
dir %USERPROFILE%\file-validator-quarantine
```

**Expected result:**
- File moved to quarantine
- JSON log entry created
- Console alert displayed

## 🗂️ Quarantine Structure
```
file-validator-quarantine/
├── 20260208_103045_123456/
│   ├── malware.jpg           # The suspicious file
│   └── metadata.json         # Complete forensics data
└── 20260208_110230_789012/
    ├── invoice.pdf
    └── metadata.json
```

**Metadata includes:**
- Original file path
- SHA256 hash
- File owner (Windows username)
- Detection timestamp
- Magic number (hex)
- File size

## 🔧 Run as Windows Service

### Method 1: NSSM (Recommended)
```cmd
# Download NSSM: https://nssm.cc/download
nssm install FileValidator ^
  "C:\Python39\python.exe" ^
  "C:\path\to\file_validator_windows.py"

nssm start FileValidator
```

### Method 2: Task Scheduler

1. Open Task Scheduler
2. Create Task → "File Validator"
3. Trigger: At startup
4. Action: `python.exe C:\path\to\file_validator_windows.py`
5. Run with highest privileges

## 📈 Supported File Types

PDF, PNG, JPG, GIF, ZIP, RAR, 7Z, ISO, TAR, GZ, BZ2, EXE, DLL, DOC, DOCX, XLSX, PPTX

## 🔍 Use Cases

### Corporate Environment
- Monitor employee Downloads folders
- Protect shared network drives
- Detect ransomware before execution

### Web Servers
- Validate uploaded files
- Prevent malicious uploads
- Compliance logging (PCI-DSS, HIPAA)

### Incident Response
- Forensic analysis of suspicious files
- Track file origins (user attribution)
- Hash database for malware correlation

## 🆘 Troubleshooting

**Dependencies failed:**
```cmd
pip install --upgrade pip
pip install watchdog pyyaml
```

**Permission errors:**
- Run Command Prompt as Administrator

**pywin32 failed (optional):**
- Tool still works without it
- User attribution will show current user only

## 📝 Logs Location

- **Log file:** `C:\Users\[User]\file-validator.log`
- **Config:** `C:\Users\[User]\file-validator-config.yaml`
- **Quarantine:** `C:\Users\[User]\file-validator-quarantine\`

## 🔗 Links

- **Linux Version:** See main README.md
- **GitHub:** https://github.com/AnasRm01/file-validator
- **Report Issues:** https://github.com/AnasRm01/file-validator/issues

## 📄 License

MIT License - Free for personal and commercial use
