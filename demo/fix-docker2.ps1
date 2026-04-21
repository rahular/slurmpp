# Fix stale Docker socket files by creating an empty temp dir and using robocopy
$runDir = "$env:LOCALAPPDATA\Docker\run"
$emptyDir = "$env:TEMP\empty-docker-fix"
New-Item -ItemType Directory -Force -Path $emptyDir | Out-Null

# robocopy /PURGE copies from empty dir, deleting everything in dest
# But we only want to delete specific files
foreach ($file in @("dockerInference", "userAnalyticsOtlpHttp.sock")) {
    $fullPath = Join-Path $runDir $file
    if (Test-Path $fullPath -ErrorAction SilentlyContinue) {
        Write-Host "Trying to remove: $fullPath"
        # Try with .NET
        try {
            [System.IO.File]::Delete($fullPath)
            Write-Host "  Deleted via .NET"
        } catch {
            Write-Host "  .NET failed: $_"
        }
    }
}

# Also try takeown + icacls
foreach ($file in @("dockerInference", "userAnalyticsOtlpHttp.sock")) {
    $fullPath = Join-Path $runDir $file
    & takeown /f $fullPath 2>&1 | Out-Null
    & icacls $fullPath /grant Administrators:F 2>&1 | Out-Null
    & cmd /c "del /f /q `"$fullPath`"" 2>&1
}

Write-Host "Remaining in run dir:"
Get-ChildItem $runDir -ErrorAction SilentlyContinue | Select-Object Name

Remove-Item $emptyDir -Force -Recurse -ErrorAction SilentlyContinue
