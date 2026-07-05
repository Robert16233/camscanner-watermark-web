@echo off
chcp 65001 >nul
setlocal

title Login GitHub CLI
echo Logging in to GitHub CLI...
echo If a one-time code appears, open this URL and enter it:
echo https://github.com/login/device
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0scripts\login_github_cli.ps1"
echo.
echo Login helper finished.
echo Log file:
echo %~dp0login_github_cli.log
pause
