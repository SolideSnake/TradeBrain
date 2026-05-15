@echo off
setlocal
powershell -ExecutionPolicy Bypass -File "%~dp0powershell\install.ps1" %*
set EXITCODE=%ERRORLEVEL%

echo.
if "%EXITCODE%"=="0" (
  echo TradeBrain install/check finished.
) else (
  echo TradeBrain install/check failed. Exit code: %EXITCODE%
)
echo Press any key to close this window...
pause >nul

exit /b %EXITCODE%
