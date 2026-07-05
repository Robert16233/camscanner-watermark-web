@echo off
chcp 65001 >nul
setlocal

title Publish CamScanner Watermark Web to GitHub
echo Starting GitHub publish helper...
echo Keep this window open. If a GitHub one-time code appears, copy it into:
echo https://github.com/login/device
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0scripts\publish_to_github.ps1"
echo.
echo Publish helper finished.
pause
