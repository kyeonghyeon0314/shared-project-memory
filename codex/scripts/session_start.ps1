$ErrorActionPreference = 'Stop'
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = $OutputEncoding
[Console]::OutputEncoding = $OutputEncoding
$candidates = @()
if ($env:SPM_PYTHON) {
    $candidates += [pscustomobject]@{ Command = $env:SPM_PYTHON; Prefix = @() }
}
$bundled = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
if (Test-Path -LiteralPath $bundled -PathType Leaf) {
    $candidates += [pscustomobject]@{ Command = $bundled; Prefix = @() }
}
foreach ($name in @('python', 'python3', 'py')) {
    $resolved = Get-Command $name -ErrorAction SilentlyContinue
    if ($resolved) {
        $prefix = @()
        if ($name -eq 'py') { $prefix = @('-3') }
        $candidates += [pscustomobject]@{ Command = $resolved.Source; Prefix = $prefix }
    }
}
foreach ($candidate in $candidates) {
    $pythonCommand = $candidate.Command
    $pythonPrefix = $candidate.Prefix
    & $pythonCommand @pythonPrefix -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' 2>$null
    if ($LASTEXITCODE -eq 0) {
        $payload = [Console]::In.ReadToEnd()
        $payload | & $pythonCommand @pythonPrefix (Join-Path $PSScriptRoot 'hook_entry.py') @args
        exit $LASTEXITCODE
    }
}
throw 'Shared Project Memory requires an existing Python 3.11+ interpreter. Set SPM_PYTHON to its executable path. Nothing was installed.'
