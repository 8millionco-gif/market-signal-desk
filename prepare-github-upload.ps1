param(
  [string]$RemoteUrl = "",
  [string]$CommitMessage = "Initial Market Signal Desk MVP",
  [switch]$Commit,
  [switch]$Push
)

$ErrorActionPreference = "Stop"

function Write-Step($Message) {
  Write-Host ""
  Write-Host "== $Message ==" -ForegroundColor Cyan
}

function Require-Command($Name) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "$Name command is required."
  }
}

Require-Command git

Write-Step "Repository"
if (-not (Test-Path ".git")) {
  git init
} else {
  Write-Host "Git repository already exists."
}

Write-Step "Ignored runtime files"
$ignoredTargets = @(
  "outputs/market-signal-desk/data/runs",
  "outputs/market-signal-desk/data/watchlist.json",
  "outputs/market-signal-desk/data/dart-corp-codes.json",
  "outputs/market-signal-desk/__pycache__",
  "work/scheduler-test-runs"
)

foreach ($target in $ignoredTargets) {
  if (Test-Path $target) {
    git check-ignore -q $target
    if ($LASTEXITCODE -eq 0) {
      Write-Host "ignored: $target" -ForegroundColor Green
    } else {
      throw "Not ignored: $target"
    }
  }
}

Write-Step "Secret pattern scan"
$candidateFiles = git ls-files --others --exclude-standard
$secretPattern = "tsck_|tssk_|sk-[A-Za-z0-9]{10,}|ADMIN_TOKEN=.*[A-Za-z0-9]{12,}|TOSS_CLIENT_SECRET=.*[A-Za-z0-9]{12,}|NAVER_CLIENT_SECRET=.*[A-Za-z0-9]{12,}|OPENAI_API_KEY=.*[A-Za-z0-9]{12,}|DART_API_KEY=.*[A-Za-z0-9]{12,}"

if ($candidateFiles) {
  $candidateFiles = $candidateFiles | Where-Object { $_ -ne "prepare-github-upload.ps1" }
}

if ($candidateFiles) {
  $matches = Select-String -Path $candidateFiles -Pattern $secretPattern -CaseSensitive -ErrorAction SilentlyContinue
  if ($matches) {
    $matches | ForEach-Object {
      Write-Host "$($_.Path):$($_.LineNumber) potential secret pattern" -ForegroundColor Red
    }
    throw "Potential secret detected. Review before uploading."
  }
}
Write-Host "No obvious secret pattern found in upload candidates." -ForegroundColor Green

Write-Step "Current git status"
git status --short

if ($Commit) {
  Write-Step "Commit"
  git add .
  git status --short
  git commit -m $CommitMessage
}

if ($RemoteUrl) {
  Write-Step "Remote"
  $existingRemote = git remote get-url origin 2>$null
  if ($LASTEXITCODE -eq 0 -and $existingRemote) {
    git remote set-url origin $RemoteUrl
  } else {
    git remote add origin $RemoteUrl
  }
  git branch -M main
  git remote -v
}

if ($Push) {
  $hasCommit = $false
  git rev-parse --verify HEAD *> $null
  if ($LASTEXITCODE -eq 0) {
    $hasCommit = $true
  }
  if (-not $hasCommit -and -not $Commit) {
    throw "No commit exists yet. Run with -Commit -Push for the first upload."
  }
  if (-not $RemoteUrl) {
    $existingRemote = git remote get-url origin 2>$null
    if ($LASTEXITCODE -ne 0 -or -not $existingRemote) {
      throw "RemoteUrl is required for push when origin is not configured."
    }
  }
  Write-Step "Push"
  git push -u origin main
}

Write-Step "Done"
Write-Host "GitHub upload preparation finished." -ForegroundColor Green
