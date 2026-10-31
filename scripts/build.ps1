param([switch]$ConnectedTests, [switch]$EmulatorTests, [ValidateSet("debug", "development", "selectedSvm", "nbGeneralization", "lr", "lrCandidate", "lrCalibrated4", "nb", "svm", "mbert", "mbertQuantized")][string]$Variant = "debug", [string]$ModelParityDir, [string]$FoldedParityDir, [string]$MbertParityDir, [string]$NbParityDir)
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
try {
    # Work around a host Java AF_UNIX loopback failure without changing system settings.
    # The path is intentionally nonexistent so Java falls back to TCP for its NIO pipe.
    $priorJavaOptions = $env:JAVA_TOOL_OPTIONS
    $env:JAVA_TOOL_OPTIONS = "$priorJavaOptions -Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir".Trim()
    $variantTask = $Variant.Substring(0, 1).ToUpperInvariant() + $Variant.Substring(1)
    $gradleOptions = @("-PinstrumentedBuild=$Variant", '--console=plain')
    if ($NbParityDir) { $gradleOptions += "-PnbParityDir=$NbParityDir" }
    if ($ModelParityDir) { $gradleOptions += "-PmodelParityDir=$ModelParityDir" }
    if ($FoldedParityDir) { $gradleOptions += "-PfoldedParityDir=$FoldedParityDir" }
    if ($MbertParityDir) { $gradleOptions += "-PmbertParityDir=$MbertParityDir" }
    if ($EmulatorTests -and $Variant -in @('mbert', 'mbertQuantized') -and -not $MbertParityDir) {
        throw 'mBERT emulator verification requires its private actual-model parity directory.'
    }
    if ($EmulatorTests -and $Variant -eq 'lrCalibrated4' -and -not $FoldedParityDir) {
        throw 'LR4 emulator verification requires -FoldedParityDir pointing to the private parity output.'
    }
    if ($EmulatorTests -and $Variant -eq 'selectedSvm' -and -not $ModelParityDir) {
        throw 'Selected SVM emulator checks require -ModelParityDir pointing to the private raw-SMS parity fixtures.'
    }
    if ($EmulatorTests -and $Variant -eq 'nbGeneralization' -and -not $NbParityDir) {
        throw 'Retrained NB emulator checks require -NbParityDir pointing to the frozen private fixtures.'
    }
    & .\gradlew.bat ":app:assemble$variantTask" ":app:lint$variantTask" ":app:test${variantTask}UnitTest" @gradleOptions
    if ($LASTEXITCODE -ne 0) { throw 'Android build/checks failed.' }
    if ($ConnectedTests) {
        & .\gradlew.bat ":app:connected${variantTask}AndroidTest" @gradleOptions
        if ($LASTEXITCODE -ne 0) { throw 'Connected Android tests failed.' }
    }
    if ($EmulatorTests) {
        if ($Variant -notin @('debug', 'development', 'selectedSvm', 'nbGeneralization', 'lr', 'nb', 'svm', 'lrCalibrated4', 'mbert', 'mbertQuantized')) { throw 'Use connected tests for other model variants; this verifier has no corresponding private parity setup.' }
        & .\gradlew.bat ":app:assemble${variantTask}AndroidTest" @gradleOptions
        if ($LASTEXITCODE -ne 0) { throw 'Android test APK build failed.' }
        if ($Variant -in @('mbert', 'mbertQuantized')) {
            & research\.venv\Scripts\python.exe scripts\emulator_verify.py --variant $Variant --output "$MbertParityDir/emulator-results.json"
        } else {
            & research\.venv\Scripts\python.exe scripts\emulator_verify.py --variant $Variant
        }
        if ($LASTEXITCODE -ne 0) { throw 'Emulator verification failed.' }
    }
} finally {
    $env:JAVA_TOOL_OPTIONS = $priorJavaOptions
    Pop-Location
}
