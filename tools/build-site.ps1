# Build public site from docs (robust / skip if none)
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $PSCommandPath
$repo = Resolve-Path (Join-Path $here '..')
$pub = Join-Path $repo 'public-site'
New-Item -ItemType Directory -Force $pub | Out-Null

# candidate doc roots (any that exist will be copied)
$candidates = @('docs\python-sdk\api-reference-docs',
                'site\python-sdk\api-reference-docs',
                'api-service\IntelliOptics\docs\python-sdk\api-reference-docs',
                'api-service\IntelliOptics\site\python-sdk\api-reference-docs')
$existing = @()
foreach ($rel in $candidates) {
  $p = Join-Path $repo $rel
  if (Test-Path $p) { $existing += $p }
}

if ($existing.Count -eq 0) {
  Write-Host "No docs directories found; skipping site build."
  exit 0
}

function Copy-Robo([string]$src,[string]$dst) {
  New-Item -ItemType Directory -Force $dst | Out-Null
  robocopy $src $dst /E /NFL /NDL /NJH /NJS
  $rc = $LASTEXITCODE
  if ($rc -ge 8) { throw "robocopy failed with exit code $rc from $src" }
}

foreach ($s in $existing) {
  $name = Split-Path $s -Leaf
  $dst = Join-Path $pub $name
  Copy-Robo $s $dst
}

Write-Host "Site build complete: $pub"
exit 0
