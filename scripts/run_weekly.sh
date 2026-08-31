#!/usr/bin/env bash
# Uruchamiane co niedziele przez crona (patrz install_cron.sh).
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

"$PROJECT_ROOT/venv/bin/python" "$PROJECT_ROOT/src/record_transcribe.py" --config "$PROJECT_ROOT/config.json"
