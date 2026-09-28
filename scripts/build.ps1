param([switch]$ConnectedTests, [switch]$EmulatorTests, [ValidateSet("debug", "development", "lr", "nb", "svm")][string]$Variant = "debug", [string]$ModelParityDir)
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    # Work around a host Java AF_UNIX loopback failure without changing system settings.
    # The path is intentionally nonexistent so Java falls back to TCP for its NIO pipe.
    $priorJavaOptions = $env:JAVA_TOOL_OPTIONS
    $env:JAVA_TOOL_OPTIONS = "$priorJavaOptions -Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir".Trim()
    $variantTask = (Get-Culture).TextInfo.ToTitleCase($Variant)
    $gradleOptions = @("-PinstrumentedBuild=$Variant", '--console=plain')
    if ($ModelParityDir) { $gradleOptions += "-PmodelParityDir=$ModelParityDir" }
    & .\gradlew.bat ":app:assemble$variantTask" ":app:lint$variantTask" ":app:test${variantTask}UnitTest" @gradleOptions
    if ($LASTEXITCODE -ne 0) { throw 'Android build/checks failed.' }
    if ($ConnectedTests) {
        & .\gradlew.bat ":app:connected${variantTask}AndroidTest" @gradleOptions
        if ($LASTEXITCODE -ne 0) { throw 'Connected Android tests failed.' }
    }
    if ($EmulatorTests) {
        if ($Variant -notin @('debug', 'development', 'lr')) { throw 'Use connected tests for new research models; specialized verifier supports the existing historical LR only.' }
        & .\gradlew.bat ":app:assemble${variantTask}AndroidTest" @gradleOptions
        if ($LASTEXITCODE -ne 0) { throw 'Android test APK build failed.' }
        & research\.venv\Scripts\python.exe scripts\emulator_verify.py --variant $Variant
        if ($LASTEXITCODE -ne 0) { throw 'Emulator verification failed.' }
    }
} finally {
    $env:JAVA_TOOL_OPTIONS = $priorJavaOptions
    Pop-Location
}
