# Usuwa zadanie utworzone przez install_task.ps1. Uruchom jako Administrator.
Unregister-ScheduledTask -TaskName "NagrywaczMszy" -Confirm:$false
Write-Host "Zadanie 'NagrywaczMszy' usuniete."
