# Build public site from docs (always produce .\site\index.html)
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
  $htmlLines = @(
    "<!doctype html>",
    "<html><head><meta charset=""utf-8""><title>IntelliOptics Docs</title></head>",
    "<body style=""font:16px/1.5 system-ui,Segoe UI,Roboto,Helvetica,Arial"">",
    "<h1>IntelliOptics Documentation</h1>",
    "<p>No generated docs were found in this build. The SDK is present under <code>python-sdk/</code>.</p>",
    "</body></html>"
  )
  $out = Join-Path $site "index.html"
  $htmlLines -join [Environment]::NewLine | Set-Content -Encoding UTF8 -Path $out
  Write-Host "Placeholder written to $out"
}

Write-Host "Site build complete: $site"
exit 0
