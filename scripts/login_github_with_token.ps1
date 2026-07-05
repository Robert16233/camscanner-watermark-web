$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$GhConfigDir = Join-Path $ProjectRoot ".gh-config"
New-Item -ItemType Directory -Force -Path $GhConfigDir | Out-Null
$env:GH_CONFIG_DIR = $GhConfigDir

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

Write-Host "Using GitHub CLI config dir: $GhConfigDir"
Write-Host "Paste a GitHub classic token with repo, read:org, and gist scopes."
$secure = Read-Host "GitHub token" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $token = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
    if ([string]::IsNullOrWhiteSpace($token)) {
        throw "No token entered."
    }
    $token | gh auth login --hostname github.com --git-protocol https --with-token --insecure-storage
    gh auth status
} finally {
    if ($bstr -ne [IntPtr]::Zero) {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
    if ($token) {
        Remove-Variable token -ErrorAction SilentlyContinue
    }
}
