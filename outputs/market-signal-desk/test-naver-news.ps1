param(
  [string]$Query = "삼성전자",
  [int]$Display = 5,
  [string]$BaseUrl = "https://openapi.naver.com/v1/search/news"
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

function Normalize-NewsUrl($Url) {
  $trimmed = $Url.TrimEnd("/")
  if ($trimmed.EndsWith("/v1/search/news")) {
    return "$trimmed.json"
  }
  return $trimmed
}

$clientId = Read-SecretText "Naver Client ID"
$clientSecret = Read-SecretText "Naver Client Secret"

if ([string]::IsNullOrWhiteSpace($clientId)) {
  throw "Naver Client ID is required."
}

if ([string]::IsNullOrWhiteSpace($clientSecret)) {
  throw "Naver Client Secret is required."
}

$requestUrl = Normalize-NewsUrl $BaseUrl
$builder = [System.UriBuilder]::new($requestUrl)
$queryString = [System.Web.HttpUtility]::ParseQueryString("")
$queryString["query"] = $Query
$queryString["display"] = [string]$Display
$queryString["start"] = "1"
$queryString["sort"] = "date"
$builder.Query = $queryString.ToString()
$uri = $builder.Uri.AbsoluteUri

$headers = @{
  "X-Naver-Client-Id" = $clientId.Trim()
  "X-Naver-Client-Secret" = $clientSecret.Trim()
}

$response = Invoke-RestMethod -Uri $uri -Headers $headers -Method Get

Write-Host "Naver news API test succeeded."
Write-Host "Query: $Query"
Write-Host "Total: $($response.total)"
Write-Host "Display: $($response.display)"
Write-Host ""

$index = 1
foreach ($item in $response.items) {
  $title = [System.Net.WebUtility]::HtmlDecode(($item.title -replace "<[^>]+>", ""))
  $publisher = ""
  try {
    $publisher = ([Uri]$item.originallink).Host
  }
  catch {
    $publisher = "news"
  }
  Write-Host "$index. $title"
  Write-Host "   $publisher"
  $index += 1
}
