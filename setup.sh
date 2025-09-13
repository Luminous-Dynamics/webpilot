#!/usr/bin/env bash

# WebPilot Setup Script
# Installs and configures WebPilot for easy use

set -e

echo "🚁 WebPilot Setup"
echo "================="
echo ""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Make scripts executable
echo "📝 Making scripts executable..."
chmod +x "$SCRIPT_DIR/webpilot_cli.py"
chmod +x "$SCRIPT_DIR/examples/basic_automation.py"

# Create webpilot command
echo "🔧 Creating webpilot command..."
cat > /tmp/webpilot << EOF
#!/usr/bin/env bash
python3 "$SCRIPT_DIR/webpilot_cli.py" "\$@"
EOF

chmod +x /tmp/webpilot

# Try to install globally (may need sudo)
if [ -w /usr/local/bin ]; then
    cp /tmp/webpilot /usr/local/bin/
    echo "✅ Installed webpilot to /usr/local/bin/"
elif [ -w "$HOME/.local/bin" ]; then
    mkdir -p "$HOME/.local/bin"
    cp /tmp/webpilot "$HOME/.local/bin/"
    echo "✅ Installed webpilot to ~/.local/bin/"
    echo "   Make sure ~/.local/bin is in your PATH"
else
    echo "⚠️  Could not install globally. Add this alias to your shell config:"
    echo "   alias webpilot='python3 $SCRIPT_DIR/webpilot_cli.py'"
fi

# Check dependencies
echo ""
echo "🔍 Checking dependencies..."

check_command() {
    if command -v "$1" &> /dev/null; then
        echo "  ✅ $1: Found"
        return 0
    else
        echo "  ❌ $1: Not found"
        return 1
    fi
}

echo "Required:"
check_command python3 || echo "     Install: nix-shell -p python3"
check_command firefox || check_command chromium || check_command google-chrome || \
    echo "     Install: nix-shell -p firefox"

echo ""
echo "Optional (for full features):"
check_command xdotool || echo "     Install: nix-shell -p xdotool"
check_command import || echo "     Install: nix-shell -p imagemagick"
check_command curl || echo "     Install: nix-shell -p curl"

# Create session directory
echo ""
echo "📁 Creating session directory..."
mkdir -p /tmp/webpilot-sessions
echo "✅ Session directory ready: /tmp/webpilot-sessions"

# Test import
echo ""
echo "🧪 Testing WebPilot import..."
if python3 -c "import sys; sys.path.insert(0, '$SCRIPT_DIR'); from webpilot import WebPilot; print('✅ WebPilot imports successfully!')"; then
    echo ""
else
    echo "❌ Import failed. Check Python installation."
    exit 1
fi

# Show usage
echo ""
echo "📚 Quick Start Guide:"
echo "===================="
echo ""
echo "1. Test the installation:"
echo "   webpilot --version"
echo ""
echo "2. Browse a website:"
echo "   webpilot browse https://example.com"
echo ""
echo "3. Take a screenshot:"
echo "   webpilot screenshot --url https://github.com --output github.png"
echo ""
echo "4. Interactive mode:"
echo "   webpilot interact"
echo ""
echo "5. Run the example:"
echo "   python3 $SCRIPT_DIR/examples/basic_automation.py"
echo ""
echo "6. Use in Python:"
echo "   from webpilot import WebPilot"
echo "   pilot = WebPilot()"
echo "   pilot.start('https://example.com')"
echo ""
echo "✨ WebPilot setup complete!"
echo ""
echo "For full documentation, see: $SCRIPT_DIR/README.md"