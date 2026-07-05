$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot
$GhConfigDir = Join-Path $ProjectRoot ".gh-config"
New-Item -ItemType Directory -Force -Path $GhConfigDir | Out-Null
$env:GH_CONFIG_DIR = $GhConfigDir

function Require-Command($Name) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $cmd) {
        throw "Missing command: $Name"
    }
}

Require-Command git
Require-Command gh

function Assert-GitHubReachable {
    Write-Host "Checking DNS for github.com..."
    $resolved = Resolve-DnsName github.com -ErrorAction SilentlyContinue |
        Where-Object { $_.Type -eq "A" -and $_.IPAddress } |
        Select-Object -First 1
    if ($resolved -and $resolved.IPAddress -eq "127.0.0.1") {
        throw @"
github.com is resolving to 127.0.0.1 on this machine.

That usually means C:\Windows\System32\drivers\etc\hosts contains GitHub blocking entries.
Please remove or comment the GitHub-related lines in that hosts file, then run this script again.
"@
    }
}

function Enable-LocalProxyIfNeeded {
    Write-Host "Checking GitHub network connectivity..."
    $canDirect = $false
    try {
        $tcp = Test-NetConnection github.com -Port 443 -InformationLevel Quiet -WarningAction SilentlyContinue
        if ($tcp) {
            $canDirect = $true
        }
    } catch {
        $canDirect = $false
    }

    if ($canDirect) {
        return
    }

    $ports = @(7897, 7898, 7899, 7890, 1080, 10808)
    $netstat = @(netstat -ano)
    foreach ($port in $ports) {
        $listening = $netstat | Where-Object {
            $_ -match "LISTENING" -and $_ -match "(:|\])$port\s+"
        } | Select-Object -First 1
        if ($listening) {
            $proxy = "http://127.0.0.1:$port"
            $env:HTTP_PROXY = $proxy
            $env:HTTPS_PROXY = $proxy
            $env:http_proxy = $proxy
            $env:https_proxy = $proxy
            Write-Host "GitHub direct connection is unavailable. Using local proxy: $proxy"
            return
        }
    }

    Write-Host "GitHub direct connection is unavailable and no common local proxy port was found."
    Write-Host "If you use Clash Verge, turn on System Proxy or TUN, then run this script again."
}

if (-not (Test-Path ".git")) {
    git init | Out-Host
}

Write-Host ""
Write-Host "== CamScanner Watermark Web: GitHub publisher =="
Write-Host "This window may show a one-time GitHub code."
Write-Host "If it does, open https://github.com/login/device and enter that code."
Write-Host ""

Assert-GitHubReachable
Enable-LocalProxyIfNeeded

Write-Host "Checking GitHub CLI authentication..."
$authOk = $true
try {
    gh auth status 2>$null | Out-Null
} catch {
    $authOk = $false
}

if (-not $authOk) {
    Write-Host "GitHub CLI is not logged in. Starting gh auth login..."
    Write-Host "When a one-time code appears, copy it into https://github.com/login/device."
    gh auth login --hostname github.com --git-protocol https --web --insecure-storage
    try {
        gh auth status 2>$null | Out-Null
    } catch {
        throw "GitHub CLI authentication did not complete. Run 'gh auth login' successfully, then re-run this script."
    }
}

$login = (gh api user --jq ".login" 2>$null).Trim()
$userId = (gh api user --jq ".id" 2>$null).Trim()
if (-not $login -or -not $userId) {
    throw "Could not read GitHub user information from gh."
}

$repoName = Read-Host "Repository name [camscanner-watermark-web]"
if ([string]::IsNullOrWhiteSpace($repoName)) {
    $repoName = "camscanner-watermark-web"
}

$visibility = Read-Host "Visibility: public or private [public]"
if ([string]::IsNullOrWhiteSpace($visibility)) {
    $visibility = "public"
}
if ($visibility -ne "public" -and $visibility -ne "private") {
    throw "Visibility must be public or private."
}

$gitName = (git config user.name)
if ([string]::IsNullOrWhiteSpace($gitName)) {
    git config user.name $login
}

$gitEmail = (git config user.email)
if ([string]::IsNullOrWhiteSpace($gitEmail)) {
    git config user.email "$userId+$login@users.noreply.github.com"
}

$readme = Join-Path $ProjectRoot "README.md"
$content = Get-Content -LiteralPath $readme -Raw -Encoding UTF8
$content = $content -replace "YOUR_GITHUB_USERNAME", $login
Set-Content -LiteralPath $readme -Value $content -Encoding UTF8

git add .

$hasCommit = $true
git rev-parse --verify HEAD 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    $hasCommit = $false
}

$needCommit = $true
git diff --cached --quiet
if ($LASTEXITCODE -eq 0) {
    $needCommit = $false
}

if ($needCommit) {
    if ($hasCommit) {
        git commit -m "Prepare GitHub release"
    } else {
        git commit -m "Initial release"
    }
} else {
    Write-Host "No staged changes to commit."
}

git branch -M main

$repoFullName = "$login/$repoName"
$repoExists = $true
try {
    gh repo view $repoFullName 2>$null | Out-Null
} catch {
    $repoExists = $false
}

if ($repoExists) {
    Write-Host "Repository already exists: $repoFullName"
    $remoteUrl = "https://github.com/$repoFullName.git"
    $remoteExists = $true
    git remote get-url origin 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        $remoteExists = $false
    }
    if ($remoteExists) {
        git remote set-url origin $remoteUrl
    } else {
        git remote add origin $remoteUrl
    }
    git push -u origin main
} else {
    if ($visibility -eq "public") {
        gh repo create $repoFullName --public --source=. --remote=origin --push
    } else {
        gh repo create $repoFullName --private --source=. --remote=origin --push
    }
}

Write-Host ""
Write-Host "Published: https://github.com/$repoFullName"
Write-Host "Next: deploy with Render, Railway, Fly.io, or your VPS."
