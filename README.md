# 🛡️ File Validator

Lightweight security tool that detects files with mismatched extensions and magic numbers.

## The Problem

Attackers disguise malicious files:
- `ransomware.exe` → `invoice.pdf`
- `malware.js` → `report.docx`

File Validator catches them instantly.

## Features

- ⚡ Real-time detection using inotify
- 🪶 Lightweight (<10MB memory)
- 📊 SIEM-ready logging
- 🚀 Runs as systemd service

## Quick Install
```bash
git clone https://github.com/YOUR-USERNAME/file-validator.git
cd file-validator
sudo ./install.sh
```

## Usage
```bash
# Check status
sudo systemctl status file-validator

# View logs
sudo tail -f /var/log/file-validator.log

# Test it
echo "%PDF" > test.jpg  # Will trigger detection
```

## Uninstall
```bash
sudo ./uninstall.sh
```

## License

MIT License - Free to use
