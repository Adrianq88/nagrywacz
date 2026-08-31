#!/usr/bin/env bash
# Usuwa wpis crona utworzony przez install_cron.sh.
set -euo pipefail

( crontab -l 2>/dev/null | grep -vF "run_weekly.sh" ) | crontab - || true
echo "Usunieto wpis crona dla run_weekly.sh."
echo
echo "Aktualny crontab:"
crontab -l 2>/dev/null || echo "(pusty)"
