Get-Process -Name Service_name -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        $_.Kill()
    } catch {
        Write-Host "Failed to terminate process: $($_.Name) (ID: $($_.Id)) - $($_.Exception.Message)"
    }
}
