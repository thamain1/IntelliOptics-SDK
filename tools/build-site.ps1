# Build public site from docs (always produce .\site\index.html, no angle brackets)
$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $PSCommandPath
$repo = Resolve-Path (Join-Path $here "..")
$site = Join-Path $repo "site"
New-Item -ItemType Directory -Force -Path $site | Out-Null

# Candidate Sphinx build roots
$candidates = @(
  "docs\python-sdk\api-reference-docs",
  "site\python-sdk\api-reference-docs",
  "api-service\IntelliOptics\docs\python-sdk\api-reference-docs",
  "api-service\IntelliOptics\site\python-sdk\api-reference-docs"
)

$existing = $null
foreach ($rel in $candidates) {
  $p = Join-Path $repo $rel
  if (Test-Path -Path $p) { $existing = $p; break }
}

function Copy-Robo([string]$src, [string]$dst) {
  New-Item -ItemType Directory -Force -Path $dst | Out-Null
  robocopy $src $dst /E /NFL /NDL /NJH /NJS | Out-Null
  $rc = $LASTEXITCODE
  if ($rc -ge 8) { throw "robocopy failed with exit code $rc from $src" }
}

if ($existing) {
  Write-Host "Docs found at: $existing — copying into $site"
  Copy-Robo -src $existing -dst $site
} else {
  Write-Host "No docs directories found; emitting placeholder site."
  $out = Join-Path $site "index.html"
  $content = "IntelliOptics documentation placeholder. No generated docs were found in this build. The SDK lives under python-sdk/."
  Set-Content -Encoding UTF8 -Path $out -Value $content
  Write-Host "Placeholder written to $out"
}

Write-Host "Site build complete: $site"
exit 0
