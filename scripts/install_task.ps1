# Rejestruje w Harmonogramie zadan Windows cotygodniowe zadanie: kazda niedziela 9:55.
# Stream kosciola leci 24/7, wiec skrypt nie czeka az sie "zacznie" - startuje
# nagrywanie dokladnie o tej godzinie i nagrywa przez record_duration_minutes
# (patrz config.json), czyli 5 min przed msza + zapas na przeciagniecie sie.
#
# Uruchom w PowerShell JAKO ADMINISTRATOR:
#   powershell -ExecutionPolicy Bypass -File install_task.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RunScript = Join-Path $ProjectRoot "scripts\run_weekly.ps1"

$Action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$RunScript`""

$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 9:55AM

$Settings = New-ScheduledTaskSettingsSet `
    -WakeToRun `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -ExecutionTimeLimit (New-TimeSpan -Hours 3) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5)

Register-ScheduledTask -TaskName "NagrywaczMszy" `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Description "Nagrywa niedzielna transmisje mszy z YouTube i zapisuje transkrypcje na Dysku Google" `
    -Force

Write-Host "Zadanie 'NagrywaczMszy' zarejestrowane: kazda niedziela o 9:50."
Write-Host "Upewnij sie, ze w ustawieniach zasilania Windows wlaczone jest 'Zezwalaj na czasomierze pobudki' (Wake timers),"
Write-Host "a laptop jest podlaczony do zasilania i nie jest calkowicie wylaczany przed ta godzina."
