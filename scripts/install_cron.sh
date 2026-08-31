#!/usr/bin/env bash
# Rejestruje wpis w crontabie: kazda niedziela 9:55 UTC-lokalny czas serwera.
# Sprawdz `timedatectl` na VPS i dopasuj godzine ponizej do polskiej strefy
# czasowej (Europe/Warsaw), jesli serwer chodzi na UTC.
#
# Uzycie: bash scripts/install_cron.sh
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$PROJECT_ROOT/logs"

CRON_LINE="55 9 * * 0 $PROJECT_ROOT/scripts/run_weekly.sh >> $PROJECT_ROOT/logs/cron.log 2>&1"

( crontab -l 2>/dev/null | grep -vF "run_weekly.sh" ; echo "$CRON_LINE" ) | crontab -

echo "Zarejestrowano zadanie crona:"
echo "  $CRON_LINE"
echo
echo "Aktualny crontab:"
crontab -l
