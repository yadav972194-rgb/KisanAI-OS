Write-Host "`n=== KisanAI-OS Local Test ===" -ForegroundColor Green

$port = 8000
$project = (Get-Location).Path

Write-Host "`n[1/4] Checking API..." -ForegroundColor Cyan

try {
    $r = Invoke-WebRequest "http://127.0.0.1:$port/docs" -UseBasicParsing -TimeoutSec 5
    Write-Host "API is RUNNING on port $port" -ForegroundColor Green
}
catch {
    Write-Host "API is not running. Starting main.py..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$project'; python main.py"
    Start-Sleep -Seconds 5
}

Write-Host "`n[2/4] Checking API again..." -ForegroundColor Cyan
try {
    $r = Invoke-WebRequest "http://127.0.0.1:$port/docs" -UseBasicParsing -TimeoutSec 5
    Write-Host "API OK" -ForegroundColor Green
}
catch {
    Write-Host "API did not respond on port $port" -ForegroundColor Red
    exit 1
}

Write-Host "`n[3/4] Detecting Wi-Fi IP..." -ForegroundColor Cyan
$ip = Get-NetIPAddress -AddressFamily IPv4 |
    Where-Object {
        $_.IPAddress -like "10.*" -or
        $_.IPAddress -like "192.168.*" -or
        $_.IPAddress -like "172.16.*"
    } |
    Select-Object -First 1 -ExpandProperty IPAddress

Write-Host "PC IP: $ip" -ForegroundColor Green

Write-Host "`n[4/4] Mobile test URL:" -ForegroundColor Cyan
Write-Host "http://$ip`:$port/docs" -ForegroundColor Yellow

Write-Host "`n=== DONE ===" -ForegroundColor Green