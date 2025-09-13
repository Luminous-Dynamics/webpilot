#!/usr/bin/env bash

# WebPilot Dependency Auto-Installer
# Automatically detects system and installs required dependencies

set -e

echo "🚁 WebPilot Dependency Installer"
echo "================================="
echo ""

# Detect operating system
detect_os() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$ID
        VER=$VERSION_ID
    elif [ -f /etc/nixos ]; then
        OS="nixos"
    elif command -v sw_vers &> /dev/null; then
        OS="macos"
    else
        OS="unknown"
    fi
    echo "Detected OS: $OS"
}

# Check if running on NixOS
is_nixos() {
    [ -f /etc/NIXOS ] || [ -d /nix ]
}

# Check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Install for NixOS
install_nixos() {
    echo "📦 Installing for NixOS..."
    
    # Create a temporary shell.nix
    cat > /tmp/webpilot-shell.nix << 'EOF'
{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    # Python and packages
    python3
    python3Packages.selenium
    python3Packages.pillow
    python3Packages.opencv4
    python3Packages.beautifulsoup4
    python3Packages.aiohttp
    python3Packages.requests
    python3Packages.numpy
    
    # Browser drivers
    geckodriver
    chromedriver
    
    # Browsers
    firefox
    chromium
    
    # System tools
    xdotool
    imagemagick
    tesseract
    scrot
    curl
    
    # OCR
    tesseract
  ];
}
EOF
    
    echo "Starting NixOS shell with dependencies..."
    echo "Run: nix-shell /tmp/webpilot-shell.nix"
    echo ""
    echo "Or install globally with:"
    echo "  nix-env -iA nixpkgs.firefox nixpkgs.xdotool nixpkgs.imagemagick"
}

# Install for Ubuntu/Debian
install_debian() {
    echo "📦 Installing for Debian/Ubuntu..."
    
    # Update package list
    sudo apt update
    
    # Install system packages
    sudo apt install -y \
        firefox \
        chromium-browser \
        xdotool \
        imagemagick \
        scrot \
        curl \
        tesseract-ocr \
        python3-pip
    
    # Install Python packages
    pip3 install --user \
        selenium \
        webdriver-manager \
        pillow \
        pytesseract \
        opencv-python \
        beautifulsoup4 \
        aiohttp \
        requests
    
    # Download geckodriver
    install_geckodriver_linux
}

# Install for Fedora/RHEL
install_fedora() {
    echo "📦 Installing for Fedora/RHEL..."
    
    sudo dnf install -y \
        firefox \
        chromium \
        xdotool \
        ImageMagick \
        scrot \
        curl \
        tesseract \
        python3-pip
    
    # Install Python packages
    pip3 install --user \
        selenium \
        webdriver-manager \
        pillow \
        pytesseract \
        opencv-python \
        beautifulsoup4 \
        aiohttp
}

# Install for macOS
install_macos() {
    echo "📦 Installing for macOS..."
    
    # Check if Homebrew is installed
    if ! command_exists brew; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Install packages
    brew install \
        firefox \
        imagemagick \
        tesseract \
        geckodriver \
        chromedriver
    
    # Install Python packages
    pip3 install --user \
        selenium \
        webdriver-manager \
        pillow \
        pytesseract \
        opencv-python \
        beautifulsoup4 \
        aiohttp
}

# Install geckodriver for Linux
install_geckodriver_linux() {
    echo "Installing geckodriver..."
    
    # Get latest version
    GECKO_VERSION=$(curl -s https://api.github.com/repos/mozilla/geckodriver/releases/latest | grep -oP '"tag_name": "\K[^"]+')
    
    # Download and install
    wget -q "https://github.com/mozilla/geckodriver/releases/download/${GECKO_VERSION}/geckodriver-${GECKO_VERSION}-linux64.tar.gz"
    tar -xzf geckodriver-*.tar.gz
    sudo mv geckodriver /usr/local/bin/
    rm geckodriver-*.tar.gz
    
    echo "✅ geckodriver installed"
}

# Install Python packages with pip
install_python_packages() {
    echo "📦 Installing Python packages..."
    
    # Check if pip is available
    if command_exists pip3; then
        pip3 install --user \
            selenium \
            webdriver-manager \
            pillow \
            pytesseract \
            opencv-python \
            beautifulsoup4 \
            aiohttp \
            requests \
            numpy
        echo "✅ Python packages installed"
    else
        echo "❌ pip3 not found. Install Python 3 first."
    fi
}

# Check installed dependencies
check_dependencies() {
    echo ""
    echo "🔍 Checking installed dependencies..."
    echo ""
    
    # Check browsers
    echo "Browsers:"
    check_command "firefox" "Firefox"
    check_command "chromium" "Chromium" || check_command "google-chrome" "Chrome"
    
    echo ""
    echo "System tools:"
    check_command "xdotool" "xdotool"
    check_command "import" "ImageMagick"
    check_command "scrot" "scrot"
    check_command "tesseract" "Tesseract OCR"
    check_command "curl" "curl"
    
    echo ""
    echo "Browser drivers:"
    check_command "geckodriver" "geckodriver"
    check_command "chromedriver" "chromedriver"
    
    echo ""
    echo "Python packages:"
    check_python_package "selenium"
    check_python_package "PIL" "pillow"
    check_python_package "cv2" "opencv-python"
    check_python_package "pytesseract"
    check_python_package "bs4" "beautifulsoup4"
    check_python_package "aiohttp"
}

# Check if command exists and print status
check_command() {
    if command_exists "$1"; then
        echo "  ✅ $2"
    else
        echo "  ❌ $2"
    fi
}

# Check if Python package is installed
check_python_package() {
    local package=$1
    local pip_name=${2:-$1}
    
    if python3 -c "import $package" 2>/dev/null; then
        echo "  ✅ $pip_name"
    else
        echo "  ❌ $pip_name"
    fi
}

# Main installation flow
main() {
    detect_os
    
    echo ""
    echo "Choose installation option:"
    echo "1) Auto-detect and install"
    echo "2) NixOS"
    echo "3) Ubuntu/Debian"
    echo "4) Fedora/RHEL"
    echo "5) macOS"
    echo "6) Python packages only"
    echo "7) Check dependencies only"
    echo ""
    
    read -p "Enter choice [1-7]: " choice
    
    case $choice in
        1)
            if is_nixos; then
                install_nixos
            elif [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
                install_debian
            elif [ "$OS" = "fedora" ] || [ "$OS" = "rhel" ]; then
                install_fedora
            elif [ "$OS" = "macos" ]; then
                install_macos
            else
                echo "❌ Could not detect OS. Please choose manual option."
            fi
            ;;
        2)
            install_nixos
            ;;
        3)
            install_debian
            ;;
        4)
            install_fedora
            ;;
        5)
            install_macos
            ;;
        6)
            install_python_packages
            ;;
        7)
            # Just check
            ;;
        *)
            echo "Invalid choice"
            exit 1
            ;;
    esac
    
    # Always check dependencies at the end
    check_dependencies
    
    echo ""
    echo "✨ Installation complete!"
    echo ""
    echo "To test WebPilot, run:"
    echo "  python3 /srv/luminous-dynamics/claude-webpilot/webpilot_cli.py --help"
}

# Run main function
main