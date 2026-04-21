$runDir = "$env:LOCALAPPDATA\Docker\run"
Write-Host "Cleaning stale Docker sockets in: $runDir"
Get-ChildItem $runDir -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "Removing: $($_.Name)"
    cmd /c "del /f /q `"$($_.FullName)`"" 2>&1
}
Write-Host "Remaining files:"
Get-ChildItem $runDir -ErrorAction SilentlyContinue | Select-Object Name
