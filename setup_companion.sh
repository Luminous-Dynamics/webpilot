#!/usr/bin/env bash
# Claude Development Companion - Global Setup Script

echo "🤖 Setting up Claude Development Companion"
echo "=========================================="

# Create companion directory in home
COMPANION_HOME="$HOME/.claude-companion"
mkdir -p "$COMPANION_HOME"

# Copy core files
echo "📁 Installing companion files..."
cp /srv/luminous-dynamics/_development/web-automation/claude-webpilot/claude_companion.py "$COMPANION_HOME/"
cp /srv/luminous-dynamics/_development/web-automation/claude-webpilot/companion.py "$COMPANION_HOME/"
cp /srv/luminous-dynamics/_development/web-automation/claude-webpilot/feedback_example.py "$COMPANION_HOME/"

# Create a global launcher script
cat > "$COMPANION_HOME/companion" << 'EOF'
#!/usr/bin/env bash
# Claude Companion Launcher

# Check for required packages
check_requirements() {
    python3 -c "import mss" 2>/dev/null || echo "⚠️  Install screen capture: pip install mss Pillow"
    python3 -c "import selenium" 2>/dev/null || echo "⚠️  Install browser automation: pip install selenium"
}

# Get the workspace (current directory or first argument)
WORKSPACE="${1:-$(pwd)}"

# Run the companion
check_requirements
cd "$HOME/.claude-companion"
python3 companion.py --workspace "$WORKSPACE"
EOF

chmod +x "$COMPANION_HOME/companion"

# Create shell aliases
echo "📝 Adding shell aliases..."

# For bash
if [ -f "$HOME/.bashrc" ]; then
    grep -q "claude-companion" "$HOME/.bashrc" || cat >> "$HOME/.bashrc" << 'EOF'

# Claude Development Companion
alias companion="$HOME/.claude-companion/companion"
alias comp="$HOME/.claude-companion/companion"
alias claude-dev="$HOME/.claude-companion/companion"

# Quick companion commands
companion-test() {
    python3 -c "from claude_companion import ClaudeCompanion; c = ClaudeCompanion(); c.run('$1')"
}

companion-show() {
    python3 -c "from claude_companion import ClaudeCompanion; c = ClaudeCompanion(); c.capture(annotation='$1')"
}
EOF
    echo "✅ Added to ~/.bashrc"
fi

# For zsh
if [ -f "$HOME/.zshrc" ]; then
    grep -q "claude-companion" "$HOME/.zshrc" || cat >> "$HOME/.zshrc" << 'EOF'

# Claude Development Companion
alias companion="$HOME/.claude-companion/companion"
alias comp="$HOME/.claude-companion/companion"
alias claude-dev="$HOME/.claude-companion/companion"

# Quick companion commands
companion-test() {
    python3 -c "from claude_companion import ClaudeCompanion; c = ClaudeCompanion(); c.run('$1')"
}

companion-show() {
    python3 -c "from claude_companion import ClaudeCompanion; c = ClaudeCompanion(); c.capture(annotation='$1')"
}
EOF
    echo "✅ Added to ~/.zshrc"
fi

# Create a desktop entry for GUI environments
mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/claude-companion.desktop" << EOF
[Desktop Entry]
Name=Claude Development Companion
Comment=AI pair programmer with real-time feedback
Exec=$COMPANION_HOME/companion
Icon=terminal
Terminal=true
Type=Application
Categories=Development;
EOF

echo ""
echo "✅ Installation Complete!"
echo "========================"
echo ""
echo "🚀 Quick Start Commands:"
echo "  companion         - Launch interactive companion"
echo "  comp             - Short alias"
echo "  claude-dev       - Descriptive alias"
echo ""
echo "📝 Direct Commands:"
echo "  companion-test 'npm test'  - Run a quick test"
echo "  companion-show 'error'     - Capture screen"
echo ""
echo "⚠️  Reload your shell or run:"
echo "  source ~/.bashrc  (or ~/.zshrc)"
echo ""