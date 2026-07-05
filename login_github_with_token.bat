@echo off
chcp 65001 >nul
setlocal

title Login GitHub CLI with Token
echo Login GitHub CLI with a Personal Access Token.
echo The token is read in this local window and is not printed to chat.
echo.
echo Create a classic token with the repo scope here:
echo https://github.com/settings/tokens/new?scopes=repo,read:org,gist&description=camscanner-watermark-web
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0scripts\login_github_with_token.ps1"
echo.
echo Token login helper finished.
pause
