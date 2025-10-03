#!/usr/bin/env python3
"""
WebPilot v2.0 Cleanup Plan - Identifies redundant code to remove
"""

import os
from pathlib import Path

# Files and directories to KEEP (AI value)
KEEP = {
    # Core v2.0 architecture
    'src/webpilot/v2/',
    'src/webpilot/ai/',
    
    # Utilities that support AI
    'src/webpilot/utils/logger.py',
    'src/webpilot/utils/config.py',
    
    # CLI (will be refactored)
    'src/webpilot/cli/',
    
    # Reporting (valuable for all frameworks)
    'src/webpilot/reporting/',
    
    # Package essentials
    'src/webpilot/__init__.py',
    'setup.py',
    'pyproject.toml',
    'requirements.txt',
    
    # Documentation (will be updated)
    'README.md',
    'docs/',
    'examples/',
    
    # Development files
    '.gitignore',
    'LICENSE',
    'CHANGELOG.md',
}

# Files and directories to REMOVE (redundant browser automation)
REMOVE = {
    # Old browser automation core
    'src/webpilot/core.py',
    'src/webpilot/webpilot.py',
    'src/webpilot/browser.py',
    'src/webpilot/element.py',
    
    # Redundant backends
    'src/webpilot/backends/',
    
    # Old mobile support (Playwright has better)
    'src/webpilot/mobile/',
    
    # Parallel execution (Playwright has built-in)
    'src/webpilot/parallel/',
    
    # API testing (separate concern)
    'src/webpilot/api/',
    
    # Recorder (browser-specific)
    'src/webpilot/recorder.py',
    
    # Smart wait (Playwright has better)
    'src/webpilot/utils/smart_wait.py',
    
    # Old tests (will need rewriting)
    'tests/test_core.py',
    'tests/test_backends.py',
    'tests/test_browser.py',
    'tests/test_integration_suite.py',
    
    # Chrome extension (separate project)
    'chrome-extension/',
    
    # Old validation scripts
    'validate_features.py',
    'test_v1_8_0_complete.py',
}

def analyze_cleanup():
    """Analyze what will be removed"""
    
    print("🔍 WebPilot v2.0 Cleanup Analysis")
    print("=" * 50)
    
    to_remove = []
    to_keep = []
    
    # Check each path
    for root, dirs, files in os.walk('src'):
        for file in files:
            filepath = os.path.join(root, file)
            
            # Check if should keep
            should_keep = any(filepath.startswith(k) or filepath.endswith(k) 
                             for k in KEEP)
            
            # Check if should remove
            should_remove = any(filepath.startswith(r) or filepath.endswith(r) 
                              for r in REMOVE)
            
            if should_remove and not should_keep:
                to_remove.append(filepath)
            elif should_keep:
                to_keep.append(filepath)
    
    # Add directories to remove
    for remove_dir in REMOVE:
        if os.path.isdir(remove_dir):
            to_remove.append(remove_dir)
    
    print(f"\n📊 Statistics:")
    print(f"Files to remove: {len(to_remove)}")
    print(f"Files to keep: {len(to_keep)}")
    print(f"Reduction: {len(to_remove) / (len(to_remove) + len(to_keep)) * 100:.1f}%")
    
    print(f"\n🗑️ Will Remove:")
    for path in sorted(to_remove)[:20]:
        print(f"  - {path}")
    if len(to_remove) > 20:
        print(f"  ... and {len(to_remove) - 20} more files")
    
    print(f"\n✅ Will Keep:")
    for path in sorted(to_keep)[:10]:
        print(f"  - {path}")
    if len(to_keep) > 10:
        print(f"  ... and {len(to_keep) - 10} more files")
    
    return to_remove

def generate_cleanup_script(to_remove):
    """Generate shell script to perform cleanup"""
    
    script = """#!/bin/bash
# WebPilot v2.0 Cleanup Script
# Removes 70% redundant browser automation code

echo "🧹 WebPilot v2.0 Cleanup - Removing redundant code"
echo "=================================================="

# Count before
BEFORE=$(find src -name "*.py" | wc -l)
echo "Files before cleanup: $BEFORE"

# Remove redundant files
"""
    
    for path in to_remove:
        script += f"rm -rf {path}\n"
    
    script += """
# Count after  
AFTER=$(find src -name "*.py" | wc -l)
echo "Files after cleanup: $AFTER"

REMOVED=$((BEFORE - AFTER))
PERCENT=$((REMOVED * 100 / BEFORE))
echo ""
echo "✅ Cleanup complete!"
echo "Removed $REMOVED files ($PERCENT% reduction)"
"""
    
    with open('cleanup_v2.sh', 'w') as f:
        f.write(script)
    
    os.chmod('cleanup_v2.sh', 0o755)
    print("\n✅ Generated cleanup_v2.sh")
    print("Run: ./cleanup_v2.sh")

if __name__ == '__main__':
    to_remove = analyze_cleanup()
    generate_cleanup_script(to_remove)