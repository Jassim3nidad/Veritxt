param(
    [string]$Serial,
    [switch]$Install,
    [string]$ApkPath = (Join-Path $PSScriptRoot 'Veritxt-USB-Demo.apk'),
    [string]$Message,
    [string]$CasesPath = (Join-Path $PSScriptRoot 'usb-demo-messages.json'),
    [ValidateRange(0, 60)][int]$DelaySeconds = 4
)
$ErrorActionPreference = 'Stop'
$adbCommand = Get-Command adb -ErrorAction SilentlyContinue
if ($adbCommand) { $adbPath = $adbCommand.Source }
else {
    $adbPath = Join-Path $env:LOCALAPPDATA 'Android/Sdk/platform-tools/adb.exe'
    if (-not (Test-Path -LiteralPath $adbPath)) { throw 'Install Android SDK Platform-Tools and add adb to PATH before the defense.' }
}
if (-not $Serial) {
    $devices = @(& $adbPath devices | Where-Object { $_ -match '^\S+\s+device$' } | ForEach-Object { ($_ -split '\s+')[0] })
    if ($devices.Count -ne 1) { throw 'Connect and authorize exactly one phone, or pass -Serial from adb devices.' }
    $Serial = $devices[0]
}
if ($Serial -notmatch '^[A-Za-z0-9._:-]+$') { throw 'Invalid ADB serial.' }
$package = 'ph.smishguard.demo.usb'
function Invoke-DemoAdb {
    param([string[]]$AdbArguments)
    $result = & $adbPath -s $Serial @AdbArguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw ($result -join "`n") }
    return ($result -join "`n")
}
if ($Install) {
    if (-not (Test-Path -LiteralPath $ApkPath)) { throw "Demo APK not found: $ApkPath" }
    Invoke-DemoAdb -AdbArguments @('install', '-r', (Resolve-Path -LiteralPath $ApkPath).Path) | Write-Host
    $api = [int](Invoke-DemoAdb -AdbArguments @('shell', 'getprop', 'ro.build.version.sdk'))
    if ($api -ge 33) {
        Invoke-DemoAdb -AdbArguments @('shell', 'pm', 'grant', $package, 'android.permission.POST_NOTIFICATIONS') | Out-Null
    }
    Invoke-DemoAdb -AdbArguments @('shell', 'am', 'start', '-W', '-n', "$package/ph.smishguard.MainActivity") | Out-Null
    Write-Host 'Setup: accept the privacy notice and finish onboarding on the phone. Incoming SMS can stay OFF.'
    Write-Host 'Then rerun this script without -Install to send fictional samples. Unlock the phone to see reports.'
    return
}
if ($PSBoundParameters.ContainsKey('Message')) {
    $cases = @([pscustomobject]@{ id = 'custom'; text = $Message })
} else {
    # Assign the JSON array directly: Windows PowerShell 5.1 does not enumerate
    # ConvertFrom-Json's array on the pipeline as PowerShell 7 does.
    $cases = Get-Content -LiteralPath $CasesPath -Raw -Encoding UTF8 | ConvertFrom-Json
}
if ($cases.Count -eq 0) { throw 'No fictional samples provided.' }
foreach ($case in $cases) {
    $text = [string]$case.text
    if ([string]::IsNullOrWhiteSpace($text) -or $text.Length -gt 10000) { throw 'Each message must contain 1 to 10000 characters.' }
    # Base64 avoids shell metacharacters and preserves Unicode/newlines. Fictional messages only:
    # ADB is a developer transport; Android/shell tools can observe the submitted input.
    $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($text))
    Write-Host ("Sending fictional sample: " + $case.id)
    $result = Invoke-DemoAdb -AdbArguments @('shell', 'am', 'broadcast', '--include-stopped-packages', '-n',
        "$package/ph.smishguard.demo.UsbDemoReceiver", '-a', 'ph.smishguard.action.USB_DEMO_MESSAGE',
        '--es', 'message_base64', $encoded)
    if ($result -notmatch 'result=-1\b' -or $result -notmatch 'Demo report posted') { throw $result }
    Write-Host 'Demo report posted. Read the actual model category and risk result on the phone.'
    if ($DelaySeconds) { Start-Sleep -Seconds $DelaySeconds }
}
