param()

# Rebuild site/ from docs/ (public subset only)
$Root = Resolve-Path "$PSScriptRoot\.."
$Docs = Join-Path $Root "docs"
$Site = Join-Path $Root "site"
$SdkSrc = Join-Path $Docs "python-sdk\api-reference-docs"
$SdkDst = Join-Path $Site "python-sdk\api-reference-docs"

# Clean site/
if (Test-Path $Site) { Remove-Item $Site -Recurse -Force }
New-Item -ItemType Directory $Site | Out-Null

# Copy SDK docs only
robocopy $SdkSrc $SdkDst /MIR | Out-Null

# Redirect index.html and 404.html to SDK home
$Redirect = @"
<!doctype html>
<meta charset='utf-8'>
<meta http-equiv='refresh' content='0; url=python-sdk/api-reference-docs/index.html'>
<script>location.replace('python-sdk/api-reference-docs/index.html');</script>
<p><a href='python-sdk/api-reference-docs/index.html'>Go to IntelliOptics Python SDK docs</a></p>
"@

$IndexPath = Join-Path $Site "index.html"
$ErrorPath  = Join-Path $Site "404.html"
$Redirect | Out-File -Encoding utf8 $IndexPath
$Redirect | Out-File -Encoding utf8 $ErrorPath

Write-Host "✅ site/ rebuilt from docs/ (SDK as landing page)"
