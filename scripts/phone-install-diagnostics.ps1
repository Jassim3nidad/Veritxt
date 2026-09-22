param([string]$Adb = "$env:LOCALAPPDATA/Android/Sdk/platform-tools/adb.exe")
$ErrorActionPreference = 'Stop'
# Read only. -d selects a single physical USB device, never an emulator.
# Do not collect serial numbers, account data, full properties or device logs.
$state = & $Adb -d get-state 2>$null
if ($LASTEXITCODE -ne 0 -or $state -ne 'device') {
    throw 'One authorized physical USB device is required. Unlock the phone and accept its USB-debugging prompt; do not bypass setup.'
}
foreach ($property in @('ro.product.model', 'ro.build.version.release', 'ro.build.version.sdk', 'ro.build.version.incremental', 'ro.build.version.security_patch', 'ro.product.cpu.abilist')) {
    $value = & $Adb -d shell getprop $property
    Write-Output "$property=$value"
}
foreach ($setting in @(@('secure', 'secure_frp_mode'), @('secure', 'user_setup_complete'), @('global', 'device_provisioned'))) {
    $value = & $Adb -d shell settings --user 0 get $setting[0] $setting[1]
    Write-Output "$($setting[1])=$value"
}
Write-Output 'SmishGuard package presence (no output means not found for this query):'
& $Adb -d shell pm list packages ph.smishguard.dev
Write-Output 'Read-only collection complete. No installation or security-setting changes were made.'
