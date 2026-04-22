#!/bin/bash
set -e

if [ -f pyproject.toml ]; then
  uv sync --frozen 2>/dev/null || uv sync || true
fi

echo "post-merge: ok"
