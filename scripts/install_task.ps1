# Rejestruje w Harmonogramie zadan Windows cotygodniowe zadanie: kazda niedziela 9:50.
# 9:50 (10 min przed msza), zeby yt-dlp zdazyl zlapac poczatek transmisji.
#
# Uruchom w PowerShell JAKO ADMINISTRATOR:
#   powershell -ExecutionPolicy Bypass -File install_task.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$RunScript = Join-Path $ProjectRoot "scripts\run_weekly.ps1"

$Action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$RunScript`""

$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 9:50AM

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
