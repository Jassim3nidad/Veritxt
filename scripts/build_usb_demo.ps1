param([switch]$TestApk)
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
$priorJavaOptions = $env:JAVA_TOOL_OPTIONS
try {
    $env:JAVA_TOOL_OPTIONS = "$priorJavaOptions -Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir".Trim()
    $tasks = @(':app:assembleUsbDemo', ':app:lintUsbDemo', ':app:testUsbDemoUnitTest')
    $options = @('-PinstrumentedBuild=usbDemo', '--console=plain')
    if ($TestApk) {
        $parityRoot = (Resolve-Path -LiteralPath 'research/runs/old-binary-svm-20261020/parity').Path.Replace('\', '/')
        $tasks += ':app:assembleUsbDemoAndroidTest'
        $options += "-PoldSvmParityDir=$parityRoot"
    }
    & .\gradlew.bat @tasks @options
    if ($LASTEXITCODE -ne 0) { throw 'USB demo build/checks failed.' }
} finally { $env:JAVA_TOOL_OPTIONS = $priorJavaOptions; Pop-Location }
