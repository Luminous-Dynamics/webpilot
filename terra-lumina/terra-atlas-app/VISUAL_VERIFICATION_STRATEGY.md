# Visual Verification Strategy for Terra Atlas Globe

## The Challenge
WebGL-based 3D visualizations (like our globe) don't render in headless browsers, making automated screenshot testing impractical for:
- GPU-dependent rendering (Three.js, WebGL)
- NixOS environment limitations with browser dependencies

## Hybrid Testing Approach ✅

### 1. Automated Testing (Data & Logic Layer)
Test what CAN be automated - the data and component behavior:

```typescript
// tests/globe/data-layer.test.ts
describe('Globe Data Layer', () => {
  it('correctly transforms project data for visualization', () => {
    const projects = mockProjects;
    const markers = transformProjectsToMarkers(projects);

    expect(markers).toHaveLength(projects.length);
    expect(markers[0]).toMatchSnapshot(); // Snapshot the data structure
  });

  it('filters projects by type correctly', () => {
    const filtered = filterProjectsByType(projects, 'solar');
    expect(filtered.every(p => p.type === 'solar')).toBe(true);
  });

  it('calculates correct globe positions from lat/lng', () => {
    const position = latLngToGlobePosition(37.7749, -122.4194);
    expect(position.x).toBeCloseTo(expected.x, 2);
    expect(position.y).toBeCloseTo(expected.y, 2);
    expect(position.z).toBeCloseTo(expected.z, 2);
  });
});
```

### 2. Component Snapshot Testing
Test component props and state without rendering:

```typescript
// tests/globe/component-snapshots.test.ts
describe('TerraGlobe Component', () => {
  it('renders with correct props structure', () => {
    const { container } = render(
      <TerraGlobe projects={mockProjects} selectedType="solar" />
    );

    // Snapshot the DOM structure (not visual)
    expect(container.firstChild).toMatchSnapshot();
  });

  it('applies correct CSS classes based on state', () => {
    const { container } = render(<TerraGlobe loading={true} />);
    expect(container.querySelector('.loading')).toBeInTheDocument();
  });
});
```

### 3. Manual Visual Verification (When Needed)
For actual visual changes, use a structured manual process:

#### Quick Visual Check Script
```bash
#!/bin/bash
# scripts/visual-verify-globe.sh

echo "🌍 Terra Atlas Globe Visual Verification"
echo "========================================"
echo ""
echo "Starting dev server..."
npm run dev &
DEV_PID=$!

sleep 3

echo "✅ Dev server started at http://localhost:3000"
echo ""
echo "📋 Manual Verification Checklist:"
echo ""
echo "  [ ] Globe renders correctly"
echo "  [ ] All project markers visible"
echo "  [ ] Hover states work"
echo "  [ ] Click interactions functional"
echo "  [ ] Animation smooth (60fps)"
echo "  [ ] No console errors"
echo "  [ ] Mobile responsive"
echo ""
echo "Press ENTER when verification complete..."
read

kill $DEV_PID
echo "✅ Verification session ended"
```

#### Visual Regression Checklist
Create `docs/VISUAL_REGRESSION_CHECKLIST.md`:
```markdown
# Visual Regression Checklist

## Before Each Release
Test these scenarios manually in browser:

### Globe Rendering
- [ ] Globe loads within 2 seconds
- [ ] Texture quality is high (no pixelation)
- [ ] Lighting/shadows render correctly
- [ ] Globe rotates smoothly (60fps)

### Project Markers
- [ ] All markers appear in correct locations
- [ ] Marker sizes scale appropriately with zoom
- [ ] Colors match project types
- [ ] Hover highlights work
- [ ] Click opens correct project details

### Interactions
- [ ] Mouse drag rotates globe
- [ ] Scroll zooms in/out
- [ ] Touch gestures work on mobile
- [ ] Auto-rotation can be paused/resumed

### Performance
- [ ] Frame rate stays above 45fps
- [ ] Memory usage stable over 5 minutes
- [ ] No WebGL warnings in console
```

### 4. WebPilot for Non-Visual Testing
Use WebPilot to test everything EXCEPT the visual rendering:

```python
# tests/webpilot/globe-interactions.py
"""Test globe interactions using WebPilot"""

from webpilot import WebPilot

pilot = WebPilot()
pilot.start("http://localhost:3000")

# Test that globe component loads
assert pilot.element_exists(".terra-globe-container")

# Test data loads
pilot.wait_for_element(".project-marker", timeout=5000)
markers = pilot.count_elements(".project-marker")
assert markers > 0, "Project markers should be visible"

# Test interactions work (even if we can't see the result)
pilot.click(".project-marker:first-child")
assert pilot.element_exists(".project-details-panel"), "Details panel should open"

# Test filters work
pilot.click("button[data-filter='solar']")
pilot.wait(1000)  # Wait for animation
# Verify URL or state changed
assert "filter=solar" in pilot.get_url()

print("✅ Globe interaction tests passed")
```

### 5. Video Recording for Documentation
When making significant visual changes:

```bash
# Use OBS Studio or simple screen recording
# Record a 30-second demo showing:
# 1. Globe loading
# 2. Rotation
# 3. Marker interaction
# 4. Filter changes

# Save as: docs/visual-evidence/globe-v{VERSION}.mp4
```

## Recommended Workflow

### For Small Changes (CSS, colors, sizing)
1. ✅ Automated: Run component snapshot tests
2. ✅ Manual: Quick browser check (30 seconds)
3. ✅ Git: Commit with screenshot in PR description

### For Medium Changes (new features, layouts)
1. ✅ Automated: Data layer tests + component tests
2. ✅ Manual: Full checklist verification (5 minutes)
3. ✅ WebPilot: Interaction tests
4. ✅ Git: Commit with before/after screenshots

### For Major Changes (architecture, rendering engine)
1. ✅ Automated: Full test suite
2. ✅ Manual: Complete checklist + multiple browsers
3. ✅ WebPilot: Full interaction suite
4. ✅ Video: Record demo for documentation
5. ✅ Git: Detailed PR with visual evidence

## Tools Setup

### Install Visual Testing Tools
```bash
# For manual verification
npm install -D @storybook/react  # Component playground

# For data testing
npm install -D jest @testing-library/react

# For interaction testing (via WebPilot)
cd ../../../_development/web-automation/claude-webpilot
poetry install
```

### Quick Commands
```json
{
  "scripts": {
    "test:data": "jest tests/globe/data-layer.test.ts",
    "test:components": "jest tests/globe/component-snapshots.test.ts",
    "test:interactions": "poetry run python tests/webpilot/globe-interactions.py",
    "verify:visual": "./scripts/visual-verify-globe.sh",
    "storybook": "storybook dev -p 6006"
  }
}
```

## Why This Works

✅ **Fast automated tests** for 90% of changes (data, logic, DOM structure)
✅ **Manual verification** only for actual visual changes (10% of commits)
✅ **WebPilot** handles all interactions and functional testing
✅ **No false negatives** from trying to screenshot WebGL
✅ **Clear documentation** of what was verified and how

## Example PR Description Template

```markdown
## Changes
- Updated globe marker colors
- Added hover animation

## Verification
✅ Automated Tests: `npm test` (all passing)
✅ Visual Check: Verified in Chrome, Firefox, Safari
✅ Interactions: WebPilot tests passing
✅ Checklist: 7/7 items verified

### Screenshots
Before: ![before](...)
After: ![after](...)

### Video
30-second demo: [globe-demo.mp4](...)
```

---

**Bottom Line**: Accept that WebGL can't be screenshot-tested automatically. Instead:
1. Test the data/logic layer thoroughly (automated)
2. Test interactions with WebPilot (automated)
3. Do quick manual visual checks when needed (5 minutes)
4. Document with real screenshots/video (manual, but rare)

This gives you **90% automation with 10% manual verification** - which is realistic and sustainable.
