@echo off
setlocal

powershell -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
set EXITCODE=%ERRORLEVEL%

if not "%EXITCODE%"=="0" (
  echo.
  echo TradeBrain start failed. Exit code: %EXITCODE%
  echo Press any key to close this window...
  pause >nul
)

exit /b %EXITCODE%
