#!/bin/bash
# Quality Gate — code coverage pre-commit hook
# Installed to: .git/hooks/pre-commit
#
# Blocks git commit if test coverage is below 80%.
# Requires: uv, pytest, pytest-cov
#
# Install:
#   cp hooks/quality/pre-commit.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit
#
# Bypass (emergency only):
#   SKIP_COVERAGE=true git commit -m "..."

set -euo pipefail

[[ "${SKIP_COVERAGE:-}" == "true" ]] && {
  echo "⚠️  Coverage check skipped (SKIP_COVERAGE=true)"
  exit 0
}

THRESHOLD=80

# Require uv
if ! command -v uv &>/dev/null; then
  echo "⚠️  Coverage check skipped — uv not found"
  exit 0
fi

# Ensure pytest-cov is available
if ! uv run python -c "import pytest_cov" 2>/dev/null; then
  echo "⚠️  Coverage check skipped — pytest-cov not installed (uv add --dev pytest-cov)"
  exit 0
fi

echo "🧪 Running tests with coverage (minimum: ${THRESHOLD}%)..."
echo ""

# Run pytest with coverage — fail-under enforces the threshold
if uv run pytest \
    --cov \
    --cov-report=term-missing \
    --cov-fail-under="${THRESHOLD}" \
    -q 2>&1; then
  echo ""
  echo "✅ Coverage >= ${THRESHOLD}% — commit allowed"
  exit 0
else
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "❌ COMMIT BLOCKED — coverage below ${THRESHOLD}%"
  echo ""
  echo "   Add tests to bring coverage up, then retry."
  echo "   To bypass (emergency only): SKIP_COVERAGE=true git commit -m \"...\""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  exit 1
fi
