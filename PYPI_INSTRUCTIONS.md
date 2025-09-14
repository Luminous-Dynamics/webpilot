# PyPI Publication Instructions

## Prerequisites
1. Create PyPI account at https://pypi.org/account/register/
2. Create TestPyPI account at https://test.pypi.org/account/register/
3. Generate API tokens for both

## Configure Poetry with API Tokens

```bash
# For TestPyPI
poetry config pypi-token.testpypi <your-test-token>

# For PyPI (production)
poetry config pypi-token.pypi <your-production-token>
```

## Publish to TestPyPI First

```bash
# Publish to TestPyPI
poetry publish -r testpypi

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ webpilot
```

## Publish to PyPI (Production)

```bash
# Once verified on TestPyPI, publish to production
poetry publish

# Verify installation
pip install webpilot
```

## Alternative: Using Twine

```bash
# Install twine
pip install twine

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Upload to PyPI
twine upload dist/*
```

## Current Package Files
- `dist/webpilot-1.1.0-py3-none-any.whl`
- `dist/webpilot-1.1.0.tar.gz`

Both files are ready for upload!