$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
$priorJavaOptions = $env:JAVA_TOOL_OPTIONS
try {
    $parityRoot = (Resolve-Path -LiteralPath 'research/runs/old-binary-svm-20261020/parity').Path.Replace('\', '/')
    $env:JAVA_TOOL_OPTIONS = "$priorJavaOptions -Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir".Trim()
    & .\gradlew.bat :app:assembleOldSvm :app:lintOldSvm :app:testOldSvmUnitTest :app:assembleOldSvmAndroidTest "-PmodelParityDir=$parityRoot" "-PoldSvmParityDir=$parityRoot" '-PinstrumentedBuild=oldSvm' --console=plain
    if ($LASTEXITCODE -ne 0) { throw 'Old binary SVM build/checks failed.' }
} finally { $env:JAVA_TOOL_OPTIONS = $priorJavaOptions; Pop-Location }
