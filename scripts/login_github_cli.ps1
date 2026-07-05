$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$LogPath = Join-Path $ProjectRoot "login_github_cli.log"
Start-Transcript -Path $LogPath -Force | Out-Null

try {
$GhConfigDir = Join-Path $ProjectRoot ".gh-config"
New-Item -ItemType Directory -Force -Path $GhConfigDir | Out-Null
$env:GH_CONFIG_DIR = $GhConfigDir
Write-Host "Using GitHub CLI config dir: $GhConfigDir"

function Enable-LocalProxyIfNeeded {
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
            Write-Host "Using local proxy: $proxy"
            return
        }
    }
}

Enable-LocalProxyIfNeeded

try {
    gh auth status 2>$null | Out-Null
    Write-Host "GitHub CLI is already logged in."
    gh auth status
} catch {
    Write-Host "Starting GitHub CLI login..."
    Write-Host "Copy the one-time code into https://github.com/login/device when prompted."
    gh auth login --hostname github.com --git-protocol https --web --insecure-storage
    gh auth status
}
} finally {
    Stop-Transcript | Out-Null
}
