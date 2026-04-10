#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Activate venv if present
if [[ -f ".venv/bin/activate" ]]; then
    source .venv/bin/activate
fi

# Check server is running
if ! curl -sf http://localhost:8000/api/health > /dev/null 2>&1; then
    echo ""
    echo "  Server not running. Start it first:"
    echo "  uvicorn server:app --port 8000"
    echo ""
    exit 1
fi

# Run tests
PYTHONPATH="$REPO_ROOT" python tests/test_api.py "$@"
