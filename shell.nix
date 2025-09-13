{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    # Python and Poetry
    python311
    poetry
    
    # Browsers
    firefox
    chromium
    
    # Browser drivers
    geckodriver
    chromedriver
    
    # System tools for automation
    xdotool
    imagemagick
    scrot
    curl
    jq
    
    # OCR support
    tesseract
    
    # Development tools
    git
    ripgrep
    fd
  ];
  
  shellHook = ''
    echo "🚁 WebPilot Development Environment"
    echo "=================================="
    echo ""
    echo "Available browsers:"
    command -v firefox >/dev/null && echo "  ✅ Firefox"
    command -v chromium >/dev/null && echo "  ✅ Chromium"
    echo ""
    echo "Available drivers:"
    command -v geckodriver >/dev/null && echo "  ✅ Geckodriver"
    command -v chromedriver >/dev/null && echo "  ✅ Chromedriver"
    echo ""
    echo "Quick start:"
    echo "  1. poetry install          # Install Python dependencies"
    echo "  2. poetry install -E vision # With vision features"
    echo "  3. poetry run webpilot --help"
    echo ""
    echo "Development:"
    echo "  poetry run pytest          # Run tests"
    echo "  poetry run black .         # Format code"
    echo "  poetry run ruff check .    # Lint code"
    echo ""
    
    # Create virtual environment in project
    export POETRY_VIRTUALENVS_IN_PROJECT=true
    
    # Ensure Poetry is configured correctly
    poetry config virtualenvs.create true
    poetry config virtualenvs.in-project true
  '';
  
  # Environment variables for browser automation
  CHROME_BIN = "${pkgs.chromium}/bin/chromium";
  FIREFOX_BIN = "${pkgs.firefox}/bin/firefox";
  GECKODRIVER_PATH = "${pkgs.geckodriver}/bin/geckodriver";
  CHROMEDRIVER_PATH = "${pkgs.chromedriver}/bin/chromedriver";
}