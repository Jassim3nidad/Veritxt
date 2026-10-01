param([switch]$ConnectedTests, [switch]$EmulatorTests, [ValidateSet("debug", "development", "lr", "lrCandidate", "lrCalibrated4", "nb", "svm")][string]$Variant = "debug", [string]$ModelParityDir, [string]$FoldedParityDir)
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    # Work around a host Java AF_UNIX loopback failure without changing system settings.
    # The path is intentionally nonexistent so Java falls back to TCP for its NIO pipe.
    $priorJavaOptions = $env:JAVA_TOOL_OPTIONS
    $env:JAVA_TOOL_OPTIONS = "$priorJavaOptions -Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir".Trim()
    $variantTask = $Variant.Substring(0, 1).ToUpperInvariant() + $Variant.Substring(1)
    $gradleOptions = @("-PinstrumentedBuild=$Variant", '--console=plain')
    if ($ModelParityDir) { $gradleOptions += "-PmodelParityDir=$ModelParityDir" }
    if ($FoldedParityDir) { $gradleOptions += "-PfoldedParityDir=$FoldedParityDir" }
    if ($EmulatorTests -and $Variant -eq 'lrCalibrated4' -and -not $FoldedParityDir) {
        throw 'LR4 emulator verification requires -FoldedParityDir pointing to the private parity output.'
    }
    & .\gradlew.bat ":app:assemble$variantTask" ":app:lint$variantTask" ":app:test${variantTask}UnitTest" @gradleOptions
    if ($LASTEXITCODE -ne 0) { throw 'Android build/checks failed.' }
    if ($ConnectedTests) {
        & .\gradlew.bat ":app:connected${variantTask}AndroidTest" @gradleOptions
        if ($LASTEXITCODE -ne 0) { throw 'Connected Android tests failed.' }
    }
    if ($EmulatorTests) {
        if ($Variant -notin @('debug', 'development', 'lr', 'lrCalibrated4')) { throw 'Use connected tests for other model variants; this verifier has no corresponding private parity setup.' }
        & .\gradlew.bat ":app:assemble${variantTask}AndroidTest" @gradleOptions
        if ($LASTEXITCODE -ne 0) { throw 'Android test APK build failed.' }
        & research\.venv\Scripts\python.exe scripts\emulator_verify.py --variant $Variant
        if ($LASTEXITCODE -ne 0) { throw 'Emulator verification failed.' }
    }
} finally {
    $env:JAVA_TOOL_OPTIONS = $priorJavaOptions
    Pop-Location
}
