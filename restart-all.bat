@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Restarting All Servers and Tunnels
echo ========================================
echo.

REM Try to find PowerShell
set PS_CMD=
if exist "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" (
    set PS_CMD=C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe
    goto :found_ps
)

where pwsh >nul 2>&1
if not errorlevel 1 (
    set PS_CMD=pwsh
    goto :found_ps
)

where powershell >nul 2>&1
if not errorlevel 1 (
    set PS_CMD=powershell
    goto :found_ps
)

echo ERROR: PowerShell not found!
echo Please install PowerShell or use the .ps1 file directly.
pause
exit /b 1

:found_ps
echo Using PowerShell: %PS_CMD%
echo.
echo This will start everything and auto-configure the frontend.
echo.
pause

%PS_CMD% -ExecutionPolicy Bypass -File "%~dp0restart-all.ps1"

pause

