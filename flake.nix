{
  description = "WebPilot - Browser Automation Development Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in {
      devShells.${system}.default = pkgs.mkShell {
        packages = with pkgs; [
          # Core development tools
          python311
          poetry
          git

          # Browsers for manual testing
          firefox
          chromium

          # For reference: NixOS has playwright-driver but it has dependency issues
          # See NIXOS_PLAYWRIGHT_STATUS.md for details
        ];

        shellHook = ''
          echo "🚀 WebPilot Development Environment (NixOS)"
          echo ""
          echo "✅ Python 3.11 + Poetry + Git ready"
          echo "✅ Firefox & Chromium browsers available"
          echo ""
          echo "ℹ️  NOTE: For Playwright testing, use Docker:"
          echo "   docker run -it --rm -v \$(pwd):/workspace \\"
          echo "     mcr.microsoft.com/playwright/python:v1.55.0-focal bash"
          echo ""
          echo "   Then inside container:"
          echo "     cd /workspace && pip install -e . && playwright install firefox"
          echo "     python test_playwright_migration.py"
          echo ""
          echo "See NIXOS_PLAYWRIGHT_STATUS.md for full details."
          echo ""

          # Poetry config
          export POETRY_VIRTUALENVS_CREATE=true
          export POETRY_VIRTUALENVS_IN_PROJECT=true

          echo "✨ Environment ready for development!"
        '';
      };
    };
}
