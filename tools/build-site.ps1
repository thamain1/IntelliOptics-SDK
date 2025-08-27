# Build public site from docs (always produce .\site\index.html)
$ErrorActionPreference = "Stop"

$here = Split-Path -Parent $PSCommandPath
$repo = Resolve-Path (Join-Path $here "..")
$site = Join-Path $repo "site"
New-Item -ItemType Directory -Force -Path $site | Out-Null

# Candidate doc roots
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

function Copy-Robo($src, $dst) {
  New-Item -ItemType Directory -Force -Path $dst | Out-Null
  robocopy $src $dst /E /NFL /NDL /NJH /NJS | Out-Null
  if ($LASTEXITCODE -ge 8) { throw ("robocopy failed with exit code " + $LASTEXITCODE + " from " + $src) }
}

if ($existing -ne $null) {
  Write-Host ("Docs found at: " + $existing + " copying into " + $site)
  Copy-Robo $existing $site
} else {
  Write-Host "No docs directories found; writing placeholder site."
  $out = Join-Path $site "index.html"
  $content = "IntelliOptics docs placeholder. No generated docs in this build. SDK under python-sdk/."
  Set-Content -Encoding UTF8 -Path $out -Value $content
  Write-Host ("Placeholder written to " + $out)
}

Write-Host ("Site build complete: " + $site)
exit 0
