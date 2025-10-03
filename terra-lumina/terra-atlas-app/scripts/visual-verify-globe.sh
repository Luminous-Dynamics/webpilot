#!/usr/bin/env bash
# Terra Atlas Globe Visual Verification Script
#
# This script helps with manual visual verification of the globe
# when automated screenshot testing isn't feasible due to WebGL limitations

set -e

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  🌍 Terra Atlas Globe Visual Verification                 ║"
echo "║  Manual testing for WebGL components                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm not found. Please install Node.js${NC}"
    exit 1
fi

# Navigate to correct directory
cd "$(dirname "$0")/.."

# Check if dev server is already running
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Dev server already running at http://localhost:3000${NC}"
    ALREADY_RUNNING=true
else
    echo -e "${GREEN}Starting dev server...${NC}"
    npm run dev > /tmp/terra-atlas-dev.log 2>&1 &
    DEV_PID=$!
    ALREADY_RUNNING=false

    # Wait for server to be ready
    echo -n "Waiting for server to start"
    for i in {1..30}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            echo ""
            echo -e "${GREEN}✅ Dev server started successfully${NC}"
            break
        fi
        echo -n "."
        sleep 1
    done
    echo ""
fi

# Open browser
echo ""
echo -e "${CYAN}🌐 Opening browser at http://localhost:3000${NC}"
echo ""

# Try to open in default browser
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:3000 &
elif command -v open &> /dev/null; then
    open http://localhost:3000 &
else
    echo -e "${YELLOW}Please open http://localhost:3000 in your browser${NC}"
fi

# Show verification checklist
echo -e "${CYAN}┌─────────────────────────────────────────────────────────┐"
echo "│  📋 Manual Verification Checklist                      │"
echo "└─────────────────────────────────────────────────────────┘${NC}"
echo ""
echo "Please verify the following in your browser:"
echo ""
echo "  🌍 Globe Rendering"
echo "     [ ] Globe loads within 2-3 seconds"
echo "     [ ] Earth texture is high quality (no pixelation)"
echo "     [ ] Lighting and shadows look natural"
echo "     [ ] Globe rotates smoothly (60fps)"
echo ""
echo "  📍 Project Markers"
echo "     [ ] All demo markers are visible"
echo "     [ ] Markers are in correct geographic positions"
echo "     [ ] Marker colors match project types"
echo "     [ ] Marker sizes are appropriate"
echo ""
echo "  🖱️  Interactions"
echo "     [ ] Mouse drag rotates the globe"
echo "     [ ] Scroll wheel zooms in/out"
echo "     [ ] Hover over marker shows highlight"
echo "     [ ] Click marker shows project details"
echo "     [ ] Auto-rotation can be toggled"
echo ""
echo "  🎨 Filters & UI"
echo "     [ ] Filter buttons work correctly"
echo "     [ ] 'Solar' filter shows only solar projects"
echo "     [ ] 'Wind' filter shows only wind projects"
echo "     [ ] 'All Projects' shows everything"
echo "     [ ] Project count updates correctly"
echo ""
echo "  📱 Responsive"
echo "     [ ] Works at desktop size (1920x1080)"
echo "     [ ] Works at tablet size (768x1024)"
echo "     [ ] Works at mobile size (375x667)"
echo ""
echo "  ⚡ Performance"
echo "     [ ] No console errors (F12 > Console)"
echo "     [ ] Frame rate stays above 45fps"
echo "     [ ] Memory usage stable over 2 minutes"
echo "     [ ] No WebGL warnings"
echo ""

# Wait for user confirmation
echo -e "${YELLOW}Press ENTER when verification is complete...${NC}"
read -r

# Take screenshot for documentation
echo ""
echo -e "${CYAN}Would you like to take a screenshot for documentation? (y/n)${NC}"
read -r SCREENSHOT

if [ "$SCREENSHOT" = "y" ] || [ "$SCREENSHOT" = "Y" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    SCREENSHOT_PATH="docs/visual-evidence/globe-${TIMESTAMP}.png"

    echo ""
    echo -e "${GREEN}Instructions:${NC}"
    echo "1. Switch to your browser window"
    echo "2. Use your OS screenshot tool:"
    echo "   - Linux: PrtScn or Shift+PrtScn"
    echo "   - macOS: Cmd+Shift+4"
    echo "   - Windows: Win+Shift+S"
    echo "3. Save to: ${SCREENSHOT_PATH}"
    echo ""
    echo "Press ENTER when screenshot is saved..."
    read -r

    if [ -f "$SCREENSHOT_PATH" ]; then
        echo -e "${GREEN}✅ Screenshot saved: ${SCREENSHOT_PATH}${NC}"
    else
        echo -e "${YELLOW}⚠️  Screenshot not found at expected path${NC}"
        echo "   Please save manually to docs/visual-evidence/"
    fi
fi

# Clean up
echo ""
if [ "$ALREADY_RUNNING" = false ]; then
    echo -e "${CYAN}Stopping dev server...${NC}"
    kill $DEV_PID 2>/dev/null || true
    echo -e "${GREEN}✅ Dev server stopped${NC}"
else
    echo -e "${YELLOW}ℹ️  Leaving dev server running (was already running)${NC}"
fi

echo ""
echo -e "${GREEN}┌─────────────────────────────────────────────────────────┐"
echo "│  ✅ Visual Verification Session Complete                │"
echo "└─────────────────────────────────────────────────────────┘${NC}"
echo ""
echo "Next steps:"
echo "  • If issues found: Document and fix"
echo "  • If all good: Commit changes with 'Verified manually' note"
echo "  • Include screenshot in PR if visual changes made"
echo ""
