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

### Quick Install (One Command)
```bash
curl -sSL https://raw.githubusercontent.com/AnasRm01/file-validator/main/install.sh -o install.sh
sudo bash install.sh
```

**Supported:** Ubuntu, Debian, CentOS, RHEL, Fedora, Rocky Linux, AlmaLinux

### Alternative: Clone and Install
```bash
git clone https://github.com/AnasRm01/file-validator.git
cd file-validator
sudo ./install.sh
```

### Verify Installation
```bash
# Check service status
sudo systemctl status file-validator

# View logs
sudo tail -f /var/log/file-validator.log
```

### Test Detection
```bash
# Create a fake malicious file
echo "%PDF-1.4 fake" > /tmp/test.jpg

# Check detection
sudo tail /var/log/file-validator.log
```

### Configuration
```bash
# Edit settings
sudo nano /etc/file-validator/config.yaml
```

### Uninstall
```bash
cd file-validator
sudo ./uninstall.sh
```

**📖 [Linux Full Documentation →](docs/LINUX.md)**

---

## 🪟 Windows Installation

### Quick Install

**Step 1:** Download and extract
```cmd
git clone https://github.com/AnasRm01/file-validator.git
cd file-validator
```

**Step 2:** Run installer
```cmd
install-windows.bat
```

**Supported:** Windows 7/8/10/11, Windows Server 2012+

### Verify Installation
```cmd
# Program should start automatically
# Check log file
notepad %USERPROFILE%\file-validator.log
```

### Test Detection
```cmd
# Create test file
cd %USERPROFILE%\Downloads
echo %PDF-1.4 fake > test.jpg

# Check log
notepad %USERPROFILE%\file-validator.log
```

### Configuration
```cmd
# Edit settings
notepad %USERPROFILE%\file-validator-config.yaml
```

### Run as Service

See [Windows Service Setup](docs/WINDOWS.md#run-as-service)

**📖 [Windows Full Documentation →](docs/WINDOWS.md)**

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

**📖 [SIEM Integration Guide →](docs/SIEM.md)**

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

## 📖 Documentation

- **[Linux Guide](docs/LINUX.md)** - Installation, configuration, troubleshooting
- **[Windows Guide](docs/WINDOWS.md)** - Installation, configuration, service setup
- **[SIEM Integration](docs/SIEM.md)** - Splunk, ELK, Wazuh, QRadar setup
- **[Configuration](docs/CONFIG.md)** - YAML configuration reference
- **[API Reference](docs/API.md)** - Log format and fields

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
