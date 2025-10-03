#!/bin/bash
# WebPilot v2.0 Cleanup Script
# Removes 70% redundant browser automation code

echo "🧹 WebPilot v2.0 Cleanup - Removing redundant code"
echo "=================================================="

# Count before
BEFORE=$(find src -name "*.py" | wc -l)
echo "Files before cleanup: $BEFORE"

# Remove redundant files
rm -rf src/webpilot/core.py
rm -rf src/webpilot/parallel/__pycache__/worker.cpython-313.pyc
rm -rf src/webpilot/parallel/__pycache__/load_balancer.cpython-313.pyc
rm -rf src/webpilot/parallel/__pycache__/results.cpython-313.pyc
rm -rf src/webpilot/parallel/__pycache__/scheduler.cpython-313.pyc
rm -rf src/webpilot/parallel/__pycache__/__init__.cpython-313.pyc
rm -rf src/webpilot/parallel/__pycache__/executor.cpython-313.pyc
rm -rf src/webpilot/mobile/__pycache__/gestures.cpython-313.pyc
rm -rf src/webpilot/mobile/__pycache__/locators.cpython-313.pyc
rm -rf src/webpilot/mobile/__pycache__/capabilities.cpython-313.pyc
rm -rf src/webpilot/mobile/__pycache__/__init__.cpython-313.pyc
rm -rf src/webpilot/mobile/__pycache__/mobile_pilot.cpython-313.pyc
rm -rf src/webpilot/backends/playwright_pilot.py
rm -rf src/webpilot/backends/selenium.py
rm -rf src/webpilot/backends/async_pilot.py
rm -rf src/webpilot/backends/__pycache__/async_pilot.cpython-313.pyc
rm -rf src/webpilot/backends/__pycache__/selenium.cpython-313.pyc
rm -rf src/webpilot/utils/smart_wait.py
rm -rf src/webpilot/api/__pycache__/response.cpython-313.pyc
rm -rf src/webpilot/api/__pycache__/request.cpython-313.pyc
rm -rf src/webpilot/api/__pycache__/client.cpython-313.pyc
rm -rf src/webpilot/api/__pycache__/auth.cpython-313.pyc
rm -rf src/webpilot/api/__pycache__/models.cpython-313.pyc
rm -rf src/webpilot/api/__pycache__/__init__.cpython-313.pyc
rm -rf src/webpilot/api/__pycache__/session.cpython-313.pyc
rm -rf src/webpilot/backends/
rm -rf src/webpilot/parallel/
rm -rf src/webpilot/api/
rm -rf src/webpilot/mobile/

# Count after  
AFTER=$(find src -name "*.py" | wc -l)
echo "Files after cleanup: $AFTER"

REMOVED=$((BEFORE - AFTER))
PERCENT=$((REMOVED * 100 / BEFORE))
echo ""
echo "✅ Cleanup complete!"
echo "Removed $REMOVED files ($PERCENT% reduction)"
