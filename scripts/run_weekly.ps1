# Uruchamiane co niedziele przez Harmonogram zadan Windows (patrz install_task.ps1).
# Aktywuje wirtualne srodowisko i odpala nagrywanie + transkrypcje.

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

& "$ProjectRoot\venv\Scripts\python.exe" "$ProjectRoot\src\record_transcribe.py" --config "$ProjectRoot\config.json"
exit $LASTEXITCODE
