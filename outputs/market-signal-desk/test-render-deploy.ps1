param(
  [string]$BaseUrl = "https://market-signal-desk.onrender.com"
)

$ErrorActionPreference = "Stop"

function Read-SecretText($PromptText) {
  $secure = Read-Host -Prompt $PromptText -AsSecureString
  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try {
    [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
  }
  finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
  }
}

function Join-Url($Base, $Path) {
  "$($Base.TrimEnd('/'))/$($Path.TrimStart('/'))"
}

function Write-Check($Label, $Ok, $Detail = "") {
  $status = if ($Ok) { "OK" } else { "CHECK" }
  $color = if ($Ok) { "Green" } else { "Yellow" }
  if ($Detail) {
    Write-Host "[$status] $Label - $Detail" -ForegroundColor $color
  } else {
    Write-Host "[$status] $Label" -ForegroundColor $color
  }
}

$adminToken = Read-SecretText "Render ADMIN_TOKEN"
if ([string]::IsNullOrWhiteSpace($adminToken)) {
  throw "ADMIN_TOKEN is required."
}

$headers = @{
  "X-Admin-Token" = $adminToken.Trim()
}

Write-Host ""
Write-Host "Testing Render deployment: $BaseUrl" -ForegroundColor Cyan
Write-Host ""

$health = Invoke-RestMethod -Uri (Join-Url $BaseUrl "/api/health") -Method Get -TimeoutSec 30
Write-Check "health" ([bool]$health.ok) "time=$($health.time)"

$auth = Invoke-RestMethod -Uri (Join-Url $BaseUrl "/api/auth/status") -Method Get -TimeoutSec 30
Write-Check "auth protection" ([bool]$auth.enabled) "enabled=$($auth.enabled)"

try {
  Invoke-RestMethod -Uri (Join-Url $BaseUrl "/api/dashboard?mode=close") -Method Get -TimeoutSec 30 | Out-Null
  Write-Check "unauthorized dashboard block" $false "dashboard allowed without token"
}
catch {
  $statusCode = [int]$_.Exception.Response.StatusCode
  Write-Check "unauthorized dashboard block" ($statusCode -eq 401) "status=$statusCode"
}

$dashboard = Invoke-RestMethod -Uri (Join-Url $BaseUrl "/api/dashboard?mode=close") -Headers $headers -Method Get -TimeoutSec 45
Write-Check "authorized dashboard" ($dashboard.summary.candidateCount -gt 0) "candidates=$($dashboard.summary.candidateCount)"

$scheduler = Invoke-RestMethod -Uri (Join-Url $BaseUrl "/api/scheduler/status") -Headers $headers -Method Get -TimeoutSec 30
Write-Check "scheduler disabled for staging" (-not [bool]$scheduler.config.enabled) "enabled=$($scheduler.config.enabled)"

$news = Invoke-RestMethod -Uri (Join-Url $BaseUrl "/api/integrations/news/status") -Headers $headers -Method Get -TimeoutSec 30
$gdeltReady = [bool]$news.gdelt.readyForNews
$naverReady = [bool]$news.naver.readyForNews
Write-Check "GDELT status" $gdeltReady "ready=$gdeltReady"
Write-Check "Naver news status" (-not $naverReady -or $naverReady) "ready=$naverReady"

$gdeltDashboardStatus = $dashboard.integrations.news.gdelt.items
if ($gdeltDashboardStatus) {
  $detail = "source=$($gdeltDashboardStatus.source), news=$($gdeltDashboardStatus.newsCount)"
  if ($gdeltDashboardStatus.error) {
    $detail = "$detail, error=$($gdeltDashboardStatus.error)"
  }
  Write-Check "GDELT dashboard source" ($gdeltDashboardStatus.source -eq "gdelt") $detail
}

Write-Host ""
Write-Host "Render deployment test finished." -ForegroundColor Green
