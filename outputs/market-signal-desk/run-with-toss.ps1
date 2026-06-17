param(
  [string]$PythonPath = "C:\Users\doyeo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe",
  [int]$Port = 8787
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

$clientId = Read-Host -Prompt "Toss API Key"
$clientSecret = Read-SecretText "Toss Secret Key"
$accountSeq = Read-Host -Prompt "Toss Account Seq (optional, press Enter to skip)"
$dartApiKey = Read-SecretText "OpenDART API Key (optional, press Enter to skip)"
$naverClientId = Read-Host -Prompt "Naver Client ID (optional, press Enter to skip)"
$naverClientSecret = Read-SecretText "Naver Client Secret (optional, press Enter to skip)"
$openAiApiKey = Read-SecretText "OpenAI API Key (optional, press Enter to skip)"

if ([string]::IsNullOrWhiteSpace($clientId)) {
  throw "Toss API Key is required."
}

if ([string]::IsNullOrWhiteSpace($clientSecret)) {
  throw "Toss Secret Key is required."
}

$previousClientId = $env:TOSS_CLIENT_ID
$previousClientSecret = $env:TOSS_CLIENT_SECRET
$previousAccountSeq = $env:TOSS_ACCOUNT_SEQ
$previousPort = $env:PORT
$previousDartApiKey = $env:DART_API_KEY
$previousNaverClientId = $env:NAVER_CLIENT_ID
$previousNaverClientSecret = $env:NAVER_CLIENT_SECRET
$previousOpenAiApiKey = $env:OPENAI_API_KEY

try {
  $env:TOSS_CLIENT_ID = $clientId.Trim()
  $env:TOSS_CLIENT_SECRET = $clientSecret.Trim()
  $env:PORT = [string]$Port
  if (-not [string]::IsNullOrWhiteSpace($accountSeq)) {
    $env:TOSS_ACCOUNT_SEQ = $accountSeq.Trim()
  }
  if (-not [string]::IsNullOrWhiteSpace($dartApiKey)) {
    $env:DART_API_KEY = $dartApiKey.Trim()
  }
  if (-not [string]::IsNullOrWhiteSpace($naverClientId)) {
    $env:NAVER_CLIENT_ID = $naverClientId.Trim()
  }
  if (-not [string]::IsNullOrWhiteSpace($naverClientSecret)) {
    $env:NAVER_CLIENT_SECRET = $naverClientSecret.Trim()
  }
  if (-not [string]::IsNullOrWhiteSpace($openAiApiKey)) {
    $env:OPENAI_API_KEY = $openAiApiKey.Trim()
  }

  Write-Host "Market Signal Desk is starting with API credentials in this session only."
  Write-Host "Open http://127.0.0.1:$Port"
  & $PythonPath server.py
}
finally {
  $env:TOSS_CLIENT_ID = $previousClientId
  $env:TOSS_CLIENT_SECRET = $previousClientSecret
  $env:TOSS_ACCOUNT_SEQ = $previousAccountSeq
  $env:PORT = $previousPort
  $env:DART_API_KEY = $previousDartApiKey
  $env:NAVER_CLIENT_ID = $previousNaverClientId
  $env:NAVER_CLIENT_SECRET = $previousNaverClientSecret
  $env:OPENAI_API_KEY = $previousOpenAiApiKey
}
