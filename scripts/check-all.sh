#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
codex_dir="${CODEX_HOME:-${HOME}/.codex}"
validator="$codex_dir/skills/.system/skill-creator/scripts/quick_validate.py"

cd "$repo_dir"

if [[ ! -f "$validator" ]]; then
  echo "Skill validator not found: $validator" >&2
  exit 1
fi

skills=(
  submit-product-directories-v1-batch
  submit-product-directories-v2-quality
  writer
  writer/linkedin-writer
  writer/medium-writer
  writer/wechat-writer
)

for skill in "${skills[@]}"; do
  echo "Validating $skill"
  uv run python "$validator" "$skill"
done

echo "Running V1 tests"
uv run python -m unittest discover -s submit-product-directories-v1-batch/tests

echo "Running V2 tests"
uv run python -m unittest discover -s submit-product-directories-v2-quality/tests

echo "Running Writer tests"
node --test writer/tests/upload-r2.test.mjs
