$ErrorActionPreference = 'Stop'
Push-Location (Split-Path $PSScriptRoot -Parent)
$priorJavaOptions = $env:JAVA_TOOL_OPTIONS
try {
    $parityRoot = (Resolve-Path -LiteralPath 'research/runs/cashback-review-20261020/parity').Path.Replace('\', '/')
    $env:JAVA_TOOL_OPTIONS = "$priorJavaOptions -Djdk.net.unixdomain.tmpdir=C:/sg-nonexistent-socket-dir".Trim()
    & .\gradlew.bat :app:assembleCashbackReview :app:lintCashbackReview :app:testCashbackReviewUnitTest :app:assembleCashbackReviewAndroidTest "-Psvm60ParityDir=$parityRoot" '-PinstrumentedBuild=cashbackReview' --console=plain
    if ($LASTEXITCODE -ne 0) { throw 'Cashback review build/checks failed.' }
} finally { $env:JAVA_TOOL_OPTIONS = $priorJavaOptions; Pop-Location }
