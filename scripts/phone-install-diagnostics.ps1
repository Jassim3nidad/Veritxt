param([string]$Adb = (Join-Path $PSScriptRoot 'platform-tools/adb.exe'))
$ErrorActionPreference = 'Stop'
# Read only. -d selects a single physical USB device, never an emulator.
# Do not collect serial numbers, account data, full properties or device logs.
if (-not (Test-Path -LiteralPath $Adb -PathType Leaf)) {
    Write-Output 'STOP: Extract official Platform Tools beside this script so platform-tools/adb.exe exists, or supply -Adb with its full path.'
    exit 1
}
# Suppress native error details: they can contain local paths or transport identifiers.
# Explicit loopback server and -d keep queries on this computer's USB device.
function Read-AdbValue([string[]]$Query) {
    $prior = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try {
        $value = & $Adb -H 127.0.0.1 -P 5037 -d @Query 2>$null
        if ($LASTEXITCODE -ne 0) { return 'unavailable' }
        return (($value -join ' ').Trim())
    } finally { $ErrorActionPreference = $prior }
}
$state = Read-AdbValue @('get-state')
if ($state -ne 'device') {
    Write-Output 'STOP: Need one authorized USB phone. Unlock it, accept the USB-debugging prompt, and disconnect other USB Android devices. If setup blocks this, stop and use official owner verification.'
    exit 1
}
foreach ($property in @('ro.product.model', 'ro.build.version.release', 'ro.build.version.sdk', 'ro.build.version.incremental', 'ro.build.version.security_patch', 'ro.product.cpu.abilist')) {
    $value = Read-AdbValue @('shell', 'getprop', $property)
    if ($value -notmatch '^[A-Za-z0-9._, /()+-]{1,160}$') { $value = 'unavailable' }
    Write-Output "$property=$value"
}
foreach ($setting in @(@('secure', 'secure_frp_mode'), @('secure', 'user_setup_complete'), @('global', 'device_provisioned'))) {
    $value = Read-AdbValue @('shell', 'settings', '--user', '0', 'get', $setting[0], $setting[1])
    if ($value -notin @('0', '1', 'null')) { $value = 'unavailable' }
    Write-Output "$($setting[1])=$value"
}
$packages = Read-AdbValue @('shell', 'pm', 'list', 'packages', 'ph.smishguard.dev')
$presence = if ($packages -eq 'package:ph.smishguard.dev') { 'present' } elseif ($packages -eq '') { 'not found' } else { 'unavailable' }
Write-Output "SmishGuard package presence=$presence"
Write-Output 'Read-only collection complete. No installation or security-setting changes were made.'
