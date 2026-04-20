# fix-wsl-ports.ps1
# ==============================================================================
# Run this script ONCE as Administrator to forward WSL2 Docker ports to Windows.
# Right-click this file → "Run with PowerShell as Administrator"
# ==============================================================================

$wslIp = (wsl hostname -I).Trim().Split(' ')[0]
Write-Host "WSL2 IP detected: $wslIp" -ForegroundColor Cyan

$ports = @(
    @{ Host = 3005; Name = "Frontend (Next.js)" },
    @{ Host = 8005; Name = "Backend (FastAPI)" },
    @{ Host = 6380; Name = "Redis" }
)

foreach ($p in $ports) {
    # Remove existing proxy if any
    netsh interface portproxy delete v4tov4 listenport=$($p.Host) listenaddress=127.0.0.1 2>$null

    # Add new proxy
    netsh interface portproxy add v4tov4 `
        listenport=$($p.Host) `
        listenaddress=127.0.0.1 `
        connectport=$($p.Host) `
        connectaddress=$wslIp

    Write-Host "✓ Proxied localhost:$($p.Host) → WSL($wslIp):$($p.Host)  ($($p.Name))" -ForegroundColor Green
}

# Add Windows Firewall rule to allow the ports in (in case Firewall blocks WSL traffic)
$ruleName = "WSL2-CRM-Project"
netsh advfirewall firewall delete rule name=$ruleName 2>$null
netsh advfirewall firewall add rule `
    name=$ruleName `
    dir=in `
    action=allow `
    protocol=TCP `
    localport=3005,8005,6380

Write-Host ""
Write-Host "✓ Firewall rule added for ports 3005, 8005, 6380" -ForegroundColor Green
Write-Host ""
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "  All done! Open these URLs in your browser:" -ForegroundColor Yellow
Write-Host "  Frontend:  http://localhost:3005" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8005/docs" -ForegroundColor White
Write-Host "  Health:    http://localhost:8005/health" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "NOTE: If WSL restarts, the IP may change. Re-run this script." -ForegroundColor DarkGray

# Verify by showing what's listening
Write-Host ""
Write-Host "Current port proxy rules:" -ForegroundColor Cyan
netsh interface portproxy show v4tov4
