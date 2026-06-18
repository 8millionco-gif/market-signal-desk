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

function Format-ApiError($ErrorRecord) {
  $message = $ErrorRecord.Exception.Message
  $body = $ErrorRecord.ErrorDetails.Message
  if ($body) {
    try {
      $payload = $body | ConvertFrom-Json
      $parts = @()
      if ($payload.status) { $parts += "status=$($payload.status)" }
      if ($payload.error) { $parts += "error=$($payload.error)" }
      if ($payload.message) { $parts += "message=$($payload.message)" }
      if ($payload.detail) { $parts += "detail=$($payload.detail)" }
      if ($parts.Count -gt 0) {
        return ($parts -join ", ")
      }
    } catch {
      return $body
    }
  }
  return $message
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

$toss = Invoke-RestMethod -Uri (Join-Url $BaseUrl "/api/integrations/toss/status") -Headers $headers -Method Get -TimeoutSec 30
$tossReady = [bool]$toss.readyForMarketData
Write-Check "Toss status" $tossReady "ready=$tossReady, prices=$($toss.livePricesEnabled), candles=$($toss.liveCandlesEnabled), orderbook=$($toss.liveOrderbookEnabled), trades=$($toss.liveTradesEnabled)"

$dart = Invoke-RestMethod -Uri (Join-Url $BaseUrl "/api/integrations/dart/status") -Headers $headers -Method Get -TimeoutSec 30
$dartReady = [bool]$dart.readyForDisclosures
Write-Check "OpenDART status" $dartReady "ready=$dartReady, cache=$($dart.corpCodeCacheExists)"

$news = Invoke-RestMethod -Uri (Join-Url $BaseUrl "/api/integrations/news/status") -Headers $headers -Method Get -TimeoutSec 30
$gdeltReady = [bool]$news.gdelt.readyForNews
$naverReady = [bool]$news.naver.readyForNews
Write-Check "GDELT status" $gdeltReady "ready=$gdeltReady"
Write-Check "Naver news status" $naverReady "ready=$naverReady"

$openai = Invoke-RestMethod -Uri (Join-Url $BaseUrl "/api/integrations/openai/status") -Headers $headers -Method Get -TimeoutSec 30
$openaiReady = [bool]$openai.readyForAnalysis
Write-Check "OpenAI status" $openaiReady "ready=$openaiReady, model=$($openai.model)"

$gdeltDashboardStatus = $dashboard.integrations.news.gdelt.items
if ($gdeltDashboardStatus) {
  $detail = "source=$($gdeltDashboardStatus.source), news=$($gdeltDashboardStatus.newsCount)"
  if ($gdeltDashboardStatus.error) {
    $detail = "$detail, error=$($gdeltDashboardStatus.error)"
  }
  Write-Check "GDELT dashboard source" ($gdeltDashboardStatus.source -eq "gdelt") $detail
}

$naverDashboardStatus = $dashboard.integrations.news.naver.items
if ($naverDashboardStatus) {
  $detail = "source=$($naverDashboardStatus.source), news=$($naverDashboardStatus.newsCount)"
  if ($naverDashboardStatus.error) {
    $detail = "$detail, error=$($naverDashboardStatus.error)"
  }
  Write-Check "Naver dashboard source" ($naverDashboardStatus.source -eq "naver") $detail
}

if ($naverReady) {
  $naverSearch = Invoke-RestMethod -Uri (Join-Url $BaseUrl "/api/integrations/news/search?query=%EC%82%BC%EC%84%B1%EC%A0%84%EC%9E%90&display=3&sort=date") -Headers $headers -Method Get -TimeoutSec 30
  Write-Check "Naver search API" (($naverSearch.items | Measure-Object).Count -gt 0) "items=$(($naverSearch.items | Measure-Object).Count)"
} else {
  Write-Check "Naver search API" $false "waiting for NAVER_CLIENT_ID/SECRET and NAVER_LIVE_NEWS=1"
}

$tossPriceStatus = $dashboard.integrations.toss.prices
if ($tossPriceStatus) {
  $detail = "source=$($tossPriceStatus.source), prices=$($tossPriceStatus.priceCount)"
  if ($tossPriceStatus.error) {
    $detail = "$detail, status=$($tossPriceStatus.status), error=$($tossPriceStatus.error), detail=$($tossPriceStatus.detail)"
  }
  Write-Check "Toss dashboard prices" ($tossPriceStatus.source -eq "toss") $detail
}

$tossCandleStatus = $dashboard.integrations.toss.candles
if ($tossCandleStatus) {
  $detail = "source=$($tossCandleStatus.source), candles=$($tossCandleStatus.candleCount), stale=$($tossCandleStatus.staleCount)"
  if ($tossCandleStatus.error) {
    $detail = "$detail, status=$($tossCandleStatus.status), error=$($tossCandleStatus.error), detail=$($tossCandleStatus.detail)"
  }
  Write-Check "Toss dashboard candles" ($tossCandleStatus.source -eq "toss") $detail
}

$tossOrderbookStatus = $dashboard.integrations.toss.orderbook
if ($tossOrderbookStatus) {
  $detail = "source=$($tossOrderbookStatus.source), orderbooks=$($tossOrderbookStatus.orderbookCount)"
  if ($tossOrderbookStatus.error) {
    $detail = "$detail, status=$($tossOrderbookStatus.status), error=$($tossOrderbookStatus.error), detail=$($tossOrderbookStatus.detail)"
  }
  Write-Check "Toss dashboard orderbook" ($tossOrderbookStatus.source -eq "toss") $detail
}

$tossTradesStatus = $dashboard.integrations.toss.trades
if ($tossTradesStatus) {
  $detail = "source=$($tossTradesStatus.source), trades=$($tossTradesStatus.tradeCount)"
  if ($tossTradesStatus.error) {
    $detail = "$detail, status=$($tossTradesStatus.status), error=$($tossTradesStatus.error), detail=$($tossTradesStatus.detail)"
  }
  Write-Check "Toss dashboard trades" ($tossTradesStatus.source -eq "toss") $detail
}

if ($tossReady) {
  try {
    $prices = Invoke-RestMethod -Uri (Join-Url $BaseUrl "/api/integrations/toss/prices?symbols=005930") -Headers $headers -Method Get -TimeoutSec 45
    Write-Check "Toss prices API" (($prices.result | Measure-Object).Count -gt 0) "items=$(($prices.result | Measure-Object).Count)"
  } catch {
    Write-Check "Toss prices API" $false (Format-ApiError $_)
  }
  try {
    $candles = Invoke-RestMethod -Uri (Join-Url $BaseUrl "/api/integrations/toss/candles?symbol=005930&interval=1d&count=5") -Headers $headers -Method Get -TimeoutSec 45
    Write-Check "Toss candles API" (($candles.result.candles | Measure-Object).Count -gt 0) "items=$(($candles.result.candles | Measure-Object).Count)"
  } catch {
    Write-Check "Toss candles API" $false (Format-ApiError $_)
  }
  try {
    $orderbook = Invoke-RestMethod -Uri (Join-Url $BaseUrl "/api/integrations/toss/orderbook?symbol=005930") -Headers $headers -Method Get -TimeoutSec 45
    Write-Check "Toss orderbook API" ($null -ne $orderbook.result) "symbol=005930"
  } catch {
    Write-Check "Toss orderbook API" $false (Format-ApiError $_)
  }
  try {
    $trades = Invoke-RestMethod -Uri (Join-Url $BaseUrl "/api/integrations/toss/trades?symbol=005930&count=5") -Headers $headers -Method Get -TimeoutSec 45
    Write-Check "Toss trades API" (($trades.result | Measure-Object).Count -gt 0) "items=$(($trades.result | Measure-Object).Count)"
  } catch {
    Write-Check "Toss trades API" $false (Format-ApiError $_)
  }
} else {
  Write-Check "Toss prices API" $false "waiting for TOSS_CLIENT_ID/SECRET and TOSS_LIVE_PRICES=1"
  Write-Check "Toss candles API" $false "waiting for TOSS_CLIENT_ID/SECRET and TOSS_LIVE_CANDLES=1"
  Write-Check "Toss orderbook API" $false "waiting for TOSS_CLIENT_ID/SECRET and TOSS_LIVE_ORDERBOOK=1"
  Write-Check "Toss trades API" $false "waiting for TOSS_CLIENT_ID/SECRET and TOSS_LIVE_TRADES=1"
}

$dartDashboardStatus = $dashboard.integrations.dart.disclosures
if ($dartDashboardStatus) {
  $detail = "source=$($dartDashboardStatus.source), disclosures=$($dartDashboardStatus.disclosureCount)"
  if ($dartDashboardStatus.error) {
    $detail = "$detail, error=$($dartDashboardStatus.error)"
  }
  Write-Check "OpenDART dashboard source" ($dartDashboardStatus.source -eq "opendart") $detail
}

if ($dartReady) {
  $corp = Invoke-RestMethod -Uri (Join-Url $BaseUrl "/api/integrations/dart/corp-code?symbol=005930") -Headers $headers -Method Get -TimeoutSec 45
  Write-Check "OpenDART corp code" ($null -ne $corp.corp) "symbol=005930"
  $disclosures = Invoke-RestMethod -Uri (Join-Url $BaseUrl "/api/integrations/dart/disclosures?symbol=005930&days=7") -Headers $headers -Method Get -TimeoutSec 45
  Write-Check "OpenDART disclosures API" ($disclosures.source -eq "opendart") "items=$(($disclosures.items | Measure-Object).Count)"
} else {
  Write-Check "OpenDART disclosures API" $false "waiting for DART_API_KEY and DART_LIVE_DISCLOSURES=1"
}

$openaiAnalysisStatus = $dashboard.integrations.openai.analysis
if ($openaiAnalysisStatus) {
  $detail = "source=$($openaiAnalysisStatus.source), openai=$($openaiAnalysisStatus.openaiCount), fallback=$($openaiAnalysisStatus.fallbackCount)"
  if ($openaiAnalysisStatus.lastError) {
    $detail = "$detail, error=$($openaiAnalysisStatus.lastError)"
  }
  Write-Check "OpenAI dashboard source" ($openaiAnalysisStatus.source -eq "openai") $detail
}

if ($openaiReady) {
  $analysis = Invoke-RestMethod -Uri (Join-Url $BaseUrl "/api/integrations/openai/analyze?symbol=005930") -Headers $headers -Method Get -TimeoutSec 60
  $detail = "source=$($analysis.source), sentiment=$($analysis.sentiment), impact=$($analysis.impactScore)"
  if ($analysis.error) {
    $detail = "$detail, error=$($analysis.error)"
  }
  Write-Check "OpenAI analyze API" ($analysis.source -eq "openai") $detail
} else {
  Write-Check "OpenAI analyze API" $false "waiting for OPENAI_API_KEY and OPENAI_ANALYSIS_ENABLED=1"
}

Write-Host ""
Write-Host "Render deployment test finished." -ForegroundColor Green
