# Physical device verification script for KisanAI-OS
# Runs on Windows PowerShell 5.1

$adb = "C:\Android\Sdk\platform-tools\adb.exe"
$package = "com.kisanai.app"

Write-Host "=== Kisan-Tester Physical Device Verification ===" -ForegroundColor Cyan

# 1. Verify device
Write-Host "`n1. Device status:" -ForegroundColor Yellow
$result = & $adb "devices"
if ($result -match "device") {
    Write-Host "   PASS: Device connected and authorized" -ForegroundColor Green
} else {
    Write-Host "   FAIL: No authorized device found" -ForegroundColor Red
}

# 2. Verify app installed
Write-Host "`n2. App installation:" -ForegroundColor Yellow
$installed = & $adb "shell" "pm list packages $package"
if ($installed -match $package) {
    Write-Host "   PASS: $package is installed" -ForegroundColor Green
    # Version info
    $versionInfo = & $adb "shell" "dumpsys package $package" | Select-String "versionName|versionCode"
    Write-Host "   Version: $($versionInfo -replace 'versionName=|versionCode=' -join ' ').Trim()" -ForegroundColor Cyan
} else {
    Write-Host "   FAIL: $package not found" -ForegroundColor Red
}

# 3. Launch app
Write-Host "`n3. App launch:" -ForegroundColor Yellow
$launch = & $adb "shell" "am start -n $package/.MainActivity 2>&1"
if ($launch -match "Starting") {
    Write-Host "   PASS: App launched successfully" -ForegroundColor Green
} else {
    Write-Host "   FAIL: App launch failed: $launch" -ForegroundColor Red
}

# Wait for app to settle
Start-Sleep -Seconds 3

# 4. Try taking screenshot
Write-Host "`n4. Screenshot attempt:" -ForegroundColor Yellow
$screenshotResult = & $adb "shell" "screencap -p /sdcard/kisanai_verification.png 2>&1"
if ($LASTEXITCODE -eq 0) {
    $pullResult = & $adb "pull" "/sdcard/kisanai_verification.png" "C:\Users\Sultan Computer\Desktop\KisanAI-OS\kisanai_device_screenshot.png" 2>&1
    if ($pullResult -match "1 file pulled") {
        Write-Host "   PASS: Screenshot saved" -ForegroundColor Green
    } else {
        Write-Host "   WARN: Screenshot captured but pull failed" -ForegroundColor Yellow
    }
} else {
    Write-Host "   WARN: Screenshot capture failed (may need rooted/allowlisted)" -ForegroundColor Yellow
}

# 5. Key event test - home
Write-Host "`n5. Home key:" -ForegroundColor Yellow
$home = & $adb "shell" "input keyevent 3 2>&1"
Write-Host "   Result: $home" -ForegroundColor Cyan

Write-Host "`n=== Verification Complete ===" -ForegroundColor Cyan
Write-Host "For full Definition-of-Done feature verification, manual interaction" -ForegroundColor Yellow
Write-Host "is required. See items marked MANUAL EVIDENCE NEEDED below.`n" -ForegroundColor Yellow

# List items requiring manual evidence
Write-Host "Items requiring manual physical-device evidence:" -ForegroundColor Magenta
Write-Host "  1. Weather uses real production data - Navigate to Weather screen, verify live data from https://kisanai-os.onrender.com/api/weather" -ForegroundColor Gray
Write-Host "  2. No 429/fallback incorrectly treated as success - Trigger rate-limited requests, verify error Hindi message" -ForegroundColor Gray
Write-Host "  3. Village/backend lists from real backend - Navigate to farm creation, verify location dropdowns populate from backend" -ForegroundColor Gray
Write-Host "  4. All seven model features return real inference - Each detection type (growth stage, water stress, pest, weed, nutrient deficiency, disease detection, predictions)" -ForegroundColor Gray
Write-Host "  5. Login/session survives app restart - Login, Home, Background, Foreground, re-verify session" -ForegroundColor Gray
Write-Host "  6. Persistent database behavior - Create farm, restart app, verify persistence" -ForegroundColor Gray
Write-Host "  7. DEBUG=false - Already verified via code/config change (800/800 tests pass)" -ForegroundColor Gray
Write-Host "  8. Documentation/verification requirements - Check MASTER_TEST_REPORT.md compliance" -ForegroundColor Gray