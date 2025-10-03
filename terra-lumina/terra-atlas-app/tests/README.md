# Terra Atlas Testing Guide

## The WebGL Challenge 🎯

**Problem**: WebGL (3D globe) doesn't render in headless browsers.

**Solution**: Use `headless=False` for WebGL support! Simple and effective.

## Quick Start

### Complete Test Suite (All 6 WebPilot Features!)

```bash
# Run the complete test suite with WebGL support
python tests/complete-globe-test.py

# This tests:
# ✅ Feature 1: Dev Server Detection
# ✅ Feature 2: Lighthouse Performance Audit
# ✅ Feature 3: Visual Regression (WebGL screenshots!)
# ✅ Feature 4: Accessibility (WCAG 2.1)
# ✅ Feature 5: Smart Selectors
# ✅ Feature 6: Interaction Testing
```

### Prerequisites

1. **Start the dev server first:**
   ```bash
   cd terra-atlas-app
   npm run dev
   ```

2. **Browser will open visibly** (headless=False for WebGL)

3. **Watch the automation** - You'll see the browser testing everything!

## Testing Strategy by Change Type

### CSS/Styling Changes (Small)
```bash
# 1. Run automated tests
python tests/webpilot-globe-test.py

# 2. Quick manual check (30 seconds)
./scripts/visual-verify-globe.sh

# 3. Commit with note
git commit -m "Update marker colors - verified manually"
```

### Feature Changes (Medium)
```bash
# 1. Write/update automated tests
# Edit tests/webpilot-globe-test.py

# 2. Run all tests
python tests/webpilot-globe-test.py

# 3. Full manual verification
./scripts/visual-verify-globe.sh

# 4. Capture screenshots
# Save to docs/visual-evidence/

# 5. Commit with evidence
git commit -m "Add filter animations - tests + screenshots"
```

### Architecture Changes (Large)
```bash
# 1. Update all tests
# Edit tests/webpilot-globe-test.py

# 2. Run automated suite
python tests/webpilot-globe-test.py

# 3. Full verification + video
./scripts/visual-verify-globe.sh

# Record 30-second demo
# Save to docs/visual-evidence/globe-demo.mp4

# 4. Document in PR
# Include screenshots, video, test results
```

## What Gets Automated vs Manual

### ✅ Automated (WebPilot Tests)
- Component structure loads correctly
- Project data fetches and displays
- Filter buttons work
- Click handlers fire
- URL changes happen
- Responsive breakpoints trigger
- Performance metrics (load time, etc.)
- No console errors
- State management works

### ⚠️ Manual (Visual Verification)
- Globe actually renders
- Textures look good
- Colors are correct
- Animations are smooth
- Markers are in right positions
- Lighting looks natural
- No visual glitches

## File Structure

```
terra-atlas-app/
├── tests/
│   ├── README.md (this file)
│   └── webpilot-globe-test.py (automated tests)
├── scripts/
│   └── visual-verify-globe.sh (manual helper)
├── docs/
│   ├── VISUAL_VERIFICATION_STRATEGY.md (full strategy)
│   └── visual-evidence/ (screenshots, videos)
└── package.json (test commands)
```

## NPM Scripts

Add to your `package.json`:

```json
{
  "scripts": {
    "test:auto": "python tests/webpilot-globe-test.py",
    "test:visual": "./scripts/visual-verify-globe.sh",
    "test:all": "npm run test:auto && npm run test:visual"
  }
}
```

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  automated:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install dependencies
        run: npm install
      - name: Start dev server
        run: npm run dev &
      - name: Wait for server
        run: sleep 5
      - name: Run WebPilot tests
        run: python tests/webpilot-globe-test.py

  # Visual tests require manual verification
  # Comment on PR with checklist
  visual-reminder:
    runs-on: ubuntu-latest
    steps:
      - name: Comment PR
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '✅ Automated tests passed!\n\n⚠️ Manual visual verification required:\n- [ ] Globe renders correctly\n- [ ] Markers visible\n- [ ] Animations smooth\n\nRun: `./scripts/visual-verify-globe.sh`'
            })
```

## Best Practices

### 1. Test Data Layer First
```typescript
// Good: Test the underlying logic
expect(transformProjectsToMarkers(projects)).toMatchSnapshot();

// Not possible: Test visual appearance
// ❌ Can't screenshot WebGL
```

### 2. Document Visual Changes
```markdown
## PR Description

### Changes
- Updated globe marker colors from blue to green

### Verification
✅ Automated tests: All passing
✅ Visual check: Verified in Chrome, Firefox

### Screenshots
Before: ![before](docs/visual-evidence/before.png)
After: ![after](docs/visual-evidence/after.png)
```

### 3. Keep Manual Tests Fast
- Use the helper script (structured checklist)
- Only verify what changed
- 5 minutes max for normal changes
- Full verification for releases only

## Troubleshooting

### Tests fail with "Dev server not running"
```bash
# Start dev server first
npm run dev

# Then run tests in another terminal
python tests/webpilot-globe-test.py
```

### WebPilot import errors
```bash
# Install WebPilot
cd ../../../_development/web-automation/claude-webpilot
poetry install
```

### Can't see visual changes in tests
```bash
# That's expected! WebGL doesn't render in headless mode
# Use manual verification:
./scripts/visual-verify-globe.sh
```

## Summary

**90% automated** - Data, interactions, structure, performance
**10% manual** - Visual appearance only (when it actually changes)

This is a **realistic and sustainable** approach that:
- ✅ Catches functional bugs automatically
- ✅ Ensures visual quality through quick manual checks
- ✅ Doesn't waste time trying to screenshot WebGL
- ✅ Documents what was verified and how

---

**Questions?** See `docs/VISUAL_VERIFICATION_STRATEGY.md` for detailed strategy.
