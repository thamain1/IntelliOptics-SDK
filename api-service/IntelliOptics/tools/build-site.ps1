param()

# Paths
$Root = Resolve-Path "$PSScriptRoot\.."
$Docs = Join-Path $Root "docs"
$Site = Join-Path $Root "site"
$SdkSrc = Join-Path $Docs "python-sdk\api-reference-docs"
$SdkDst = Join-Path $Site "python-sdk\api-reference-docs"

# Clean site/
if (Test-Path $Site) { Remove-Item $Site -Recurse -Force }
New-Item -ItemType Directory $Site | Out-Null

# Copy SDK docs only (robocopy exit codes < 8 are success)
robocopy $SdkSrc $SdkDst /MIR /R:0 /W:0 | Out-Null
$rc = $LASTEXITCODE
if ($rc -ge 8) { throw "robocopy failed with exit code $rc" } else { Write-Host "robocopy exit code $rc (OK)" }
$global:LASTEXITCODE = 0  # avoid propagating non-zero to the runner

# Redirect index.html and 404.html to SDK home
$Redirect = @"
<!doctype html>
<meta charset='utf-8'>
<meta http-equiv='refresh' content='0; url=python-sdk/api-reference-docs/index.html'>
<script>location.replace('python-sdk/api-reference-docs/index.html');</script>
<p><a href='python-sdk/api-reference-docs/index.html'>Go to IntelliOptics Python SDK docs</a></p>
"@

$IndexPath = Join-Path $Site "index.html"
$ErrorPath = Join-Path $Site "404.html"
$Redirect | Out-File -Encoding utf8 $IndexPath
$Redirect | Out-File -Encoding utf8 $ErrorPath

if (!(Test-Path $IndexPath)) { throw "site/ was not generated." }

Write-Host "✅ site/ rebuilt from docs/ (SDK as landing page)"
$global:LASTEXITCODE = 0
