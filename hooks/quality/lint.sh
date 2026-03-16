#!/bin/bash
# Quality Gate — lint check after code generation
# Triggered by: postToolUse hook (Copilot CLI)
# Installed to: .github/hooks/quality/lint.sh
#
# Runs ruff on every Python file modified during the current tool call.
# Exits 1 on lint failure so the AI agent sees the error and can fix it.

set -euo pipefail

[[ "${SKIP_LINT:-}" == "true" ]] && exit 0

INPUT=$(cat 2>/dev/null || echo "{}")

# Only trigger after successful edit / create tool calls
if command -v jq &>/dev/null; then
  tool_name=$(echo "$INPUT" | jq -r '.toolName // empty' 2>/dev/null || echo "")
  result_type=$(echo "$INPUT" | jq -r '.toolResult.resultType // empty' 2>/dev/null || echo "")
  [[ "$tool_name" != "edit" && "$tool_name" != "create" ]] && exit 0
  [[ "$result_type" != "success" ]] && exit 0
fi

# Resolve ruff — prefer uv run, fall back to global ruff
if command -v uv &>/dev/null; then
  RUFF="uv run ruff"
elif command -v ruff &>/dev/null; then
  RUFF="ruff"
else
  echo "⚠️  Lint skipped — ruff not found (uv add --dev ruff)"
  exit 0
fi

# Collect modified Python files (staged + unstaged)
MODIFIED=$(git diff --name-only HEAD 2>/dev/null | grep '\.py$' || true)
STAGED=$(git diff --cached --name-only 2>/dev/null | grep '\.py$' || true)
FILES=$(printf '%s\n%s' "$MODIFIED" "$STAGED" | sort -u | grep -v '^$' || true)

[[ -z "$FILES" ]] && exit 0

FILE_COUNT=$(echo "$FILES" | wc -l | tr -d ' ')
echo "🔍 Linting ${FILE_COUNT} modified Python file(s)..."

FAILED=0
while IFS= read -r file; do
  [[ -f "$file" ]] || continue
  $RUFF check "$file" 2>&1 || FAILED=1
done <<< "$FILES"

if [[ "$FAILED" -eq 1 ]]; then
  echo ""
  echo "❌ Lint failed — fix the issues above before committing"
  echo "   Run: uv run ruff check --fix <file>"
  echo "   Skip: SKIP_LINT=true"
  exit 1
fi

echo "✅ Lint passed"
exit 0
