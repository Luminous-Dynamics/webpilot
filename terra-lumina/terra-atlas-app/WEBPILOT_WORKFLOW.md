# Terra Atlas + WebPilot Development Workflow

Quick guide for using WebPilot with Terra Atlas.

## Daily Workflow

1. **Start dev server**: `npm run dev`
2. **Verify environment**: `./scripts/daily-dev-check.sh`
3. **Develop features**: Edit code, browser auto-reloads
4. **Test thoroughly**: Run full WebPilot test suite

## WebPilot Features

### ✅ Dev Server Detection (WORKING!)
Auto-discovers running servers, identifies frameworks, zero config.

```bash
poetry run python tests/demo-dev-server-detection.py
```

### Browser-Based Features (Need setup)
- Visual Regression Testing
- Accessibility Audits  
- Performance Monitoring
- Automated Interaction Tests

## Setup

```bash
# Install WebPilot
cd /srv/luminous-dynamics/_development/web-automation/claude-webpilot
poetry install

# Option 1: Use Dev Server Detection (no browsers needed)
poetry run python terra-lumina/terra-atlas-app/tests/demo-dev-server-detection.py

# Option 2: Full testing via Docker
./test-in-docker.sh
```

## Benefits

- **Auto-discovery**: No manual URL configuration
- **Time savings**: ~7 hours/week with full integration
- **Quality**: Catch bugs before deployment

See `WEBPILOT_DEVELOPMENT_WORKFLOW.md` for complete documentation.
