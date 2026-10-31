param([string]$ParityDir = 'research/runs/multiclass-android-20261020/export-v2')
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
$priorJavaOptions = $env:JAVA_TOOL_OPTIONS
try {
    $parityRoot = (Resolve-Path -LiteralPath $ParityDir).Path.Replace('\', '/')
    $env:JAVA_TOOL_OPTIONS = "$priorJavaOptions -Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir".Trim()
    & .\gradlew.bat :app:assembleMulticlassSvm :app:lintMulticlassSvm :app:testMulticlassSvmUnitTest :app:assembleMulticlassSvmAndroidTest "-PmulticlassParityDir=$parityRoot" '-PinstrumentedBuild=multiclassSvm' --console=plain
    if ($LASTEXITCODE -ne 0) { throw 'Multiclass SVM build, lint or tests failed.' }
} finally {
    $env:JAVA_TOOL_OPTIONS = $priorJavaOptions
    Pop-Location
}
