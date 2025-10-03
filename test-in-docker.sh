#!/usr/bin/env bash
# Run Terra Atlas complete test suite in Docker

echo "🌍 Running Terra Atlas Complete Test Suite in Docker..."
echo ""

docker run --rm \
  -v "$(pwd)":/workspace \
  --network host \
  mcr.microsoft.com/playwright/python:latest \
  bash -c 'cd /workspace && pip install -e . -q && playwright install firefox --with-deps > /dev/null 2>&1 && python terra-lumina/terra-atlas-app/tests/complete-globe-test.py'
