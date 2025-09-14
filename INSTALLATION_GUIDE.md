# 📦 WebPilot Installation Guide

Complete guide for installing WebPilot with MCP support across different platforms and use cases.

## 🚀 Quick Install

```bash
pip install claude-webpilot
```

## 📋 Prerequisites

### System Requirements
- Python 3.9 or higher
- Operating System: Linux, macOS, or Windows
- Browser: Firefox, Chrome, or Chromium

### Browser Drivers
WebPilot requires browser drivers to control web browsers:

#### Firefox (Recommended)
```bash
# Linux/macOS
wget https://github.com/mozilla/geckodriver/releases/latest/download/geckodriver-v0.34.0-linux64.tar.gz
tar -xvzf geckodriver-v0.34.0-linux64.tar.gz
sudo mv geckodriver /usr/local/bin/

# Windows
# Download from: https://github.com/mozilla/geckodriver/releases
# Add to PATH
```

#### Chrome
```bash
# Linux
sudo apt-get install chromium-chromedriver

# macOS
brew install chromedriver

# Windows
# Download from: https://chromedriver.chromium.org/
# Add to PATH
```

## 🤖 Claude Desktop Integration

### Step 1: Install WebPilot
```bash
pip install claude-webpilot
```

### Step 2: Configure MCP

#### macOS/Linux
Edit `~/.config/claude/mcp_servers.json`:
```json
{
  "mcpServers": {
    "webpilot": {
      "command": "python",
      "args": ["-m", "webpilot.mcp.run_server"],
      "env": {
        "PYTHONPATH": "/path/to/site-packages"
      }
    }
  }
}
```

#### Windows
Edit `%APPDATA%\claude\mcp_servers.json`:
```json
{
  "mcpServers": {
    "webpilot": {
      "command": "python",
      "args": ["-m", "webpilot.mcp.run_server"],
      "env": {
        "PYTHONPATH": "C:\\Python39\\Lib\\site-packages"
      }
    }
  }
}
```

### Step 3: Find Your Python Path
```bash
# Find where WebPilot is installed
python -c "import webpilot; print(webpilot.__file__)"

# Get site-packages directory
python -c "import site; print(site.getsitepackages()[0])"
```

### Step 4: Restart Claude Desktop
Close and reopen Claude Desktop to load the MCP configuration.

### Step 5: Test Integration
Ask Claude: "Can you use WebPilot to navigate to google.com?"

## 🐳 Docker Installation

### Using Pre-built Image
```bash
docker pull ghcr.io/luminous-dynamics/webpilot:latest
docker run -it webpilot
```

### Building from Source
```dockerfile
FROM python:3.9-slim

# Install browsers and drivers
RUN apt-get update && apt-get install -y \
    firefox-esr \
    chromium \
    chromium-driver \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install geckodriver
RUN wget -q https://github.com/mozilla/geckodriver/releases/download/v0.34.0/geckodriver-v0.34.0-linux64.tar.gz \
    && tar -xzf geckodriver-v0.34.0-linux64.tar.gz \
    && mv geckodriver /usr/local/bin/ \
    && rm geckodriver-v0.34.0-linux64.tar.gz

# Install WebPilot
RUN pip install claude-webpilot

# Run MCP server
CMD ["python", "-m", "webpilot.mcp.run_server"]
```

## 🔧 Development Installation

### Clone Repository
```bash
git clone https://github.com/Luminous-Dynamics/webpilot.git
cd webpilot
```

### Install with Poetry
```bash
poetry install
poetry run python -m webpilot.mcp.run_server
```

### Install with pip (editable)
```bash
pip install -e .
```

## 🖥️ Platform-Specific Instructions

### Ubuntu/Debian
```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip firefox chromium-browser

# Install WebPilot
pip3 install claude-webpilot

# Install geckodriver
wget https://github.com/mozilla/geckodriver/releases/latest/download/geckodriver-v0.34.0-linux64.tar.gz
tar -xvzf geckodriver-v0.34.0-linux64.tar.gz
sudo mv geckodriver /usr/local/bin/
```

### macOS
```bash
# Install Homebrew if not installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install browsers and drivers
brew install --cask firefox
brew install geckodriver
brew install chromedriver

# Install WebPilot
pip install claude-webpilot
```

### Windows
```powershell
# Install Python from python.org

# Install WebPilot
pip install claude-webpilot

# Download and install browser drivers:
# Firefox: https://github.com/mozilla/geckodriver/releases
# Chrome: https://chromedriver.chromium.org/

# Add driver executables to PATH
```

### NixOS
```nix
# In configuration.nix or shell.nix
{ pkgs, ... }:

{
  environment.systemPackages = with pkgs; [
    python39
    python39Packages.pip
    firefox
    geckodriver
    chromium
    chromedriver
  ];
  
  # Install WebPilot
  # pip install claude-webpilot
}
```

## 🧪 Verify Installation

### Test Basic Import
```python
python -c "import webpilot; print(webpilot.__version__)"
```

### Test MCP Server
```bash
python -m webpilot.mcp.run_server --test
```

### Test Browser Automation
```python
from webpilot import WebPilot

with WebPilot() as pilot:
    pilot.start("https://example.com")
    pilot.screenshot("test.png")
    print("Success! WebPilot is working.")
```

## 🐛 Troubleshooting

### Import Error: No module named 'webpilot'
```bash
# Ensure WebPilot is installed
pip install claude-webpilot

# Check Python path
python -c "import sys; print(sys.path)"
```

### Browser Driver Not Found
```bash
# Check if driver is in PATH
which geckodriver  # or chromedriver

# If not found, add to PATH
export PATH=$PATH:/path/to/driver
```

### MCP Server Not Starting
```bash
# Check logs
tail -f /tmp/webpilot_mcp.log

# Test server directly
python -m webpilot.mcp.run_server --debug
```

### Permission Denied
```bash
# Make driver executable
chmod +x /path/to/geckodriver
```

### Claude Can't Find WebPilot
1. Verify MCP configuration file location
2. Check PYTHONPATH in configuration
3. Restart Claude Desktop
4. Check Claude's developer console for errors

## 📚 Additional Resources

- [MCP Integration Guide](docs/mcp_integration.md)
- [API Documentation](https://luminous-dynamics.github.io/webpilot/)
- [Examples](examples/)
- [GitHub Issues](https://github.com/Luminous-Dynamics/webpilot/issues)

## 🆘 Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Search [existing issues](https://github.com/Luminous-Dynamics/webpilot/issues)
3. Create a new issue with:
   - Your OS and Python version
   - Complete error message
   - Steps to reproduce

## 🎉 Next Steps

Once installed, you can:
- Ask Claude to automate web tasks
- Run the [quick start examples](examples/mcp_quickstart.py)
- Read the [MCP documentation](docs/mcp_integration.md)
- Join our community discussions

Happy automating! 🚀