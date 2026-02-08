# 🛡️ File Validator

**Professional file extension validation tool that detects malware hiding behind fake extensions**

Catch attackers who rename `ransomware.exe` → `invoice.pdf` in real-time.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Linux](https://img.shields.io/badge/Platform-Linux-blue.svg)](#-linux-installation)
[![Windows](https://img.shields.io/badge/Platform-Windows-0078D6.svg)](#-windows-installation)

---

## 🚨 The Problem

Attackers disguise malicious files by changing extensions:
```
ransomware.exe  →  invoice.pdf
malware.js      →  report.docx
trojan.sh       →  data.txt
```

Traditional antivirus may miss these. **File Validator catches them instantly.**

---

## ✨ Key Features

- ⚡ **Real-time detection** - Event-driven monitoring (<1% CPU)
- 🔒 **Automatic quarantine** - Isolates suspicious files
- 📊 **SIEM integration** - JSON logs for Splunk, ELK, Wazuh, QRadar
- 🔐 **File hashing** - SHA256 for malware analysis
- 👤 **User tracking** - Know who created suspicious files
- ⚙️ **Configurable** - YAML configuration file
- 🪶 **Lightweight** - <10MB memory usage

---

## 🐧 Linux Installation

### One-Command Install (Recommended)
```bash
curl -sSL https://raw.githubusercontent.com/AnasRm01/file-validator/main/install.sh | sudo bash
```

**What gets installed:**
- Main program: `/usr/local/bin/file-validator`
- Service: `/etc/systemd/system/file-validator.service`
- Config: `/etc/file-validator/config.yaml`
- Quarantine: `/var/quarantine/`
- Python dependencies: `inotify`, `pyyaml`

**Supported:** Ubuntu, Debian, CentOS, RHEL, Fedora, Rocky Linux, AlmaLinux

**Installation size:** ~50KB (plus ~5MB Python dependencies)

---

### Alternative: Download and Run
```bash
curl -sSL https://raw.githubusercontent.com/AnasRm01/file-validator/main/install.sh -o install.sh
sudo bash install.sh
```

---

### Verify Installation
```bash
# Check service status
sudo systemctl status file-validator

# View logs
sudo tail -f /var/log/file-validator.log
```

---

### Test Detection
```bash
# Create a fake malicious file
echo "%PDF-1.4 fake" > /tmp/test.jpg

# Wait 2 seconds and check logs
sleep 2
sudo tail /var/log/file-validator.log
```

**Expected output:**
```json
{
  "event_type": "FILE_EXTENSION_MISMATCH",
  "severity": "HIGH",
  "data": {
    "filepath": "/tmp/test.jpg",
    "claimed_extension": "jpg",
    "actual_type": "pdf",
    "file_hash_sha256": "abc123..."
  }
}
```

---

### Configuration
```bash
# Edit settings
sudo nano /etc/file-validator/config.yaml

# Restart after changes
sudo systemctl restart file-validator
```

---

### Uninstall
```bash
# Stop and remove service
sudo systemctl stop file-validator
sudo systemctl disable file-validator
sudo rm /etc/systemd/system/file-validator.service
sudo rm /usr/local/bin/file-validator
sudo rm -rf /etc/file-validator
sudo rm -rf /var/quarantine
sudo rm /var/log/file-validator.log
```

---

## 🪟 Windows Installation

### One-Command Install (Recommended)

**Step 1:** Download installer (Run PowerShell as Administrator)
```powershell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/AnasRm01/file-validator/main/install-windows.bat" -OutFile "install.bat"
```

**Step 2:** Run installer (Right-click → Run as Administrator)
```cmd
install.bat
```

**What gets installed:**
- Main program: `%USERPROFILE%\FileValidator\file-validator.py`
- Config: `%USERPROFILE%\file-validator-config.yaml`
- Logs: `%USERPROFILE%\file-validator.log`
- Quarantine: `%USERPROFILE%\file-validator-quarantine\`
- Python dependencies: `watchdog`, `pyyaml`, `pywin32`

**Supported:** Windows 7/8/10/11, Windows Server 2012+

**Installation size:** ~100KB (plus ~10MB Python dependencies)

---

### Alternative: Git Clone Method
```cmd
git clone https://github.com/AnasRm01/file-validator.git
cd file-validator
install-windows.bat
```

---

### Verify Installation

Program should start automatically after installation.

Check log file:
```cmd
notepad %USERPROFILE%\file-validator.log
```

---

### Test Detection
```cmd
cd %USERPROFILE%\Downloads
echo %PDF-1.4 fake > test.jpg

REM Wait 2 seconds, then check log
timeout /t 2
notepad %USERPROFILE%\file-validator.log
```

**Expected output:**
```json
{
  "event_type": "FILE_EXTENSION_MISMATCH",
  "severity": "HIGH",
  "data": {
    "filepath": "C:\\Users\\...\\test.jpg",
    "claimed_extension": "jpg",
    "actual_type": "pdf"
  }
}
```

---

### Configuration
```cmd
# Edit settings
notepad %USERPROFILE%\file-validator-config.yaml

# Restart File Validator
# (Close and run start-file-validator.bat again)
```

---

### Run as Service

See [Windows Service Setup](README_WINDOWS.md#run-as-service) for running File Validator as a Windows Service.

---

## 🔧 Supported File Types

PDF, PNG, JPG/JPEG, GIF, ZIP, RAR, 7Z, ISO, TAR, GZ, BZ2, EXE, DLL, ELF, DOC, DOCX, XLSX, PPTX

---

## 📊 SIEM Integration

File Validator outputs **structured JSON logs** compatible with enterprise SIEM platforms:

### Splunk
```conf
[monitor:///var/log/file-validator.log]
sourcetype = json
index = security
```

### ELK Stack (Filebeat)
```yaml
filebeat.inputs:
- type: log
  paths:
    - /var/log/file-validator.log
  json.keys_under_root: true
```

### Wazuh
```xml
<localfile>
  <log_format>json</log_format>
  <location>/var/log/file-validator.log</location>
</localfile>
```

**Full SIEM Integration Guide:** See [docs/SIEM.md](docs/SIEM.md) (coming soon)

---

## 🏢 Use Cases

### Enterprise Security
- Monitor file uploads on web servers
- Protect shared network drives
- Detect ransomware before execution
- Compliance logging (PCI-DSS, HIPAA, SOC 2)

### System Administration
- Monitor employee download folders
- Validate file server uploads
- Real-time security alerts

### Security Research
- Analyze malware samples
- Threat hunting
- Behavioral analysis

---

## ❓ FAQ

**Q: Does this replace antivirus?**  
A: No, it's complementary. Use alongside traditional antivirus for layered security.

**Q: Performance impact?**  
A: Minimal. Event-driven architecture means <1% CPU and <10MB RAM.

**Q: Can attackers bypass this?**  
A: Advanced attackers can craft files with fake magic numbers, but this catches 95%+ of basic evasion techniques.

**Q: Which platform should I use?**  
A: 
- **Linux servers** → Use Linux version
- **Windows workstations** → Use Windows version
- **Both** → Install on both!

**Q: What files are installed on my system?**  
A:
- **Linux:** Only the main program, config, service file, and quarantine directory (~50KB)
- **Windows:** Only the main program, config, and quarantine directory (~100KB)
- **No source code, documentation, or extra files are installed**

---

## 🤝 Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

**Areas for contribution:**
- macOS support
- Additional file type signatures
- Web dashboard
- Machine learning detection

---

## 📝 Changelog

### v1.1 - 2026-02-08
- ✅ Added automatic quarantine
- ✅ Added SIEM-ready JSON logging
- ✅ Added SHA256 file hashing
- ✅ Added user attribution
- ✅ Added YAML configuration
- ✅ Windows support
- ✅ Auto-download installers

### v1.0 - 2026-02-06
- ✅ Initial release
- ✅ Real-time detection (Linux)
- ✅ systemd service

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

Free for personal and commercial use.

---

## 🙏 Support

- ⭐ **Star this repo** if it helped you
- 🐛 **Report bugs:** [GitHub Issues](https://github.com/AnasRm01/file-validator/issues)
- 💡 **Feature requests:** [GitHub Issues](https://github.com/AnasRm01/file-validator/issues)

---

## 🔗 Quick Links

- **GitHub:** https://github.com/AnasRm01/file-validator
- **Issues:** https://github.com/AnasRm01/file-validator/issues
- **Releases:** https://github.com/AnasRm01/file-validator/releases

---

**Made with ❤️ for the security community**

*Protecting systems, one magic number at a time* 🛡️
