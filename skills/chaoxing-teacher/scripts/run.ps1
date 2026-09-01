$ErrorActionPreference = "Stop"

$scriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$bundledPython = Join-Path $scriptDirectory "runtime\python-win-x64\python.exe"
$runner = Join-Path $scriptDirectory "chaoxing_teacher.py"

if (-not (Test-Path -LiteralPath $bundledPython)) {
    [Console]::Error.WriteLine('{"status":"error","message":"Skill package is incomplete: bundled runtime is missing."}')
    exit 1
}

& $bundledPython -B -S $runner @args
exit $LASTEXITCODE
